#!/usr/bin/env python3
"""Validate frozen TokenPlan manifests and current result completeness."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cbm_drift_v2.common import read_json, read_jsonl, sha256_json, write_json
from cbm_drift_v2.tokenplan_judge import results_directory, validate_preflight


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--config", type=Path, default=ROOT / "config/tokenplan_deepseek_v4_pro.json")
    args = parser.parse_args()
    config = read_json(args.config)
    results = results_directory(ROOT, config)
    manifest = read_json(results / "experiment_manifest.json")
    queue = read_jsonl(results / "request_queue.jsonl")
    outputs = read_jsonl(results / "judge_outputs.jsonl") if (results / "judge_outputs.jsonl").exists() else []
    output_ids = [row["judge_request_id"] for row in outputs]
    queue_ids = {row["judge_request_id"] for row in queue}
    errors = []
    if sha256_json(config) != manifest["config_sha256"]:
        errors.append("config fingerprint mismatch")
    if any(row.get("experiment_fingerprint") != manifest["experiment_fingerprint"] for row in outputs):
        errors.append("output experiment fingerprint mismatch")
    if len(queue) != 1800 or len(queue_ids) != 1800:
        errors.append("request queue is not 1800 unique records")
    if len(output_ids) != len(set(output_ids)):
        errors.append("duplicate output request IDs")
    if set(output_ids) - queue_ids:
        errors.append("unknown output request IDs")
    if not args.allow_partial and len(outputs) != len(queue):
        errors.append("formal Judge coverage is incomplete")
    if not args.allow_partial and any(not row["api_success"] for row in outputs):
        errors.append("unresolved API failures remain")
    preflight = validate_preflight(ROOT, config)
    if not args.allow_partial and not preflight["passed"]:
        errors.append("preflight validation has not passed")
    result = {
        "passed": not errors,
        "validation_scope": "frozen_queue_and_partial_records" if args.allow_partial else "complete_experiment",
        "experiment_complete": len(outputs) == len(queue) and preflight["passed"] and all(
            row["api_success"] and row["parse_success"] and row["schema_valid"] for row in outputs
        ),
        "partial_allowed": args.allow_partial,
        "errors": errors,
        "experiment_fingerprint": manifest["experiment_fingerprint"],
        "expected": len(queue),
        "completed": len(outputs),
        "remaining": len(queue) - len(outputs),
        "api_failures": sum(not row["api_success"] for row in outputs),
        "parse_failures": sum(not row["parse_success"] for row in outputs),
        "schema_invalid": sum(not row["schema_valid"] for row in outputs),
        "truncated": sum(row.get("finish_reason") == "length" for row in outputs),
        "preflight": preflight,
    }
    write_json(results / "validation.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
