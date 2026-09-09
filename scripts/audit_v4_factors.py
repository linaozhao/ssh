#!/usr/bin/env python3
"""Audit per-cell balance and factor realization in a v4.1 prototype."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mad_attr_filter.factor_audit import write_factor_audit, write_refinement_report
from mad_attr_filter.io import read_jsonl


def parse_args() -> argparse.Namespace:
    """Parse command-line options."""
    parser = argparse.ArgumentParser(description="Audit v4.1 difficulty-factor cells.")
    parser.add_argument(
        "input",
        nargs="?",
        default="data/multi_constraint_v4_1_prototype.jsonl",
        help="Input v4.1 JSONL path relative to the project root.",
    )
    parser.add_argument(
        "--output",
        default="v4_factor_audit.json",
        help="Audit JSON path relative to the project root.",
    )
    parser.add_argument(
        "--refinement-report-output",
        default="V4_1_REFINEMENT_REPORT.md",
        help="Refinement report path relative to the project root.",
    )
    return parser.parse_args()


def _resolve_path(raw_path: str) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else ROOT / path


def main() -> int:
    """Read, audit, and report one v4.1 pool."""
    args = parse_args()
    input_path = _resolve_path(args.input)
    output_path = _resolve_path(args.output)
    refinement_path = _resolve_path(args.refinement_report_output)
    items = read_jsonl(input_path)
    audit = write_factor_audit(output_path, items)
    write_refinement_report(refinement_path, items, audit)
    print(f"Audited {len(items)} items across {audit['num_difficulty_cells']} cells")
    print(f"Wrote factor audit to {output_path}")
    print(f"Wrote refinement report to {refinement_path}")
    print(f"No obvious confounding detected: {audit['no_obvious_confounding_detected']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
