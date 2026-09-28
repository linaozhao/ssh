#!/usr/bin/env python3
"""Validate the frozen v2 development data independently."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXPERIMENT / "src"))

from cbm_drift_v2.common import read_json, read_jsonl, write_json  # noqa: E402
from cbm_drift_v2.validation import validate_dataset  # noqa: E402


def main() -> None:
    config = read_json(EXPERIMENT / "config/experiment_config.json")
    data = EXPERIMENT / "data"
    report = validate_dataset(
        config,
        read_jsonl(data / "evidence_sequences.jsonl"),
        read_jsonl(data / "protocol_request_plan.jsonl"),
        read_jsonl(data / "mad_request_plan.jsonl"),
    )
    write_json(data / "validation_report.json", report)
    print(report)
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

