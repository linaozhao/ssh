#!/usr/bin/env python3
"""Audit frozen data, trajectories, diagnostics, Judge records, and annotation exports."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cbm_drift_v2.common import read_json, read_jsonl, sha256_json, write_json
from cbm_drift_v2.runner import audit_outputs
from cbm_drift_v2.validation import validate_dataset


def main() -> None:
    errors: list[str] = []
    config = read_json(ROOT / "config/experiment_config.json")
    sequences = read_jsonl(ROOT / "data/evidence_sequences.jsonl")
    protocol_plan = read_jsonl(ROOT / "data/protocol_request_plan.jsonl")
    mad_plan = read_jsonl(ROOT / "data/mad_request_plan.jsonl")
    data_check = validate_dataset(config, sequences, protocol_plan, mad_plan)
    errors.extend(data_check["errors"])
    by_variant = {row["variant_id"]: row for row in sequences}
    protocol_audit, mad_audit = audit_outputs(ROOT, "protocol"), audit_outputs(ROOT, "mad")
    for audit in (protocol_audit, mad_audit):
        if audit["missing"] or audit["unknown"] or audit["duplicates"]:
            errors.append(f"{audit['kind']} inventory mismatch")
    mad = read_jsonl(ROOT / "results/mad/raw_outputs.jsonl")
    for row in mad:
        sequence = by_variant[row["variant_id"]]
        state = sequence["stage_states"][int(row["evidence_stage"]) - 1]
        if row["oracle"] != state["oracle"]:
            errors.append(f"{row['message_id']}: oracle mismatch")
        future_ids = {
            event["evidence_id"] for stage in sequence["stages"]
            if int(stage["evidence_stage"]) > int(row["evidence_stage"])
            for event in stage["events"]
        }
        rendered = json.dumps(row["messages"], ensure_ascii=False)
        if any(evidence_id in rendered for evidence_id in future_ids):
            errors.append(f"{row['message_id']}: future evidence leakage")
        visible = row.get("visible_peer_message_ids", [])
        if int(row["round"]) == 0 and visible:
            errors.append(f"{row['message_id']}: R0 has current-stage peers")
        if int(row["round"]) > 0:
            expected_marker = f":t{row['evidence_stage']}:r{int(row['round']) - 1}:"
            if len(visible) != 2 or any(expected_marker not in value for value in visible):
                errors.append(f"{row['message_id']}: peer barrier mismatch")
    diagnostics_path = ROOT / "results/program/message_diagnostics.jsonl"
    if diagnostics_path.exists():
        diagnostics = read_jsonl(diagnostics_path)
        if len(diagnostics) != len(mad) or len({row["message_id"] for row in diagnostics}) != len(diagnostics):
            errors.append("program diagnostics do not cover each MAD message exactly once")
    judge_path = ROOT / "results/judge/judge_outputs.jsonl"
    judge_audit = {"status": "not_run"}
    if judge_path.exists():
        judge = read_jsonl(judge_path)
        expected = len(mad) * len(config["judge"]["protocols"])
        ids = [row["judge_request_id"] for row in judge]
        judge_audit = {
            "expected": expected, "records": len(judge), "unique": len(set(ids)),
            "api_failures": sum(not row["api_success"] for row in judge),
            "parse_failures": sum(not row["parse_success"] for row in judge),
            "schema_invalid": sum(not row["schema_valid"] for row in judge),
        }
        if len(judge) != expected or len(set(ids)) != expected:
            errors.append("Judge coverage or uniqueness mismatch")
    annotation_manifest = ROOT / "annotation/manifest.json"
    if annotation_manifest.exists():
        annotation = read_json(annotation_manifest)
        if annotation["trajectories"] != 36 or annotation["judge_predictions_included"]:
            errors.append("annotation package scope or blinding mismatch")
    result = {
        "passed": not errors, "errors": errors, "data": data_check,
        "protocol": {key: value for key, value in protocol_audit.items() if key not in {"missing", "unknown", "duplicates"}},
        "mad": {key: value for key, value in mad_audit.items() if key not in {"missing", "unknown", "duplicates"}},
        "judge": judge_audit,
        "experiment_config_sha256": sha256_json(config),
    }
    write_json(ROOT / "results/final_validation.json", result)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
