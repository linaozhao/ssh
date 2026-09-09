#!/usr/bin/env python3
"""Analyze single-agent outputs and produce screening artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mad_attr_filter.io import load_json, read_jsonl, write_json, write_jsonl
from mad_attr_filter.single_agent import model_alias
from mad_attr_filter.single_agent_analysis import (
    build_constraint_error_statistics,
    build_empirical_dataset,
    build_examples_markdown,
    build_item_analysis,
    build_report_markdown,
    build_statistics_payload,
    select_candidate_items,
    write_jsonl as write_analysis_jsonl,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze English pilot v3 single-agent outputs.")
    parser.add_argument("--dataset", default="data/pilot_en_v3.jsonl")
    parser.add_argument("--outputs", default="results/single_agent_outputs.jsonl")
    parser.add_argument("--config", default="config/single_agent_config.json")
    parser.add_argument("--statistics", default="results/single_agent_statistics.json")
    parser.add_argument("--item-analysis", default="results/single_agent_item_analysis.jsonl")
    parser.add_argument("--constraint-error-statistics", default="results/constraint_error_statistics.json")
    parser.add_argument("--candidate-items", default="results/mad_candidate_items.jsonl")
    parser.add_argument("--examples", default="results/single_agent_examples.md")
    parser.add_argument("--report", default="results/single_agent_report.md")
    parser.add_argument("--empirical-output", default="data/pilot_en_v3_with_empirical_difficulty.jsonl")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    samples = read_jsonl(ROOT / args.dataset)
    outputs = read_jsonl(ROOT / args.outputs)
    config = load_json(ROOT / args.config)
    expected_model_aliases = [model_alias(model_config) for model_config in config["models"]]
    expected_run_ids = list(range(1, len(config["seeds"]) + 1))
    item_analysis = build_item_analysis(samples, outputs)
    candidate_items = select_candidate_items(samples, outputs, item_analysis)
    constraint_error_statistics = build_constraint_error_statistics(
        samples,
        outputs,
        expected_runs_per_item=len(config["models"]) * len(config["seeds"]),
    )
    statistics = build_statistics_payload(
        samples,
        outputs,
        item_analysis,
        candidate_items,
        constraint_error_statistics,
        expected_model_aliases=expected_model_aliases,
        expected_run_ids=expected_run_ids,
    )
    empirical_dataset = build_empirical_dataset(samples, item_analysis)
    report = build_report_markdown(statistics, item_analysis, candidate_items)
    examples = build_examples_markdown(samples, outputs, item_analysis, candidate_items)

    write_json(ROOT / args.statistics, statistics)
    write_json(ROOT / args.constraint_error_statistics, constraint_error_statistics)
    write_analysis_jsonl(ROOT / args.item_analysis, item_analysis)
    write_analysis_jsonl(ROOT / args.candidate_items, candidate_items)
    write_jsonl(ROOT / args.empirical_output, empirical_dataset)
    examples_path = ROOT / args.examples
    examples_path.parent.mkdir(parents=True, exist_ok=True)
    examples_path.write_text(examples, encoding="utf-8")
    report_path = ROOT / args.report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report + "\n", encoding="utf-8")

    print(json.dumps({
        "outputs": len(outputs),
        "items": len(item_analysis),
        "candidate_items": len(candidate_items),
        "expected_runs": statistics["overall"]["expected_runs"],
        "missing_run_count": statistics["overall"]["missing_run_count"],
        "total_parse_success_rate": statistics["overall"]["total_parse_success_rate"],
        "statistics": args.statistics,
        "constraint_error_statistics": args.constraint_error_statistics,
        "examples": args.examples,
        "report": args.report,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
