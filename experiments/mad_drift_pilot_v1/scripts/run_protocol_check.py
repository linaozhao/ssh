#!/usr/bin/env python3
"""Run or resume the 18-item candidate-set protocol check."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path[:0] = [str(ROOT / "src"), str(REPO / "src"), str(REPO / "experiments/cbm_attr_v1/src")]

from mad_drift_pilot.common import read_json  # noqa: E402
from mad_drift_pilot.runner import ProtocolCheckRunner  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit-units", type=int)
    args = parser.parse_args()
    runner = ProtocolCheckRunner(ROOT, read_json(ROOT / "config/experiment_config.json"), REPO)
    print(json.dumps(runner.run(limit_units=args.limit_units), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
