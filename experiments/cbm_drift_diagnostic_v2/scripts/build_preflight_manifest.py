#!/usr/bin/env python3
"""Record the deterministic two-family MAD preflight included in the formal run."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cbm_drift_v2.common import read_json, read_jsonl, sha256_json, write_jsonl


def main() -> None:
    config = read_json(ROOT / "config/experiment_config.json")
    sequences = read_jsonl(ROOT / "data/evidence_sequences.jsonl")
    outputs = read_jsonl(ROOT / "results/mad/raw_outputs.jsonl")
    families = sorted({row["family_id"] for row in sequences})[: int(config["mad"]["preflight_base_items"])]
    rows = []
    for sequence in sorted((row for row in sequences if row["family_id"] in families), key=lambda row: row["variant_id"]):
        records = [row for row in outputs if row["variant_id"] == sequence["variant_id"]]
        rows.append({
            "family_id": sequence["family_id"], "base_item_id": sequence["base_item_id"],
            "variant_id": sequence["variant_id"], "variant_type": sequence["variant_type"],
            "expected_messages": 45, "recorded_messages": len(records),
            "request_ids_sha256": sha256_json(sorted(row["request_id"] for row in records)),
            "api_failures": sum(not row["api_success"] for row in records),
            "unrecognized": sum(not row["recognized_answer"] for row in records),
            "truncated": sum(row["finish_reason"] == "length" for row in records),
            "included_in_formal_results": True,
        })
    write_jsonl(ROOT / "manifests/mad_preflight_manifest.jsonl", rows)
    print({"families": len(families), "trajectories": len(rows), "records": sum(row["recorded_messages"] for row in rows)})


if __name__ == "__main__":
    main()
