#!/usr/bin/env python3
# ruff: noqa: E402
"""Validate frozen follow-up datasets, outputs, fingerprints, and scoring."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mad_attr_filter.io import load_json, read_jsonl, write_json
from mad_attr_filter.qwen_followup import build_followup_fingerprints, normalized_content_hash
from mad_attr_filter.qwen_followup_runner import (
    audit_output_inventory,
    materialize_experiment_config,
)
from mad_attr_filter.v4_validation import validate_v4_item, validate_v4_pool


def main() -> int:
    config = load_json(ROOT / "config/qwen_v4_1_followup_config.json")
    prototype = read_jsonl(ROOT / "data/multi_constraint_v4_1_prototype.jsonl")
    extension = read_jsonl(ROOT / "data/multi_constraint_v4_1_extension_360.jsonl")
    combined = read_jsonl(ROOT / "data/multi_constraint_v4_1_total_540.jsonl")
    base_validation = {
        "prototype": validate_v4_pool(prototype, expected_items_per_cell=10),
        "extension": validate_v4_pool(extension, expected_items_per_cell=20),
        "combined": validate_v4_pool(combined, expected_items_per_cell=30),
    }
    hashes = [normalized_content_hash(item) for item in combined]
    if len(hashes) != len(set(hashes)):
        raise ValueError("Combined base pool contains duplicate normalized content")

    experiment_audits = {}
    deterministic_scoring_errors = []
    total_records = 0
    for name in ("position_order", "information_load", "extension"):
        experiment = materialize_experiment_config(config, name)
        dataset_path = ROOT / experiment["dataset"]
        output_path = ROOT / experiment["results_dir"] / "single_agent_outputs.jsonl"
        items = read_jsonl(dataset_path)
        for item in items:
            validate_v4_item(item)
        item_by_id = {item["item_id"]: item for item in items}
        fingerprints = build_followup_fingerprints(dataset_path, experiment)
        records, inventory = audit_output_inventory(
            output_path, items, experiment, fingerprints["experiment_sha256"]
        )
        total_records += len(records)
        for record in records:
            item = item_by_id[record["item_id"]]
            answer = record.get("answer")
            valid = answer in ("A", "B", "C", "D")
            expected_correct = bool(valid and answer == item["gold_answer"])
            expected_signature = (
                item["option_violation_signature"][answer] if valid else []
            )
            expected_name = item["entities"][answer]["name"] if valid else None
            if (
                record.get("correct") != expected_correct
                or record.get("selected_option_violation_signature") != expected_signature
                or record.get("selected_candidate_name") != expected_name
            ):
                deterministic_scoring_errors.append(
                    [name, record["variant_id"], record["run_id"]]
                )
        experiment_audits[name] = {
            "dataset_items": len(items),
            "inventory": inventory,
            "api_failures": sum(record.get("request_error") is not None for record in records),
            "unrecognized_answers": sum(
                record.get("answer_extractable") is not True for record in records
            ),
            "json_noncompliant": sum(
                record.get("json_compliant") is not True for record in records
            ),
            "truncated": sum(record.get("truncated") is True for record in records),
        }
    if deterministic_scoring_errors:
        raise ValueError(f"Deterministic scoring errors: {deterministic_scoring_errors[:5]}")
    if total_records != 1548:
        raise ValueError(f"Expected 1548 new model records, found {total_records}")

    position_items = read_jsonl(
        ROOT / "results/qwen_v4_1_followup/position_order/variants.jsonl"
    )
    position_sources = {}
    for item in position_items:
        position_sources.setdefault(item["source_item_id"], set()).add(item["gold_answer"])
    if len(position_sources) != 21 or any(labels != set("ABCD") for labels in position_sources.values()):
        raise ValueError("Position variants do not cover all labels for every source")

    il_items = read_jsonl(
        ROOT / "results/qwen_v4_1_followup/information_load/variants.jsonl"
    )
    il_by_source = {}
    for item in il_items:
        il_by_source.setdefault(item["source_item_id"], []).append(item)
    for source, pair in il_by_source.items():
        if len(pair) != 2:
            raise ValueError(f"IL pair {source} does not have two versions")
        low = next(item for item in pair if item["pair_version"] == "IL1_low")
        high = next(item for item in pair if item["pair_version"] == "IL2_high")
        for field in (
            "constraints",
            "gold_answer",
            "option_constraint_matrix",
            "option_violation_signature",
        ):
            if low[field] != high[field]:
                raise ValueError(f"IL pair {source} changed formal field {field}")

    summary = {
        "base_dataset_validation": base_validation,
        "combined_unique_item_ids": len({item["item_id"] for item in combined}),
        "combined_unique_normalized_content_hashes": len(set(hashes)),
        "position_base_items": len(position_sources),
        "position_variants": len(position_items),
        "information_load_base_items": len(il_by_source),
        "information_load_variants": len(il_items),
        "experiment_audits": experiment_audits,
        "new_model_records": total_records,
        "deterministic_scoring_error_count": 0,
        "all_checks_passed": True,
    }
    write_json(ROOT / "results/qwen_v4_1_followup/final_validation.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
