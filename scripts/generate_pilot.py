#!/usr/bin/env python3
"""Generate the English-first stage-3A pilot dataset."""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mad_attr_filter.generator import (
    default_pilot_constraint_counts,
    default_pilot_counts,
    default_pilot_scenario_counts,
    generate_dataset,
)
from mad_attr_filter.io import load_json, write_json, write_jsonl
from mad_attr_filter.lexical_audit import build_lexical_audit
from mad_attr_filter.reports import write_examples_report, write_semantic_audit_report
from mad_attr_filter.statistics import build_statistics
from mad_attr_filter.validation import validate_dataset


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate deterministic English MAD attribute-filter pilot v3 data.")
    parser.add_argument("--config", default="config/default_config.json", help="Path to generation config JSON.")
    parser.add_argument("--output", default=None, help="Override JSONL output path.")
    parser.add_argument("--stats-output", default=None, help="Override statistics JSON output path.")
    parser.add_argument("--statistics", default=None, help="Deprecated alias for --stats-output.")
    parser.add_argument("--examples-output", default=None, help="Override examples markdown output path.")
    parser.add_argument("--audit-output", default=None, help="Override semantic audit markdown output path.")
    parser.add_argument("--lexical-output", default=None, help="Override lexical audit JSON output path.")
    parser.add_argument("--num-items", type=int, default=None, help="Number of samples to generate.")
    parser.add_argument("--seed", type=int, default=None, help="Global random seed.")
    return parser.parse_args()


def _ratio_counts(total: int, ratios: dict[str, int]) -> dict[str, int]:
    ratio_sum = sum(ratios.values())
    counts = {key: total * value // ratio_sum for key, value in ratios.items()}
    remainder = total - sum(counts.values())
    order = sorted(ratios, key=lambda key: (-ratios[key], key))
    for key in order[:remainder]:
        counts[key] += 1
    return counts


def _int_key_counts(raw_counts: dict[str, int]) -> dict[int, int]:
    return {int(key): int(value) for key, value in raw_counts.items()}


def _resolve_counts(config: dict[str, object], num_items: int) -> tuple[dict[str, int], dict[int, int], dict[str, int]]:
    if num_items == 100:
        return default_pilot_counts(), default_pilot_constraint_counts(), default_pilot_scenario_counts()
    closeness_counts = _ratio_counts(num_items, {"easy": 20, "medium": 60, "hard": 20})
    constraint_counts = {int(key): value for key, value in _ratio_counts(num_items, {"3": 40, "4": 40, "5": 20}).items()}
    scenario_counts = _ratio_counts(
        num_items,
        {"expert_recruitment": 34, "project_assignment": 33, "availability_selection": 33},
    )
    return closeness_counts, constraint_counts, scenario_counts


def main() -> int:
    args = parse_args()
    config = load_json(ROOT / args.config)
    seed = int(args.seed if args.seed is not None else config["global_seed"])
    num_items = int(args.num_items if args.num_items is not None else config["num_items"])
    output_path = ROOT / (args.output or str(config["output_jsonl"]))
    stats_arg = args.stats_output or args.statistics
    statistics_path = ROOT / (stats_arg or str(config["statistics_path"]))
    examples_path = ROOT / (args.examples_output or f"{output_path.with_suffix('').as_posix()}_examples.md")
    audit_path = ROOT / (args.audit_output or f"{output_path.with_suffix('').as_posix()}_semantic_audit.md")
    lexical_path = ROOT / (args.lexical_output or f"{output_path.with_suffix('').as_posix()}_lexical_audit.json")

    option_closeness_counts, constraint_count_counts, scenario_counts = _resolve_counts(config, num_items)
    samples, report = generate_dataset(
        option_closeness_counts,
        global_seed=seed,
        max_retries_per_item=int(config["max_retries_per_item"]),
        balanced_gold=True,
        constraint_count_counts=constraint_count_counts,
        scenario_counts=scenario_counts,
    )
    validate_dataset(samples, enforce_pilot_gold_balance=True)
    write_jsonl(output_path, samples)
    statistics = build_statistics(samples, report.to_dict())
    write_json(statistics_path, statistics)
    write_examples_report(examples_path, samples, seed=seed)
    write_semantic_audit_report(audit_path, samples)
    write_json(lexical_path, build_lexical_audit(samples))

    print(f"Wrote {len(samples)} samples to {output_path.relative_to(ROOT)}")
    print(f"Wrote statistics to {statistics_path.relative_to(ROOT)}")
    print(f"Wrote examples to {examples_path.relative_to(ROOT)}")
    print(f"Wrote semantic audit to {audit_path.relative_to(ROOT)}")
    print(f"Wrote lexical audit to {lexical_path.relative_to(ROOT)}")
    print(f"Gold distribution: {statistics['gold_position_distribution']}")
    print(f"Scenario distribution: {statistics['scenario_distribution']}")
    print("Random sample preview:")
    preview_rng = random.Random(seed)
    for sample in preview_rng.sample(samples, min(3, len(samples))):
        print(
            f"- {sample['item_id']} [{sample['scenario']} / {sample['option_closeness']} / "
            f"{sample['structural_complexity']}] gold={sample['gold_answer']}"
        )
        print(f"  {sample['question'].splitlines()[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
