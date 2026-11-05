"""Flash experiment isolation, resume, transport, and comparison regressions."""

from __future__ import annotations

import copy
import json
import shutil
import sys
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cbm_drift_v2.common import read_json, read_jsonl, sha256_json, write_jsonl
from cbm_drift_v2.tokenplan_analysis import _performance, analyze_tokenplan_judge, build_chinese_report
from cbm_drift_v2.tokenplan_judge import (
    RESULTS_RELATIVE,
    TokenPlanJudgeRunner,
    atomic_write_json,
    load_atomic_records,
    materialize_atomic_records,
    prepare_tokenplan_experiment,
    results_directory,
    validate_preflight,
)


@pytest.fixture(scope="module")
def flash_template(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict]:
    root = tmp_path_factory.mktemp("flash_template")
    for name in (
        "results/judge/judge_input_packages.jsonl",
        "results/mad/raw_outputs.jsonl",
        "results/program/message_diagnostics.jsonl",
        "results/program/summary.json",
        "manifests/resume_audit.json",
    ):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(ROOT / name)
    config = read_json(ROOT / "config/tokenplan_deepseek_v4_flash.json")
    prepare_tokenplan_experiment(root, config)
    materialize_atomic_records(results_directory(root, config))
    return root, config


@pytest.fixture
def flash_root(tmp_path: Path, flash_template: tuple[Path, dict]) -> tuple[Path, dict]:
    root, config = flash_template
    shutil.copytree(root, tmp_path, dirs_exist_ok=True, symlinks=True)
    return tmp_path, copy.deepcopy(config)


def _prediction() -> dict:
    return {
        "has_diagnostic_event": False, "temporal_status": "correct_maintenance",
        "content_labels": [], "claims": [], "answer_effect": "correct_to_correct",
        "related_peer_message_ids": [], "uncertainty_reason": None,
    }


