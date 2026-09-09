#!/usr/bin/env python3
"""Select vulnerable items and stratified stable controls for the MAD pilot."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mad_attr_filter.io import load_json, read_jsonl, write_jsonl
from mad_attr_filter.mad_pilot import select_mad_pilot_manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare the small baseline MAD pilot manifest.")
    parser.add_argument("--candidates", default="results/mad_candidate_items.jsonl")
    parser.add_argument("--config", default="config/mad_pilot_config.json")
    parser.add_argument("--output", default="results/mad_pilot_manifest.jsonl")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    candidates = read_jsonl(ROOT / args.candidates)
    config = load_json(ROOT / args.config)
    manifest = select_mad_pilot_manifest(
        candidates,
        stable_control_count=int(config["stable_control_count"]),
        seed=int(config["selection_seed"]),
    )
    write_jsonl(ROOT / args.output, manifest)
    summary = {
        "items": len(manifest),
        "pilot_group": dict(Counter(record["pilot_group"] for record in manifest)),
        "screening_category": dict(Counter(record["screening_category"] for record in manifest)),
        "scenario": dict(Counter(record["scenario"] for record in manifest)),
        "structural_complexity": dict(Counter(record["structural_complexity"] for record in manifest)),
        "stable_control_scenarios": dict(
            Counter(record["scenario"] for record in manifest if record["pilot_group"] == "stable_control")
        ),
        "stable_control_complexity": dict(
            Counter(
                record["structural_complexity"]
                for record in manifest
                if record["pilot_group"] == "stable_control"
            )
        ),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
