#!/usr/bin/env python3
"""Build the dynamic Chinese experiment report."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cbm_drift_v2.reporting import build_report

if __name__ == "__main__":
    result = build_report(ROOT)
    print(json.dumps({"report": "results/CBM_DRIFT_DIAGNOSTIC_REPORT_ZH.md", "mad_records": result["mad_inventory"]["records"]}, indent=2))
