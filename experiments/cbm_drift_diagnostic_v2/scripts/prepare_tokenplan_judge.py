#!/usr/bin/env python3
"""Freeze a configured TokenPlan Judge experiment and request queue."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cbm_drift_v2.common import read_json
from cbm_drift_v2.tokenplan_judge import prepare_tokenplan_experiment


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config/tokenplan_deepseek_v4_pro.json")
    args = parser.parse_args()
    config = read_json(args.config)
    print(json.dumps(prepare_tokenplan_experiment(ROOT, config), ensure_ascii=False, indent=2))
