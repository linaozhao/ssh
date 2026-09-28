#!/usr/bin/env python3
"""Run or resume the frozen TokenPlan DeepSeek-V4-Pro Judge queue."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cbm_drift_v2.common import read_json
from cbm_drift_v2.tokenplan_judge import TokenPlanJudgeRunner, validate_preflight


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("preflight", "formal"), required=True)
    parser.add_argument("--max-new", type=int)
    parser.add_argument("--validate-preflight", action="store_true")
    args = parser.parse_args()
    config = read_json(ROOT / "config/tokenplan_deepseek_v4_pro.json")
    runner = TokenPlanJudgeRunner(ROOT, config)
    print(json.dumps(runner.run(args.phase, args.max_new), ensure_ascii=False, indent=2))
    if args.validate_preflight:
        print(json.dumps(validate_preflight(ROOT), ensure_ascii=False, indent=2))
