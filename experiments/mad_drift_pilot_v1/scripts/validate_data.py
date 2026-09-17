#!/usr/bin/env python3
"""Validate frozen data and request dependencies."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path[:0] = [str(ROOT / "src"), str(REPO / "src"), str(REPO / "experiments/cbm_attr_v1/src")]

from mad_drift_pilot.common import read_jsonl, write_json  # noqa: E402
from mad_drift_pilot.validation import validate_frozen_data  # noqa: E402


if __name__ == "__main__":
    data = ROOT / "data"
    report = validate_frozen_data(
        read_jsonl(data / "source_items.jsonl"), read_jsonl(data / "episodes.jsonl"),
        read_jsonl(data / "protocol_request_plan.jsonl"), read_jsonl(data / "mad_request_plan.jsonl"),
    )
    write_json(data / "validation_report.json", report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    raise SystemExit(0 if report["passed"] else 1)
