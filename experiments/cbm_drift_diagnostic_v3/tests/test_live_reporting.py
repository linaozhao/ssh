"""Status reporting must distinguish preflight, partial files and final results."""
from cbm_drift_v3.common import write_json, write_jsonl
from cbm_drift_v3.reporting import build_report


def test_completed_preflight_does_not_claim_full_mad(config, judge_config, tmp_path):
    config["preserve_root_report"] = True
    result = tmp_path / "results" / config["run_id"]
    write_json(result / "mad/status.json", {"status": "completed", "planned": 198, "api_success": 198})
    (tmp_path / "RUN_SUMMARY_ZH.md").write_text("preserved old report", encoding="utf-8")
    status = build_report(tmp_path, config, judge_config)
    assert status["mad_generation"]["status"] == "partial"
    assert (tmp_path / "RUN_SUMMARY_ZH.md").read_text() == "preserved old report"


def test_live_judge_files_override_absent_status(config, judge_config, tmp_path):
    result = tmp_path / "results" / config["run_id"]
    directory = result / "controlled_judge"
    write_jsonl(directory / "outputs.jsonl", [{"status": "success", "api_success": True,
                  "schema_valid": True, "quote_valid": True, "object_valid": True, "finish_reason": "stop"}])
    write_jsonl(directory / "attempts.jsonl", [{"request_id": "software_only"}])
    status = build_report(tmp_path, config, judge_config)
    assert status["controlled_judge"]["status"] == "partial"
    assert status["controlled_judge"]["terminal_requests"] == 1
    assert status["real_diagnostic_evaluation"]["status"] == "not_evaluated"
