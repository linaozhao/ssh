#!/usr/bin/env python3
"""Run CBM-Attr v1 preflight or formal inference."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(EXPERIMENT / "src")]

from cbm_attr_v1.runner import ExperimentRunner  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("preflight", "formal"), required=True)
    parser.add_argument("--resume", action="store_true", help="Document intent; resume is always fingerprint-safe")
    args = parser.parse_args()
    config = json.loads((EXPERIMENT / "config/experiment_config.json").read_text())
    result = ExperimentRunner(EXPERIMENT, config).run(phase=args.phase)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
