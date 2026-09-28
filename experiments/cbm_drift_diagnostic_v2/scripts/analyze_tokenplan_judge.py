#!/usr/bin/env python3
"""Analyze TokenPlan Judge progress and build the Chinese report."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cbm_drift_v2.tokenplan_analysis import build_chinese_report


if __name__ == "__main__":
    print(json.dumps(build_chinese_report(ROOT), ensure_ascii=False, indent=2))
