#!/usr/bin/env python3
"""Run or resume the 108 independent static protocol checks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cbm_drift_v2.common import read_json
from cbm_drift_v2.runner import ExperimentRunner, audit_outputs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true", help="Existing matching records are always skipped safely")
    args = parser.parse_args()
    del args
    runner = ExperimentRunner(ROOT, read_json(ROOT / "config/experiment_config.json"), "protocol")
    print(json.dumps(runner.run_protocol(), indent=2))
    print(json.dumps(audit_outputs(ROOT, "protocol"), indent=2))


if __name__ == "__main__":
    main()
