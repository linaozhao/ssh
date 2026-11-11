"""Check completed controlled requests and inherited raw-response provenance."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cbm_drift_v3.common import read_json, read_jsonl, sha256_file, sha256_json, write_json, write_jsonl
from cbm_drift_v3.judge import validate_prediction


def audit(directory: Path) -> dict:
    """No inference or label changes; check provider, queue and parser lineage."""
    rows = read_jsonl(directory / "outputs.jsonl")
    queue = {r["request_id"]: r for r in read_jsonl(directory / "request_queue.jsonl")}
    packages = {r["request_id"]: r for r in read_jsonl(directory / "input_packages.jsonl")}
    manifest = read_json(directory / "experiment_manifest.json")
    attempts = read_jsonl(directory / "attempts.jsonl")
    errors, validation_failures = [], []
    keys = ("schema_valid", "quote_valid", "object_valid", "formal_valid", "prediction")
    for row in rows:
        rid = row["request_id"]
        if rid not in queue or row["experiment_fingerprint"] != manifest["fingerprint"]:
            errors.append([rid, "foreign_request"])
            continue
        if any(row[k] != queue[rid][k] for k in ("case_id", "case_sha256", "protocol", "split", "messages_sha256")):
            errors.append([rid, "queue_metadata_changed"])
        if sha256_json(packages[rid]["messages"]) != queue[rid]["messages_sha256"]:
            errors.append([rid, "request_text_changed"])
        if row.get("api_success"):
            response = row["raw_provider_response"]
            choice = response["choices"][0]
            if response["model"] != manifest["config"]["model_name"] or choice["message"]["content"] != row["raw_response"]:
                errors.append([rid, "provider_response_mismatch"])
            if row.get("parse_success"):
                checked = validate_prediction(json.loads(row["raw_response"]), packages[rid]["package"])
                if any(checked[k] != row[k] for k in keys):
                    errors.append([rid, "validation_not_reproducible"])
        if not all(row.get(k) for k in keys[:4]):
            validation_failures.append({k: row.get(k) for k in ("request_id", "case_id", "protocol", "split", *keys[:4], "errors", "quote_errors", "object_errors", "formal_errors", "raw_response")})
    ids = [r["request_id"] for r in rows]
    if len(ids) != len(set(ids)) or set(ids) != set(queue):
        errors.append([None, "missing_duplicate_or_unknown_output"])
    inherited = read_json(directory / "validation_revision_manifest.json")
    source = Path(inherited["source_directory"])
    original = read_jsonl(source / "outputs.jsonl")
    if sha256_file(source / "outputs.jsonl") != inherited["source_outputs_sha256"]:
        errors.append([None, "original_response_archive_changed"])
    by_id = {r["request_id"]: r for r in rows}
    for row in original:
        if any(row[k] != by_id[row["request_id"]][k] for k in ("raw_response", "raw_provider_response", "usage", "latency_seconds")):
            errors.append([row["request_id"], "inherited_raw_response_changed"])
    summary = {"status": "passed" if not errors else "failed", "integrity_errors": errors,
               "unique_logical_requests": len(set(ids)), "http_attempts": len(attempts),
               "inherited_preflight_requests": len(original), "additional_calls_for_revalidation": 0,
               "api_success": sum(r.get("api_success", False) for r in rows),
               "validation_pass_counts": {k: sum(r.get(k, False) for r in rows) for k in keys[:4]},
               "formal_validation_failure_rows": len(validation_failures),
               "split_protocol_counts": dict(Counter(f"{r['split']}/{r['protocol']}" for r in rows)),
               "model": manifest["config"]["model_name"], "reference_kind": "program_verified_not_human",
               "outputs_sha256": sha256_file(directory / "outputs.jsonl"),
               "note": "Integrity passing does not mean all model diagnostics are correct."}
    write_json(directory / "execution_validation.json", summary)
    write_jsonl(directory / "response_validation_audit.jsonl", validation_failures)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    result = audit(args.directory)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
