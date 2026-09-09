#!/usr/bin/env python3
"""Assemble and analyze the small baseline MAD pilot trajectories."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mad_attr_filter.io import load_json, read_jsonl, write_json, write_jsonl
from mad_attr_filter.mad_analysis import (
    build_key_cases_markdown,
    build_mad_report_markdown,
    build_mad_statistics,
    build_mad_trajectories,
    flatten_events,
)
from mad_attr_filter.mad_pilot import load_mad_progress


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze the small baseline MAD pilot.")
    parser.add_argument("--dataset", default="data/pilot_en_v3.jsonl")
    parser.add_argument("--manifest", default="results/mad_pilot_manifest.jsonl")
    parser.add_argument("--config", default="config/mad_pilot_config.json")
    parser.add_argument("--progress", default="results/mad_pilot_progress.jsonl")
    parser.add_argument("--trajectories", default="results/mad_pilot_trajectories.jsonl")
    parser.add_argument("--events", default="results/mad_pilot_events.jsonl")
    parser.add_argument("--statistics", default="results/mad_pilot_statistics.json")
    parser.add_argument("--key-cases", default="results/mad_pilot_key_cases.md")
    parser.add_argument("--report", default="results/mad_pilot_report.md")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    samples = read_jsonl(ROOT / args.dataset)
    manifest = read_jsonl(ROOT / args.manifest)
    config = load_json(ROOT / args.config)
    progress_map = load_mad_progress(ROOT / args.progress)
    trajectories = build_mad_trajectories(
        samples,
        manifest,
        progress_map,
        config["models"],
        [str(agent_id) for agent_id in config["agents"]],
        [int(round_number) for round_number in config["rounds"]],
    )
    events = flatten_events(trajectories)
    progress_records = list(progress_map.values())
    statistics = build_mad_statistics(manifest, trajectories, progress_records)
    key_cases = build_key_cases_markdown(trajectories)
    report = build_mad_report_markdown(statistics, trajectories)

    write_jsonl(ROOT / args.trajectories, trajectories)
    write_jsonl(ROOT / args.events, events)
    write_json(ROOT / args.statistics, statistics)
    (ROOT / args.key_cases).write_text(key_cases, encoding="utf-8")
    (ROOT / args.report).write_text(report, encoding="utf-8")
    print(
        json.dumps(
            {
                "manifest_items": len(manifest),
                "progress_records": len(progress_records),
                "trajectories": len(trajectories),
                "events": len(events),
                **statistics["run_summary"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
