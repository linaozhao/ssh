#!/usr/bin/env python3
"""Materialize Judge JSONL after interruption without requiring API credentials."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cbm_drift_v2.tokenplan_judge import RESULTS_RELATIVE, materialize_atomic_records


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=Path, default=ROOT / RESULTS_RELATIVE)
    args = parser.parse_args()
    print(json.dumps(materialize_atomic_records(args.results_dir), ensure_ascii=False, indent=2))
