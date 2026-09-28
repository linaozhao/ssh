#!/usr/bin/env python3
"""Freeze the TokenPlan DeepSeek-V4-Pro Judge manifests and queue."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cbm_drift_v2.common import read_json
from cbm_drift_v2.tokenplan_judge import prepare_tokenplan_experiment


if __name__ == "__main__":
    config = read_json(ROOT / "config/tokenplan_deepseek_v4_pro.json")
    print(json.dumps(prepare_tokenplan_experiment(ROOT, config), ensure_ascii=False, indent=2))
