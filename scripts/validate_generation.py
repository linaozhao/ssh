#!/usr/bin/env python3
"""Generate temporary samples and validate structure plus strict semantics."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mad_attr_filter.generator import generate_dataset
from mad_attr_filter.matrix import compute_constraint_matrix, compute_violation_signatures
from mad_attr_filter.semantic_validator import collect_strict_semantic_audit, validate_semantics
from mad_attr_filter.validation import ValidationError, validate_dataset, validate_sample


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stress-test deterministic attribute-filter generation.")
    parser.add_argument("--num-items", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--strict-semantic", action="store_true")
    return parser.parse_args()


def _ratio_counts(total: int, ratios: dict[str, int]) -> dict[str, int]:
    ratio_sum = sum(ratios.values())
    counts = {key: total * value // ratio_sum for key, value in ratios.items()}
    remainder = total - sum(counts.values())
    order = sorted(ratios, key=lambda key: (-ratios[key], key))
    for key in order[:remainder]:
        counts[key] += 1
    return counts


def main() -> int:
    args = parse_args()
    option_closeness_counts = _ratio_counts(args.num_items, {"easy": 20, "medium": 60, "hard": 20})
    constraint_count_counts = {
        int(key): value for key, value in _ratio_counts(args.num_items, {"3": 40, "4": 40, "5": 20}).items()
    }
    scenario_counts = _ratio_counts(
        args.num_items,
        {"expert_recruitment": 34, "project_assignment": 33, "availability_selection": 33},
    )
    samples, report = generate_dataset(
        option_closeness_counts,
        global_seed=args.seed,
        constraint_count_counts=constraint_count_counts,
        scenario_counts=scenario_counts,
    )

    structure_errors = 0
    semantic_errors = 0
    unique_gold_violations = 0
    violation_signature_errors = 0
    for sample in samples:
        try:
            validate_sample(sample)
        except ValidationError:
            structure_errors += 1
        valid_labels = [label for label, signature in sample["option_violation_signature"].items() if not signature]
        if len(valid_labels) != 1:
            unique_gold_violations += 1
        candidate_attributes = {label: entity["attributes"] for label, entity in sample["entities"].items()}
        constraints = [
            type("ConstraintLike", (), constraint)()
            for constraint in sample["constraints"]
        ]
        matrix = compute_constraint_matrix(candidate_attributes, constraints)
        signatures = compute_violation_signatures(matrix)
        if signatures != sample["option_violation_signature"]:
            violation_signature_errors += 1
        if args.strict_semantic:
            try:
                validate_semantics(sample)
            except Exception:
                semantic_errors += 1
    try:
        validate_dataset(samples)
    except ValidationError:
        structure_errors += 1

    audit = collect_strict_semantic_audit(samples)
    forbidden_combinations = (
        int(audit["forbidden_requirement_count"])
        + int(audit["disabled_attribute_count"])
        + int(audit["negative_availability_count"])
        + int(audit["negative_preference_count"])
    )

    print(f"samples = {len(samples)}")
    print(f"generated_items = {report.generated_items}")
    print(f"unique Gold violations = {unique_gold_violations}")
    print(f"violation-signature errors = {violation_signature_errors}")
    print(f"structural errors = {structure_errors}")
    print(f"semantic errors = {semantic_errors + int(audit['semantic_error_count'])}")
    print(f"English-realization errors = {semantic_errors + int(audit['semantic_error_count'])}")
    print(f"forbidden polarity errors = {forbidden_combinations}")
    print(f"Chinese-character errors = {audit['chinese_character_count']}")
    print(f"结构错误 = {structure_errors}")
    print(f"语义错误 = {semantic_errors + int(audit['semantic_error_count'])}")
    print(f"禁止属性组合 = {forbidden_combinations}")
    print(f"forbidden_requirement_count = {audit['forbidden_requirement_count']}")
    print(f"disabled_attribute_count = {audit['disabled_attribute_count']}")
    print(f"negative_availability_count = {audit['negative_availability_count']}")
    print(f"negative_preference_count = {audit['negative_preference_count']}")
    print(f"semantic_validation_pass_rate = {audit['semantic_validation_pass_rate']}")

    if (
        structure_errors
        or semantic_errors
        or forbidden_combinations
        or int(audit["semantic_error_count"])
        or unique_gold_violations
        or violation_signature_errors
        or int(audit["chinese_character_count"])
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
