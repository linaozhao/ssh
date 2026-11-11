"""Fail-closed physical-device inspection with explicit shared-GPU authorization."""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from typing import Any

from .common import read_json, sha256_file, sha256_json, write_json

GPU_INDEX = 4
GPU_UUID = "GPU-36dfefdc-f06d-c469-3aa2-c4cb1404b8ee"
SHARED_GPU_UUID = "GPU-221ea0c6-cdd5-2d17-9594-45d336491563"
GPU_FIELDS = "index,uuid,name,pci.bus_id,memory.total,memory.used"
PROCESS_FIELDS = "pid,gpu_uuid,process_name,used_gpu_memory"


class RuntimeBlocked(RuntimeError):
    """A runtime gate failed; no alternate device may be selected."""


def _csv_rows(text: str, fields: str) -> list[dict[str, str]]:
    names = fields.split(",")
    rows = []
    for values in csv.reader(io.StringIO(text)):
        if not values or not any(value.strip() for value in values):
            continue
        values = [value.strip() for value in values]
        if values[0] == names[0]:
            continue
        if len(values) != len(names):
            raise ValueError("unexpected nvidia-smi CSV column count")
        rows.append(dict(zip(names, values)))
    return rows


def _number(value: str) -> int:
    return int(value.removesuffix(" MiB").strip())


def process_identity(pid: int) -> dict[str, int]:
    """Pin a PID to its owner and start tick, protecting against PID reuse."""
    path = Path("/proc") / str(pid)
    stat = (path / "stat").read_text()
    return {"pid": pid, "uid": path.stat().st_uid,
            "start_ticks": int(stat[stat.rfind(")") + 2:].split()[19])}


def _owned(process: dict[str, Any], service: dict[str, Any] | None) -> bool:
    if not service or service.get("gpu_uuid") not in {GPU_UUID, SHARED_GPU_UUID} or service.get("owner_uid") != os.getuid():
        return False
    try:
        actual = process_identity(int(process["pid"]))
        return actual["uid"] == os.getuid() and actual in service.get("processes", [])
    except (OSError, ValueError):
        return False