def _runner(root: Path, config: dict, monkeypatch: pytest.MonkeyPatch) -> TokenPlanJudgeRunner:
    monkeypatch.setenv("TOKENPLAN_API_KEY", "test-only-placeholder")
    runner = TokenPlanJudgeRunner(root, config)
    runner.client.close()
    def respond(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["model"] == "deepseek/deepseek-v4-flash"
        assert payload["thinking"] == {"type": "enabled"}
        assert payload["reasoning_effort"] == "low"
        content = json.dumps(_prediction())
        chunks = [
            {"model": payload["model"], "choices": [{"delta": {"content": content}, "finish_reason": "stop"}]},
            {"choices": [], "usage": {"prompt_tokens": 100, "completion_tokens": 25, "total_tokens": 125}},
        ]
        stream = "\n\n".join("data: " + json.dumps(chunk) for chunk in chunks) + "\n\ndata: [DONE]\n\n"
        return httpx.Response(200, text=stream, headers={"Content-Type": "text/event-stream"})
    runner.client = httpx.Client(transport=httpx.MockTransport(respond))
    return runner


def test_flash_config_changes_model_without_changing_judging_protocol() -> None:
    pro = read_json(ROOT / "config/tokenplan_deepseek_v4_pro.json")
    flash = read_json(ROOT / "config/tokenplan_deepseek_v4_flash.json")
    for field in ("base_url", "thinking", "reasoning_effort", "max_tokens", "response_format", "protocols", "paired_selection_seed", "preflight_selection_seed"):
        assert flash[field] == pro[field]
    assert flash["experiment_id"] != pro["experiment_id"]
    assert flash["model_name"] == "deepseek/deepseek-v4-flash"
    assert flash["require_preflight_pass"] is True
    assert results_directory(ROOT, pro) == ROOT / RESULTS_RELATIVE
    assert results_directory(ROOT, flash) != results_directory(ROOT, pro)
    raw = json.dumps(flash)
    assert "sk-" not in raw and "user_" not in raw


@pytest.mark.parametrize("value", ["/tmp/outside", "results/../../outside", "results"])
def test_results_directory_rejects_unsafe_or_shared_root(value: str) -> None:
    with pytest.raises(ValueError, match="subdirectory"):
        results_directory(ROOT, {"results_dir": value})


def test_flash_queue_matches_pro_samples_and_has_distinct_fingerprint(flash_root: tuple[Path, dict]) -> None:
    root, config = flash_root
    results = results_directory(root, config)
    manifest = read_json(results / "experiment_manifest.json")
    pro = read_json(ROOT / RESULTS_RELATIVE / "experiment_manifest.json")
    assert manifest["experiment_fingerprint"] != pro["experiment_fingerprint"]
    assert manifest["data"] == pro["data"]
    assert manifest["prompts"] == pro["prompts"]
    for name in ("preflight_manifest.jsonl", "paired_sample_manifest.jsonl"):
        assert read_jsonl(results / name) == read_jsonl(ROOT / RESULTS_RELATIVE / name)
    queue = read_jsonl(results / "request_queue.jsonl")
    assert len(queue) == len({row["judge_request_id"] for row in queue}) == 1800
    assert sum(row["is_preflight"] for row in queue) == 24
    assert sum(row["judge_protocol"] == "direct" for row in queue) == 180


def test_frozen_flash_config_cannot_be_silently_changed(flash_root: tuple[Path, dict]) -> None:
    root, config = flash_root
    config["max_tokens"] = 4096
    with pytest.raises(RuntimeError, match="Frozen artifact differs"):
        prepare_tokenplan_experiment(root, config)


def test_foreign_records_are_rejected(flash_root: tuple[Path, dict]) -> None:
    root, config = flash_root
    results = results_directory(root, config)
    queue = read_jsonl(results / "request_queue.jsonl")
    manifest = read_json(results / "experiment_manifest.json")
    atomic_write_json(results / "records/foreign.json", {
        "judge_request_id": queue[0]["judge_request_id"], "experiment_fingerprint": "pro-fingerprint",
    })
    with pytest.raises(RuntimeError, match="fingerprint mismatch"):
        load_atomic_records(results, queue, manifest["experiment_fingerprint"])


def test_mock_flash_request_is_recorded_and_resume_skips_it(
    flash_root: tuple[Path, dict], monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, config = flash_root
    runner = _runner(root, config, monkeypatch)
    try:
        summary = runner.run("preflight", max_new=1)
        assert summary["completed_records"] == summary["schema_valid"] == 1
        row = read_jsonl(runner.results / "judge_outputs.jsonl")[0]
        assert row["requested_model"] == row["response_model"] == config["model_name"]
        assert row["usage"]["total_tokens"] == 125
        assert row["finish_reason"] == "stop"
        assert row["experiment_fingerprint"] == runner.fingerprint
        assert "test-only-placeholder" not in json.dumps(row)
        assert runner.run("preflight", max_new=1)["completed_records"] == 2
        records = read_jsonl(runner.results / "judge_outputs.jsonl")
        assert len({value["judge_request_id"] for value in records}) == 2
        assert next(value for value in records if value["judge_request_id"] == row["judge_request_id"]) == row
    finally:
        runner.client.close()


def test_formal_execution_waits_for_successful_preflight(
    flash_root: tuple[Path, dict], monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, config = flash_root
    runner = _runner(root, config, monkeypatch)
    try:
        with pytest.raises(RuntimeError, match="passing frozen preflight"):
            runner.run("formal", max_new=1)
        assert not validate_preflight(root, config)["passed"]
    finally:
        runner.client.close()


def test_passing_mock_preflight_unblocks_formal_queue(
    flash_root: tuple[Path, dict], monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, config = flash_root
    monkeypatch.setattr("cbm_drift_v2.tokenplan_judge.time.sleep", lambda _: None)
    runner = _runner(root, config, monkeypatch)
    try:
        assert runner.run("preflight")["completed_records"] == 24
        assert validate_preflight(root, config)["passed"]
        assert runner.run("formal", max_new=1)["completed_records"] == 25
    finally:
        runner.client.close()


def test_report_and_comparison_use_flash_identity_and_matched_denominators(flash_root: tuple[Path, dict]) -> None:
    root, config = flash_root
    results = results_directory(root, config)
    manifest = read_json(results / "experiment_manifest.json")
    queue = read_jsonl(results / "request_queue.jsonl")
    first = queue[0]
    current = {
        **first, "experiment_fingerprint": manifest["experiment_fingerprint"],
        "requested_model": config["model_name"], "api_success": True, "parse_success": True,
        "schema_valid": True, "prediction": {**_prediction(), "has_diagnostic_event": True},
        "finish_reason": "stop", "latency_seconds": 2.0,
        "usage": {"prompt_tokens": 100, "completion_tokens": 10, "total_tokens": 110},
    }
    write_jsonl(results / "judge_outputs.jsonl", [current])
    baseline = results_directory(root, {"results_dir": config["comparison_results_dir"]})
    old_manifest = copy.deepcopy(manifest)
    old_manifest["config"]["model_name"] = "deepseek/deepseek-v4-pro"
    old_manifest["experiment_fingerprint"] = "baseline-test"
    atomic_write_json(baseline / "experiment_manifest.json", old_manifest)
    write_jsonl(baseline / "judge_outputs.jsonl", [{
        **current, "experiment_fingerprint": "baseline-test", "requested_model": "deepseek/deepseek-v4-pro",
        "latency_seconds": 10.0, "usage": {"prompt_tokens": 100, "completion_tokens": 30, "total_tokens": 130},
    }])
    summary = analyze_tokenplan_judge(root, config)
    comparison = summary["model_comparison"]
    assert comparison["both_schema_valid"] == comparison["matched_records"] == 1
    assert comparison["mean_completion_token_difference_current_minus_baseline"] == -20
    assert comparison["agreement"]["content_label_set_agrees"]["denominator"] == 1
    event = read_jsonl(results / "predicted_events.jsonl")[0]
    assert event["label_source"] == "deepseek_v4_flash_model_preannotation"
    result = build_chinese_report(root, config)
    report = (root / result["report"]).read_text(encoding="utf-8")
    assert config["model_name"] in report
    assert "周额度停止点" not in report
    assert "max_tokens 16384" in report


def test_analysis_rejects_foreign_fingerprint(flash_root: tuple[Path, dict]) -> None:
    root, config = flash_root
    results = results_directory(root, config)
    job = read_jsonl(results / "request_queue.jsonl")[0]
    write_jsonl(results / "judge_outputs.jsonl", [{**job, "experiment_fingerprint": "wrong"}])
    with pytest.raises(ValueError, match="fingerprint mismatch"):
        analyze_tokenplan_judge(root, config)


def test_unreported_reasoning_tokens_are_unknown_not_zero() -> None:
    performance = _performance([{"api_success": True, "usage": {"completion_tokens": 10}}])
    assert performance["mean_completion_tokens"] == 10
    assert performance["completion_tokens_records"] == 1
    assert performance["reasoning_tokens_records"] == 0
    assert performance["mean_reasoning_tokens"] is None
