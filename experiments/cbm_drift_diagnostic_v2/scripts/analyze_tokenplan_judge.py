#!/usr/bin/env python3
"""Analyze TokenPlan Judge progress and build the Chinese report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cbm_drift_v2.tokenplan_analysis import build_chinese_report
from cbm_drift_v2.common import read_json


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config/tokenplan_deepseek_v4_pro.json")
    args = parser.parse_args()
    print(json.dumps(build_chinese_report(ROOT, read_json(args.config)), ensure_ascii=False, indent=2))
