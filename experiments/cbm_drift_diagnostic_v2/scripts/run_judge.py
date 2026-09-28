#!/usr/bin/env python3
"""Run or resume direct and structured DeepSeek Judge pre-annotation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cbm_drift_v2.common import read_json
from cbm_drift_v2.judge import DeepSeekJudge, materialize_predicted_events

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit-requests", type=int)
    args = parser.parse_args()
    runner = DeepSeekJudge(ROOT, read_json(ROOT / "config/experiment_config.json"))
    print(json.dumps(runner.run(limit_requests=args.limit_requests), indent=2))
    print(json.dumps(materialize_predicted_events(ROOT), indent=2))