def inspect_gpu_csv(config: dict[str, Any], gpu_csv: str, process_csv: str, *,
                    owned_service: dict[str, Any] | None = None) -> dict[str, Any]:
    """Audit captured CSV. This function does not establish a live launch permit."""
    result: dict[str, Any] = {"status": "blocked", "allowed": False, "physical_gpu_index": GPU_INDEX,
                              "expected_uuid": GPU_UUID, "gpu_csv": gpu_csv, "process_csv": process_csv,
                              "inspection_only": True, "gpu": None, "processes": []}
    gpu_config = config.get("gpu", {})
    index = gpu_config.get("physical_gpu_index", GPU_INDEX)
    shared = index == 2 and gpu_config.get("sharing_authorization") == "user_2026-11-10_gpu2" and gpu_config.get("allow_shared_gpu") is True
    expected_uuid = SHARED_GPU_UUID if shared else GPU_UUID
    result.update(physical_gpu_index=index, expected_uuid=expected_uuid, shared_gpu_authorized=shared)
    if (index != GPU_INDEX and not shared
            or gpu_config.get("expected_uuid", gpu_config.get("verified_uuid", GPU_UUID)) != expected_uuid
            or gpu_config.get("allow_gpu_fallback", False)
            or not gpu_config.get("require_uuid_verification", True)
            or "RTX4090" not in gpu_config.get("expected_gpu_name", "RTX4090").replace(" ", "").upper()):
        return result | {"reason": "gpu_policy_mismatch"}
    try:
        devices = _csv_rows(gpu_csv, GPU_FIELDS)
        processes = _csv_rows(process_csv, PROCESS_FIELDS)
        matches = [row for row in devices if int(row["index"]) == index]
        if len(matches) != 1:
            return result | {"reason": "physical_gpu_mapping_unverified"}
        gpu = matches[0]
        result["gpu"] = gpu
        if gpu["uuid"] != expected_uuid or "RTX4090" not in gpu["name"].replace(" ", "").upper():
            return result | {"reason": "gpu_identity_mismatch"}
        if sum(row["uuid"] == expected_uuid for row in devices) != 1:
            return result | {"reason": "ambiguous_uuid_mapping"}
        total, used = _number(gpu["memory.total"]), _number(gpu["memory.used"])
        relevant = [row for row in processes if row["gpu_uuid"] == expected_uuid]
        result["processes"] = relevant
        foreign = [row for row in relevant if not _owned(row, owned_service)]
        result["foreign_processes"] = foreign
        if foreign and not shared:
            return result | {"reason": "gpu_occupied", "blocking_processes": foreign}
        recorded_pids = {row["pid"] for row in (owned_service or {}).get("processes", [])}
        if any(int(row["pid"]) in recorded_pids and row["gpu_uuid"] != expected_uuid for row in processes):
            return result | {"reason": "owned_process_on_wrong_gpu"}
        utilization = float(config.get("model", {}).get("deployment", {}).get("gpu_memory_utilization", 0.9))
        if total <= 0 or used < 0 or used > total or not 0 < utilization <= 1:
            return result | {"reason": "invalid_memory_measurement"}
        owned = [row for row in relevant if _owned(row, owned_service)]
        reserve = int(gpu_config.get("min_free_reserve_mib", 0)) if shared else 0
        if shared and (reserve < 1024 or utilization > 0.8):
            return result | {"reason": "shared_memory_policy_exceeds_authorization"}
        if not owned and total - used < total * utilization + reserve:
            return result | {"reason": "insufficient_free_memory"}
        if owned and total - used < reserve:
            return result | {"reason": "shared_gpu_free_reserve_exhausted"}
        return result | {"status": "ready", "allowed": True, "reason": None}
    except (ValueError, KeyError, TypeError) as exc:
        return result | {"reason": "invalid_nvidia_smi_output", "error": str(exc)}


def check_gpu(config: dict[str, Any] | None = None, *,
              owned_service: dict[str, Any] | None = None) -> dict[str, Any]:
    """Query the host mapping. Subprocess/NVML failure is blocked, never absent GPU."""
    config = config or {}
    capture = {}
    try:
        for kind, fields in (("gpu", GPU_FIELDS), ("compute-apps", PROCESS_FIELDS)):
            completed = subprocess.run(["nvidia-smi", f"--query-{kind}={fields}",
                                        "--format=csv,noheader,nounits"], capture_output=True,
                                       text=True, check=True, timeout=15)
            capture[kind] = completed.stdout
    except (OSError, subprocess.SubprocessError) as exc:
        return {"status": "blocked", "allowed": False, "reason": "nvidia_smi_query_failed",
                "physical_gpu_index": config.get("gpu", {}).get("physical_gpu_index", GPU_INDEX),
                "expected_uuid": config.get("gpu", {}).get("expected_uuid", GPU_UUID),
                "inspection_only": False, "error": str(exc), "capture": capture,
                "stderr": getattr(exc, "stderr", None)}
    return inspect_gpu_csv(config, capture["gpu"], capture["compute-apps"],
                           owned_service=owned_service) | {"inspection_only": False}


def require_gpu(config: dict[str, Any], *, owned_service: dict[str, Any] | None = None) -> dict[str, Any]:
    result = check_gpu(config, owned_service=owned_service)
    if not result["allowed"]:
        raise RuntimeBlocked(result["reason"])
    return result


