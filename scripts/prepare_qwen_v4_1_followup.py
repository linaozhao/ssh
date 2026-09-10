#!/usr/bin/env python3
# ruff: noqa: E402
"""Freeze Qwen follow-up diagnostics and the independent v4.1 extension."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mad_attr_filter.io import read_jsonl, write_json, write_jsonl
from mad_attr_filter.factor_audit import build_factor_audit
from mad_attr_filter.qwen_followup import (
    EXTENSION_BATCH_ID,
    EXTENSION_GLOBAL_SEED,
    IL_PAIR_SELECTION_SEED,
    build_extension_pool,
    build_information_load_pairs,
    build_position_variants,
    extension_index_records,
)
from mad_attr_filter.v4_validation import validate_v4_pool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--prototype",
        default="data/multi_constraint_v4_1_prototype.jsonl",
    )
    parser.add_argument(
        "--prior-item-analysis",
        default="results/v4_1_calibration/item_model_analysis.jsonl",
    )
    parser.add_argument(
        "--results-dir",
        default="results/qwen_v4_1_followup",
    )
    return parser.parse_args()


def _resolve(path: str) -> Path:
    value = Path(path)
    return value if value.is_absolute() else ROOT / value


def _write_or_verify_jsonl(path: Path, records: list[dict]) -> None:
    if path.exists():
        if read_jsonl(path) != records:
            raise ValueError(f"Frozen artifact differs from regenerated content: {path}")
        return
    write_jsonl(path, records)


def _write_or_verify_json(path: Path, value: dict) -> None:
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing != value:
            raise ValueError(f"Frozen artifact differs from regenerated content: {path}")
        return
    write_json(path, value)


def main() -> int:
    args = parse_args()
    prototype_path = _resolve(args.prototype)
    item_analysis_path = _resolve(args.prior_item_analysis)
    results_dir = _resolve(args.results_dir)
    position_dir = results_dir / "position_order"
    il_dir = results_dir / "information_load"
    extension_dir = results_dir / "extension"
    for path in (position_dir, il_dir, extension_dir):
        path.mkdir(parents=True, exist_ok=True)

    prototype = read_jsonl(prototype_path)
    validate_v4_pool(prototype, expected_items_per_cell=10)
    qwen_rows = [
        row
        for row in read_jsonl(item_analysis_path)
        if row.get("model_alias") == "qwen"
    ]
    if len(qwen_rows) != 180:
        raise ValueError(f"Expected 180 prior Qwen item rows, got {len(qwen_rows)}")

    position_variants, position_manifest = build_position_variants(prototype, qwen_rows)
    _write_or_verify_jsonl(position_dir / "variants.jsonl", position_variants)
    _write_or_verify_jsonl(position_dir / "manifest.jsonl", position_manifest)
    _write_or_verify_json(
        position_dir / "validation.json",
        {
            "base_item_count": 21,
            "variant_count": 84,
            "stable_wrong_base_count": 10,
            "mixed_base_count": 1,
            "stable_correct_control_count": 10,
            "rotations_per_item": 4,
            "all_variants_validated": True,
            "all_gold_positions_covered_per_base": True,
        },
    )

    il_variants, il_manifest = build_information_load_pairs(
        prototype,
        selection_seed=IL_PAIR_SELECTION_SEED,
    )
    _write_or_verify_jsonl(il_dir / "variants.jsonl", il_variants)
    _write_or_verify_jsonl(il_dir / "manifest.jsonl", il_manifest)
    _write_or_verify_json(
        il_dir / "validation.json",
        {
            "selection_seed": IL_PAIR_SELECTION_SEED,
            "base_item_count": 36,
            "variant_count": 72,
            "cl_ds_group_count": 9,
            "items_per_cl_ds_group": 4,
            "only_marked_non_target_facts_removed": True,
            "formal_equivalence_validated": True,
        },
    )

    extension, extension_report = build_extension_pool(
        prototype,
        items_per_cell=20,
        global_seed=EXTENSION_GLOBAL_SEED,
        start_index=181,
    )
    combined = [*prototype, *extension]
    extension_path = ROOT / "data/multi_constraint_v4_1_extension_360.jsonl"
    combined_path = ROOT / "data/multi_constraint_v4_1_total_540.jsonl"
    index_path = ROOT / "data/multi_constraint_v4_1_total_540_index.jsonl"
    _write_or_verify_jsonl(extension_path, extension)
    _write_or_verify_jsonl(combined_path, combined)
    _write_or_verify_jsonl(index_path, extension_index_records(prototype, extension))
    _write_or_verify_json(extension_dir / "validation.json", extension_report)
    _write_or_verify_json(
        extension_dir / "extension_factor_audit.json",
        build_factor_audit(extension),
    )
    _write_or_verify_json(
        extension_dir / "combined_factor_audit.json",
        build_factor_audit(combined),
    )
    _write_or_verify_json(
        extension_dir / "pool_manifest.json",
        {
            "batch_id": EXTENSION_BATCH_ID,
            "global_seed": EXTENSION_GLOBAL_SEED,
            "prototype_path": str(prototype_path.relative_to(ROOT)),
            "extension_path": str(extension_path.relative_to(ROOT)),
            "combined_path": str(combined_path.relative_to(ROOT)),
            "combined_index_path": str(index_path.relative_to(ROOT)),
            "prototype_items": 180,
            "extension_items": 360,
            "combined_items": 540,
            "extension_items_per_cell": 20,
            "combined_items_per_cell": 30,
            "frozen_before_model_inference": True,
            "model_outcomes_used_for_generation_or_filtering": False,
        },
    )
    print(
        json.dumps(
            {
                "position_variants": len(position_variants),
                "il_pair_variants": len(il_variants),
                "extension_items": len(extension),
                "combined_items": len(combined),
                "extension_validation": extension_report,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
