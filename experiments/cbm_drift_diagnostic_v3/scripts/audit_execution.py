"""Independently replay saved request lineage without any inference calls."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cbm_drift_v3.common import read_json, read_jsonl, sha256_file, sha256_json, write_json, write_jsonl
from cbm_drift_v3.runner import build_messages
from cbm_drift_v3.prompts import TASK_SYSTEM_PROMPT, snapshot_user_message
from cbm_drift_v3.state import score_answer
from cbm_drift_v3.parsing import parse_answer_set


def audit(config: dict, result: Path, data: Path) -> dict:
    """Verify uniqueness, immutable context, formal scoring and raw provenance."""
    sequences = read_jsonl(data / "evidence_sequences.jsonl")
    seqs = {s["sequence_id"]: s for s in sequences}
    summaries, inventory = {}, []
    for stage, plan_name in (("protocol", "protocol_request_plan.jsonl"), ("mad", "mad_request_plan.jsonl")):
        plan = read_jsonl(data / plan_name)
        directory = result / stage
        manifest = read_json(directory / "execution_manifest.json")
        errors = []
        if manifest["data"] != sha256_json(sequences) or manifest["plan"] != sha256_json(plan):
            errors.append({"error": "data_or_plan_fingerprint_mismatch"})
        if manifest["config"] != sha256_json(config):
            errors.append({"error": "config_fingerprint_mismatch"})
        records = {}
        for path in sorted((directory / "records").glob("*.json")):
            row = read_json(path)
            rid = row["request_id"]
            if rid in records:
                errors.append({"request_id": rid, "error": "duplicate_record"})
            records[rid] = row
            inventory.append({"stage": stage, "request_id": rid, "path": str(path.relative_to(result)),
                              "bytes": path.stat().st_size, "sha256": sha256_file(path)})
        expected = {r["request_id"] for r in plan}
        errors.extend({"request_id": rid, "error": "unknown_request"} for rid in records.keys() - expected)
        completed, scores = {}, Counter()
        for req in plan:
            rid = req["request_id"]
            if rid not in records:
                continue
            row, seq = records[rid], seqs[req["sequence_id"]]
            try:
                if row["is_mock"] or row["run_id"] != config["run_id"] or row["run_fingerprint"] != sha256_json(manifest):
                    raise ValueError("foreign_or_mock_record")
                if any(row.get(k) != v for k, v in req.items()):
                    raise ValueError("request_metadata_changed")
                messages = ([{"role": "system", "content": TASK_SYSTEM_PROMPT},
                             {"role": "user", "content": snapshot_user_message(seq, req["evidence_stage"])}]
                            if stage == "protocol" else build_messages(req, seq, completed))
                if messages != row["messages"] or row["messages_sha256"] != sha256_json(messages):
                    raise ValueError("history_or_visibility_mismatch")
                state = seq["stage_states"][req["evidence_stage"] - 1]
                parents = {mid: sha256_json(completed[mid]["raw_response"]) for mid in req.get("depends_on", [])}
                if row["parent_response_hashes"] != parents or row["state_sha256"] != sha256_json(state):
                    raise ValueError("parent_or_state_fingerprint_mismatch")
                payload = {**row["actual_generation_parameters"], "messages": messages}
                if row["request_sha256"] != sha256_json({"payload": payload, "state": state, "parents": parents, "run": manifest}):
                    raise ValueError("request_payload_fingerprint_mismatch")
                for key in ("temperature", "top_p", "max_tokens"):
                    if payload[key] != config["generation"][key]:
                        raise ValueError("generation_parameter_mismatch")
                if payload["seed"] != req["seed"] or payload["model"] != config["model"]["model_name"]:
                    raise ValueError("model_or_seed_mismatch")
                if payload.get("chat_template_kwargs", {}).get("enable_thinking") is not False:
                    raise ValueError("thinking_mode_mismatch")
                if row["api_success"]:
                    response = row["response"]
                    choice = response["choices"][0]
                    if (response.get("model") != config["model"]["model_name"]
                            or (choice["message"].get("content") or "") != row["raw_response"]
                            or choice.get("finish_reason") != row["finish_reason"]
                            or response.get("usage") != row["usage"]):
                        raise ValueError("provider_response_copy_mismatch")
                    parsed = parse_answer_set(row["raw_response"], {c: v["name"] for c, v in seq["candidate_map"].items()})
                    if parsed != row["parsed"]:
                        raise ValueError("parse_mismatch")
                    scores[score_answer(seq["rules"], state["active_evidence"], parsed["answer_set"])["answer_status"]] += 1
                completed[rid] = row
            except (ValueError, KeyError, IndexError, TypeError, RuntimeError) as exc:
                errors.append({"request_id": rid, "error": str(exc)})
        attempts = read_jsonl(directory / "attempts.jsonl")
        summaries[stage] = {"expected": len(plan), "records": len(records), "missing": len(expected - records.keys()),
                            "api_success": sum(r["api_success"] for r in records.values()), "http_attempts": len(attempts),
                            "failed_records": sum(not r["api_success"] for r in records.values()),
                            "audit_errors": len(errors), "errors": errors,
                            "answer_status_counts": dict(scores),
                            "status": "passed" if not errors and expected == records.keys() else "partial" if not errors else "failed"}
    write_jsonl(result / "raw_response_inventory.jsonl", inventory)
    status = "failed" if any(s["status"] == "failed" for s in summaries.values()) else "passed" if all(s["status"] == "passed" for s in summaries.values()) else "partial"
    summary = {"status": status, "stages": summaries}
    write_json(result / "execution_validation.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    config = read_json(args.config)
    summary = audit(config, ROOT / "results" / config["run_id"], ROOT / config.get("data_subdir", "data"))
    print(json.dumps(summary, indent=2))
    return 0 if summary["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
