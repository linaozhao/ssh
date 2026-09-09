#!/usr/bin/env python3
"""Generate the complete English v4 factorized-difficulty example pool."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mad_attr_filter.io import read_jsonl, write_jsonl
from mad_attr_filter.v4_generator import generate_v4_pool
from mad_attr_filter.v4_reports import write_v4_generator_report
from mad_attr_filter.v4_validation import validate_v4_pool


def parse_args() -> argparse.Namespace:
    """Parse command-line options."""
    parser = argparse.ArgumentParser(
        description="Generate all 18 cells of the v4 factorized attribute-filter pool."
    )
    parser.add_argument(
        "--items-per-cell",
        type=int,
        default=10,
        help="Number of items to generate in each of the 18 cells (default: 10).",
    )
    parser.add_argument(
        "--output",
        default="data/multi_constraint_v4_pool.jsonl",
        help="JSONL output path relative to the project root.",
    )
    parser.add_argument(
        "--report-output",
        default="v4_generator_report.md",
        help="Markdown validation report path relative to the project root.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Global random seed.")
    parser.add_argument(
        "--max-retries-per-item",
        type=int,
        default=100,
        help="Maximum generation attempts for one item.",
    )
    return parser.parse_args()


def _resolve_path(raw_path: str) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else ROOT / path


def main() -> int:
    """Generate, serialize, reload, validate, and report the v4 pool."""
    args = parse_args()
    if args.items_per_cell < 1:
        raise SystemExit("--items-per-cell must be positive")
    output_path = _resolve_path(args.output)
    report_path = _resolve_path(args.report_output)
    items, generation_report = generate_v4_pool(
        args.items_per_cell,
        global_seed=args.seed,
        max_retries_per_item=args.max_retries_per_item,
    )
    write_jsonl(output_path, items)

    reloaded_items = read_jsonl(output_path)
    validate_v4_pool(reloaded_items, expected_items_per_cell=args.items_per_cell)
    write_v4_generator_report(
        report_path,
        reloaded_items,
        generation_report,
        output_path=str(output_path.relative_to(ROOT))
        if output_path.is_relative_to(ROOT)
        else str(output_path),
    )

    print(f"Wrote {len(items)} v4 items to {output_path}")
    print(f"Wrote validation report to {report_path}")
    print(f"Difficulty cells: {generation_report['num_cells']}")
    print(f"Items per cell: {generation_report['items_per_cell']}")
    print(f"Validation pass rate: {generation_report['validation_pass_rate']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