def verify_service(config: dict[str, Any]) -> dict[str, Any]:
    """Only a recorded, still-owned service on the verified UUID can receive calls."""
    path = config.get("runtime", {}).get("service_manifest_path", str(Path(__file__).resolve().parents[2] / "results" / config["run_id"] / "service_manifest.json"))
    try:
        service = read_json(Path(path)) if path else None
        if not service or service.get("run_id") != config["run_id"]:
            raise RuntimeBlocked("owned_service_manifest_required")
        if service.get("model_config_sha256") != sha256_json(config["model"]):
            raise RuntimeBlocked("service_model_fingerprint_mismatch")
        inspection = require_gpu(config, owned_service=service)
        if not any(_owned(p, service) for p in inspection.get("processes", [])):
            raise RuntimeBlocked("service_pid_gpu_mapping_unverified")
        if service.get("endpoint") != config["model"]["base_url"]:
            raise RuntimeBlocked("service_endpoint_mismatch")
        return service
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise RuntimeBlocked(f"service_manifest_unavailable: {exc}") from exc


def model_files(config: dict[str, Any], *, weights: bool = False) -> dict[str, str]:
    """Fingerprint local tokenizer/template files; full weights are hashed at launch."""
    model = config["model"]
    root = Path(model.get("weights_path", model.get("deployment", {}).get("weights_path", "")))
    if not root.is_dir() or not (root / "config.json").is_file():
        raise RuntimeBlocked("local_model_files_unavailable")
    suffixes = {".json", ".jinja", ".model", ".txt"} | ({".safetensors", ".bin"} if weights else set())
    return {str(p.relative_to(root)): sha256_file(p) for p in sorted(root.rglob("*"))
            if p.is_file() and p.suffix in suffixes and ".cache" not in p.parts}


def verified_cuda_environment(identity: dict[str, Any]) -> tuple[dict[str, str], dict[str, Any]]:
    """Verify the logical device UUID before using vLLM's integer-only selector."""
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES=str(identity["physical_gpu_index"]),
                       CUDA_DEVICE_ORDER="PCI_BUS_ID")
    probe = ("import json,torch; p=torch.cuda.get_device_properties(0); "
             "print(json.dumps({'visible_devices':torch.cuda.device_count(),"
             "'uuid':str(p.uuid),'name':p.name}))")
    try:
        completed = subprocess.run([sys.executable, "-c", probe], env=environment,
                                   capture_output=True, text=True, check=True, timeout=60)
        mapping = json.loads(completed.stdout.strip())
        actual_uuid = "GPU-" + mapping["uuid"].removeprefix("GPU-")
        if mapping["visible_devices"] != 1 or actual_uuid != identity["expected_uuid"]:
            raise RuntimeBlocked("cuda_logical_device_uuid_mismatch")
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError) as exc:
        raise RuntimeBlocked("cuda_logical_device_probe_failed") from exc
    return environment, mapping


