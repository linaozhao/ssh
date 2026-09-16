#!/usr/bin/env python3
"""Prepare deterministic CBM-Attr v1 artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(EXPERIMENT / "src")]

from cbm_attr_v1.prepare import prepare_all  # noqa: E402


def main() -> None:
    config = json.loads((EXPERIMENT / "config/experiment_config.json").read_text())
    counts = prepare_all(
        ROOT / config["source_dataset"],
        EXPERIMENT / "data",
        selection_seed=config["selection_seed"],
        schedule_seed=config["schedule_seed"],
        run_seeds=config["seeds"],
    )
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()
