#!/usr/bin/env python3
# ruff: noqa: E402
"""Migrate saved follow-up outputs to the current parser without model calls."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mad_attr_filter.io import load_json, read_jsonl, write_json, write_jsonl
from mad_attr_filter.qwen_followup import (
    FOLLOWUP_PARSER_REVISION,
    FOLLOWUP_PROTOCOL_VERSION,
    build_followup_fingerprints,
    canonical_hash,
    parse_followup_response,
    sha256_file,
)
from mad_attr_filter.qwen_followup_runner import materialize_experiment_config


PARSE_FIELDS = (
    "raw_answer",
    "answer",
    "reasoning",
    "confidence",
    "answer_extractable",
    "json_compliant",
    "strict_json_syntax",
    "strict_answer_format",
    "semantic_name_mapping_used",
    "parse_source",
    "fallback_used",
    "ambiguous_answer",
    "answer_candidates",
    "parse_error",
)


def main() -> int:
    full_config = load_json(ROOT / "config/qwen_v4_1_followup_config.json")
    overall: dict[str, object] = {
        "from_parser_revision": "qwen-v4.1-name-aware-parser-1",
        "to_parser_revision": FOLLOWUP_PARSER_REVISION,
        "new_model_calls": 0,
        "experiments": {},
    }
    for name in ("position_order", "information_load", "extension"):
        config = materialize_experiment_config(full_config, name)
        dataset_path = ROOT / config["dataset"]
        results_dir = ROOT / config["results_dir"]
        output_path = results_dir / "single_agent_outputs.jsonl"
        manifest_path = results_dir / "experiment_manifest.json"
        samples = {item["item_id"]: item for item in read_jsonl(dataset_path)}
        records = read_jsonl(output_path)
        old_file_hash = sha256_file(output_path)
        old_raw_hash = canonical_hash(
            [
                {
                    "variant_id": record["variant_id"],
                    "run_id": record["run_id"],
                    "raw_response": record["raw_response"],
                }
                for record in records
            ]
        )
        changed: list[dict[str, object]] = []
        updated_records = []
        new_fingerprints = build_followup_fingerprints(dataset_path, config)
        for record in records:
            item = samples[str(record["item_id"])]
            updated = dict(record)
            if record.get("request_error") is None:
                parsed = parse_followup_response(str(record.get("raw_response", "")), item)
                for field in PARSE_FIELDS:
                    updated[field] = parsed[field]
                answer = parsed["answer"]
                valid = answer in ("A", "B", "C", "D")
                updated["selected_candidate_name"] = (
                    item["entities"][answer]["name"] if valid else None
                )
                updated["correct"] = bool(valid and answer == item["gold_answer"])
                updated["strict_format_correct"] = bool(
                    parsed["strict_answer_format"] and answer == item["gold_answer"]
                )
                updated["selected_option_violation_signature"] = (
                    list(item["option_violation_signature"][answer]) if valid else []
                )
            if updated.get("answer") != record.get("answer"):
                changed.append(
                    {
                        "variant_id": record["variant_id"],
                        "run_id": record["run_id"],
                        "old_answer": record.get("answer"),
                        "new_answer": updated.get("answer"),
                    }
                )
            updated["parser_revision"] = FOLLOWUP_PARSER_REVISION
            updated["protocol_version"] = FOLLOWUP_PROTOCOL_VERSION
            updated["experiment_fingerprint"] = new_fingerprints["experiment_sha256"]
            updated_records.append(updated)
        write_jsonl(output_path, updated_records)
        new_raw_hash = canonical_hash(
            [
                {
                    "variant_id": record["variant_id"],
                    "run_id": record["run_id"],
                    "raw_response": record["raw_response"],
                }
                for record in updated_records
            ]
        )
        if new_raw_hash != old_raw_hash:
            raise ValueError(f"Raw responses changed while reparsing {name}")
        manifest = load_json(manifest_path)
        manifest["fingerprints"] = new_fingerprints
        manifest["parser_revision"] = FOLLOWUP_PARSER_REVISION
        manifest["parser_migration"] = {
            "from": "qwen-v4.1-name-aware-parser-1",
            "to": FOLLOWUP_PARSER_REVISION,
            "new_model_calls": 0,
            "raw_response_hash_unchanged": True,
            "answer_changes": len(changed),
        }
        write_json(manifest_path, manifest)
        overall["experiments"][name] = {
            "records": len(records),
            "old_output_sha256": old_file_hash,
            "new_output_sha256": sha256_file(output_path),
            "raw_response_hash": new_raw_hash,
            "raw_response_hash_unchanged": True,
            "answer_change_count": len(changed),
            "answer_changes": changed,
            "new_experiment_fingerprint": new_fingerprints["experiment_sha256"],
        }
    write_json(
        ROOT / "results/qwen_v4_1_followup/parser_migration_audit.json",
        overall,
    )
    print(json.dumps(overall, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
