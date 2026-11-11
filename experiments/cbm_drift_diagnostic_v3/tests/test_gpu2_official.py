"""Explicit device-policy override and official provider configuration regressions."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import os

import pytest

from cbm_drift_v3.common import read_json
from cbm_drift_v3.runtime import inspect_gpu_csv, SHARED_GPU_UUID, verified_cuda_environment, RuntimeBlocked, launch_service

ROOT = Path(__file__).resolve().parents[1]


def test_shared_gpu2_requires_explicit_authorization():
    config = read_json(ROOT / "config/experiment_gpu2_shared_r2_20261110.json")
    devices = f"2,{SHARED_GPU_UUID},NVIDIA GeForce RTX 4090,00000000:3D:00.0,24564,1484"
    processes = f"123,{SHARED_GPU_UUID},foreign_python,1462"
    result = inspect_gpu_csv(config, devices, processes)
    assert result["allowed"] and result["physical_gpu_index"] == 2
    assert len(result["foreign_processes"]) == 1
    missing = copy.deepcopy(config)
    del missing["gpu"]["sharing_authorization"]
    assert not inspect_gpu_csv(missing, devices, processes)["allowed"]
    wrong = devices.replace(SHARED_GPU_UUID, "GPU-other")
    assert not inspect_gpu_csv(config, wrong, processes)["allowed"]


def test_shared_gpu2_requires_memory_reserve():
    config = read_json(ROOT / "config/experiment_gpu2_shared_r2_20261110.json")
    devices = f"2,{SHARED_GPU_UUID},NVIDIA GeForce RTX 4090,00000000:3D:00.0,24564,6000"
    assert inspect_gpu_csv(config, devices, f"123,{SHARED_GPU_UUID},foreign,5990")["reason"] == "insufficient_free_memory"
    config["model"]["deployment"]["gpu_memory_utilization"] = 0.9
    assert inspect_gpu_csv(config, devices, "")["reason"] == "shared_memory_policy_exceeds_authorization"


def test_official_config_keeps_model_and_budget_separate():
    config = read_json(ROOT / "config/judge_official_flash_20261110.json")
    old = read_json(ROOT / "config/judge_controlled_r2.json")
    assert config["base_url"] == "https://api.deepseek.com"
    assert config["model_name"] == "deepseek-flash"
    assert old["model_name"] is None
    assert config["logical_request_cap"] == 144
    assert config["max_total_formal_attempts"] == 288
    assert not config["enable_real_trajectory_queue"]
    assert not config["online_enabled_by_default"]


def test_integer_cuda_selector_requires_matching_uuid(monkeypatch):
    def probe(command, **kwargs):
        assert kwargs["env"]["CUDA_VISIBLE_DEVICES"] == "2"
        return SimpleNamespace(stdout=json.dumps({"visible_devices": 1, "uuid": SHARED_GPU_UUID[4:]}))
    monkeypatch.setattr("cbm_drift_v3.runtime.subprocess.run", probe)
    env, mapping = verified_cuda_environment({"physical_gpu_index": 2, "expected_uuid": SHARED_GPU_UUID})
    assert env["CUDA_VISIBLE_DEVICES"] == "2"
    assert mapping["visible_devices"] == 1
    with pytest.raises(RuntimeBlocked, match="uuid_mismatch"):
        verified_cuda_environment({"physical_gpu_index": 2, "expected_uuid": "GPU-wrong"})


def test_graceful_shutdown_does_not_reuse_startup_timeout(monkeypatch, tmp_path):
    config = read_json(ROOT / "config/experiment_gpu2_shared_r2_20261110.json")
    identity = {"physical_gpu_index": 2, "expected_uuid": SHARED_GPU_UUID}
    parent = {"pid": 999999, "uid": os.getuid(), "start_ticks": 1}
    class Process:
        pid = parent["pid"]
        returncode = 0
        def __init__(self):
            self.polls = iter([None, None, 0])
        def poll(self):
            return next(self.polls)
    monkeypatch.setattr("cbm_drift_v3.runtime.require_gpu", lambda *a, **k: identity)
    monkeypatch.setattr("cbm_drift_v3.runtime.model_files", lambda *a, **k: {"model.safetensors": "test"})
    monkeypatch.setattr("cbm_drift_v3.runtime.verified_cuda_environment", lambda i: ({"CUDA_VISIBLE_DEVICES": "2"}, i))
    monkeypatch.setattr("cbm_drift_v3.runtime.subprocess.Popen", lambda *a, **k: Process())
    monkeypatch.setattr("cbm_drift_v3.runtime.process_identity", lambda pid: parent)
    monkeypatch.setattr("cbm_drift_v3.runtime.Path.iterdir", lambda p: iter([]))
    monkeypatch.setattr("cbm_drift_v3.runtime._owned", lambda *a: True)
    states = iter([{"allowed": True, "processes": [{"pid": parent["pid"]}]}, {"allowed": True, "processes": []}])
    monkeypatch.setattr("cbm_drift_v3.runtime.check_gpu", lambda *a, **k: next(states))
    clock = iter([0, 500])
    monkeypatch.setattr("cbm_drift_v3.runtime.time.monotonic", lambda: next(clock))
    monkeypatch.setattr("cbm_drift_v3.runtime.time.sleep", lambda seconds: None)
    manifest = tmp_path / "service.json"
    assert launch_service(config, manifest) == 0
    assert read_json(manifest)["status"] == "exited"
