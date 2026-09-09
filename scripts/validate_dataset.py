#!/usr/bin/env python3
"""Validate a generated JSONL dataset."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mad_attr_filter.io import read_jsonl
from mad_attr_filter.validation import ValidationError, validate_dataset


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate MAD attribute-filter JSONL data.")
    parser.add_argument("jsonl_path", help="Path to the JSONL dataset.")
    parser.add_argument(
        "--no-pilot-balance",
        action="store_true",
        help="Skip pilot gold-position balance check.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    path = Path(args.jsonl_path)
    if not path.is_absolute():
        path = ROOT / path
    try:
        samples = read_jsonl(path)
        summary = validate_dataset(samples, enforce_pilot_gold_balance=not args.no_pilot_balance)
    except (OSError, ValueError, ValidationError) as exc:
        print(f"Validation failed: {exc}", file=sys.stderr)
        return 1

    print(f"Validation passed for {summary.total_samples} samples.")
    print(f"Option closeness counts: {summary.option_closeness_counts}")
    print(f"Structural complexity counts: {summary.structural_complexity_counts}")
    print(f"Scenario counts: {summary.scenario_counts}")
    print(f"Gold distribution: {summary.gold_position_distribution}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
