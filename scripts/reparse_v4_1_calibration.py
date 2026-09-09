#!/usr/bin/env python3
"""Reparse stored v4.1 responses without repeating model inference."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mad_attr_filter.io import load_json, read_jsonl, write_jsonl
from mad_attr_filter.v4_calibration import PARSER_REVISION, reparse_output_record


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reparse saved v4.1 calibration responses.")
    parser.add_argument("--config", default="config/v4_1_calibration_config.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_json(ROOT / args.config)
    samples = {
        sample["item_id"]: sample for sample in read_jsonl(ROOT / config["dataset"])
    }
    results_dir = ROOT / config["results_dir"]
    summary: dict[str, dict[str, object]] = {}
    for name in ("preflight_outputs.jsonl", "single_agent_outputs.jsonl"):
        path = results_dir / name
        records = read_jsonl(path)
        reparsed = [reparse_output_record(record, samples[record["item_id"]]) for record in records]
        write_jsonl(path, reparsed)
        summary[name] = {
            "records": len(reparsed),
            "valid_answers": sum(record["answer_extractable"] for record in reparsed),
            "json_compliant": sum(record["json_compliant"] for record in reparsed),
            "parse_sources": dict(Counter(record["parse_source"] for record in reparsed)),
        }
    print(json.dumps({"parser_revision": PARSER_REVISION, "files": summary}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
