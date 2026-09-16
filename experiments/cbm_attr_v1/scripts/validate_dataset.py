#!/usr/bin/env python3
"""Validate every generated CBM-Attr v1 artifact."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(EXPERIMENT / "src")]

from cbm_attr_v1.validation import validate_artifacts  # noqa: E402


def main() -> None:
    report = validate_artifacts(EXPERIMENT / "data", report_path=EXPERIMENT / "data/validation_report.json")
    print(json.dumps(report["counts"], indent=2))
    if not report["valid"]:
        print(json.dumps(report["errors"][:20], indent=2))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
