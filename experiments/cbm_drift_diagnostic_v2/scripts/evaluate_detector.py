#!/usr/bin/env python3
"""Evaluate Judge predictions against independent adjudicated references."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cbm_drift_v2.evaluation import evaluate_files


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", type=Path, default=ROOT / "results/judge/predicted_events.jsonl")
    parser.add_argument("--references", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "results/judge/evaluation.json")
    args = parser.parse_args()
    print(json.dumps(evaluate_files(args.predictions, args.references, args.output), indent=2))


if __name__ == "__main__":
    main()
