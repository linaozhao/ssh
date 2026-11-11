"""Recheck immutable provider responses into a new, resumable analysis directory."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cbm_drift_v3.common import read_json, read_jsonl, sha256_file, write_json, write_jsonl
from cbm_drift_v3.judge import validate_prediction


def revalidate(source: Path, destination: Path) -> dict:
    """Preserve input/response hashes and request budgets; never query a model."""
    if destination.exists():
        raise ValueError("The revalidation destination must be new")
    if not (source / "status.json").exists():
        raise ValueError("The source execution must have stopped and saved its status")
    rows = read_jsonl(source / "outputs.jsonl")
    status = read_json(source / "status.json")
    attempts = read_jsonl(source / "attempts.jsonl")
    if (status.get("stop_reason") != "technical_preflight_not_passed" or len(rows) != 12
            or status.get("terminal_requests") != 12 or any(not row.get("preflight") for row in rows)
            or any("status" not in attempt for attempt in attempts)):
        raise ValueError("Only a stopped 12-request technical preflight may be migrated")
    if any(row["split"] != "dev" for row in rows):
        raise ValueError("This preflight compatibility fix cannot be tuned on holdout outputs")
    packages = {row["request_id"]: row for row in read_jsonl(source / "input_packages.jsonl")}
    destination.mkdir(parents=True)
    frozen = ("experiment_manifest.json", "request_queue.jsonl", "input_packages.jsonl", "preflight_manifest.jsonl", "attempts.jsonl")
    for name in frozen:
        shutil.copyfile(source / name, destination / name)
    audits = []
    keys = ("schema_valid", "quote_valid", "object_valid", "formal_valid", "errors", "quote_errors", "object_errors", "formal_errors")
    for row in rows:
        before = {key: row.get(key) for key in keys}
        if row.get("parse_success"):
            row.update(validate_prediction(json.loads(row["raw_response"]), packages[row["request_id"]]["package"]))
        audits.append({"request_id": row["request_id"], "before": before,
                       "after": {key: row.get(key) for key in keys}, "new_model_call": False})
    write_jsonl(destination / "outputs.jsonl", rows)
    write_jsonl(destination / "validation_revision_audit.jsonl", audits)
    provenance = {"source_directory": str(source.resolve()), "source_outputs_sha256": sha256_file(source / "outputs.jsonl"),
                  "source_implementation_sha256": sha256_file(source / "implementation_freeze.json"),
                  "inherited_requests": len(rows), "new_model_calls": 0,
                  "input_and_prompt_changed": False, "holdout_observed": False,
                  "change": "Resolve numeric evidence versions only through unique explicit cited/conflicting evidence.",
                  "request_budget": "Inherited attempts count toward the unchanged 144 logical / 288 HTTP budget.",
                  "frozen_input_hashes": {name: sha256_file(source / name) for name in frozen}}
    write_json(destination / "validation_revision_manifest.json", provenance)
    return provenance


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(revalidate(args.source, args.destination), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