def launch_service(config: dict[str, Any], manifest_path: Path) -> int:
    """Foreground supervisor; called only by an explicit --launch invocation."""
    from urllib.parse import urlparse

    if manifest_path.exists():
        raise RuntimeBlocked("service_manifest_already_exists")
    identity = require_gpu(config)
    model, deployment = config["model"], config["model"]["deployment"]
    endpoint = urlparse(model["base_url"])
    if endpoint.hostname != "127.0.0.1" or endpoint.scheme != "http" or endpoint.path.rstrip("/") != "/v1":
        raise RuntimeBlocked("single_loopback_endpoint_required")
    if (deployment.get("tensor_parallel_size", 1) != 1 or deployment.get("quantization") is not None
            or deployment.get("dtype", "bfloat16") != "bfloat16"
            or not 1 <= deployment.get("max_num_seqs", 3) <= 3
            or not deployment.get("enable_prefix_caching", True) or not deployment.get("enforce_eager", True)):
        raise RuntimeBlocked("unsupported_deployment_policy")
    files = model_files(config, weights=True)
    if not any(name.endswith((".safetensors", ".bin")) for name in files):
        raise RuntimeBlocked("local_model_weights_unavailable")
    command = [sys.executable, "-m", "vllm.entrypoints.openai.api_server", "--model",
               model.get("weights_path", deployment.get("weights_path")), "--served-model-name", model["model_name"],
               "--host", "127.0.0.1", "--port", str(endpoint.port or 8114), "--dtype", "bfloat16",
               "--tensor-parallel-size", "1", "--max-model-len", str(deployment.get("max_model_len", 16384)),
               "--gpu-memory-utilization", str(deployment.get("gpu_memory_utilization", 0.9)),
               "--max-num-seqs", str(deployment.get("max_num_seqs", 3)), "--enable-prefix-caching", "--enforce-eager"]
    environment, cuda_mapping = verified_cuda_environment(identity)
    require_gpu(config)
    process = subprocess.Popen(command, env=environment, start_new_session=True)
    service = {"run_id": config["run_id"], "owner_uid": os.getuid(), "pid": process.pid,
               "gpu_uuid": identity["expected_uuid"], "physical_gpu_index": identity["physical_gpu_index"], "endpoint": model["base_url"],
               "processes": [process_identity(process.pid)], "status": "starting", "command": command,
               "cuda_mapping_verification": cuda_mapping,
               "cuda_visible_devices": environment["CUDA_VISIBLE_DEVICES"],
               "model_config_sha256": sha256_json(model), "model_files": files,
               "model_files_sha256": sha256_json(files), "runtime_source_sha256": sha256_file(Path(__file__))}
    write_json(manifest_path, service)
    try:
        deadline = time.monotonic() + 300
        gpu_initialized = False
        missing_since = None
        while process.poll() is None:
            # Only processes in the newly created service session can be recorded as ours.
            for entry in Path("/proc").iterdir():
                if entry.name.isdigit():
                    try:
                        identity = process_identity(int(entry.name))
                        if identity["uid"] == os.getuid() and os.getpgid(identity["pid"]) == process.pid:
                            if identity not in service["processes"]:
                                service["processes"].append(identity)
                    except (OSError, ValueError):
                        pass
            inspection = check_gpu(config, owned_service=service)
            service["inspection"] = inspection
            if not inspection["allowed"]:
                raise RuntimeBlocked(inspection["reason"])
            if any(_owned(p, service) for p in inspection.get("processes", [])):
                service["status"] = "gpu_verified"
                gpu_initialized = True
                missing_since = None
            elif not gpu_initialized and time.monotonic() > deadline:
                raise RuntimeBlocked("service_pid_gpu_mapping_timeout")
            elif gpu_initialized:
                # The engine can release CUDA before the API parent finishes
                # its graceful exit; the startup deadline no longer applies.
                service["status"] = "gpu_process_exiting"
                now = time.monotonic()
                if missing_since is None:
                    missing_since = now
                elif now - missing_since > 15:
                    raise RuntimeBlocked("service_compute_process_missing")
            write_json(manifest_path, service)
            time.sleep(2)
        service["status"] = "exited"
        service["exit_code"] = process.returncode
        write_json(manifest_path, service)
        return process.returncode
    except BaseException:
        service["status"] = "blocked"
        write_json(manifest_path, service)
        if process.poll() is None and _owned({"pid": process.pid}, service):
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--gpu-csv", type=Path)
    parser.add_argument("--process-csv", type=Path)
    parser.add_argument("--launch", action="store_true")
    args = parser.parse_args()
    config = read_json(args.config)
    if args.launch:
        if args.gpu_csv or args.process_csv:
            parser.error("captured CSV cannot authorize a launch")
        try:
            return launch_service(config, args.manifest)
        except RuntimeBlocked as exc:
            print(json.dumps({"status": "blocked", "reason": str(exc)}))
            return 2
    if bool(args.gpu_csv) != bool(args.process_csv):
        parser.error("both captured CSV files are required")
    result = (inspect_gpu_csv(config, args.gpu_csv.read_text(), args.process_csv.read_text())
              if args.gpu_csv else check_gpu(config))
    result.update(run_id=config["run_id"], runtime_source_sha256=sha256_file(Path(__file__)))
    write_json(args.manifest, result)
    print(json.dumps({key: result[key] for key in ("status", "reason", "inspection_only")}))
    return 0 if result["allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
