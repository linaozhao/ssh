"""Statistics report for generated pilot data."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

from mad_attr_filter.semantic_validator import collect_semantic_anomalies, collect_strict_semantic_audit


def _counter_to_sorted_dict(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): counter[key] for key in sorted(counter, key=lambda value: str(value))}


def build_statistics(samples: Sequence[Mapping[str, Any]], generation_report: Mapping[str, Any]) -> dict[str, Any]:
    """Build the pilot_v2_statistics.json payload."""
    scenario_counts: Counter[str] = Counter()
    option_closeness_counts: Counter[str] = Counter()
    structural_complexity_counts: Counter[str] = Counter()
    gold_positions: Counter[str] = Counter()
    constraint_counts: Counter[int] = Counter()
    polarity_counts: Counter[str] = Counter()
    wrong_violation_counts: Counter[int] = Counter()
    attribute_usage: Counter[str] = Counter()
    attribute_required_value_distribution: dict[str, Counter[str]] = defaultdict(Counter)
    exclusion_count_distribution: Counter[int] = Counter()
    per_item_exclusions: dict[str, dict[str, int]] = {}

    for sample in samples:
        scenario_counts[str(sample["scenario"])] += 1
        option_closeness_counts[str(sample["option_closeness"])] += 1
        structural_complexity_counts[str(sample["structural_complexity"])] += 1
        gold_positions[str(sample["gold_answer"])] += 1
        constraints = list(sample["constraints"])
        constraint_counts[len(constraints)] += 1
        for constraint in constraints:
            attribute_key = str(constraint["attribute"])
            required_value_key = "true" if constraint["required_value"] else "false"
            attribute_usage[attribute_key] += 1
            attribute_required_value_distribution[attribute_key][required_value_key] += 1
            polarity_counts["required_true" if constraint["required_value"] else "required_false"] += 1

        matrix = sample["option_constraint_matrix"]
        gold_answer = str(sample["gold_answer"])
        wrong_labels = [label for label in ("A", "B", "C", "D") if label != gold_answer]
        for label in wrong_labels:
            wrong_violation_counts[len(sample["option_violation_signature"][label])] += 1

        item_exclusions: dict[str, int] = {}
        for constraint in constraints:
            constraint_id = str(constraint["id"])
            excluded_count = sum(1 for label in wrong_labels if not matrix[label][constraint_id])
            exclusion_count_distribution[excluded_count] += 1
            item_exclusions[constraint_id] = excluded_count
        per_item_exclusions[str(sample["item_id"])] = item_exclusions

    attempts = int(generation_report.get("attempts", len(samples)))
    validation_pass_rate = len(samples) / attempts if attempts else 0.0
    anomalies = collect_semantic_anomalies(samples)
    strict_audit = collect_strict_semantic_audit(samples)
    return {
        "total_samples": len(samples),
        "scenario_distribution": _counter_to_sorted_dict(scenario_counts),
        "option_closeness_distribution": _counter_to_sorted_dict(option_closeness_counts),
        "structural_complexity_distribution": _counter_to_sorted_dict(structural_complexity_counts),
        "gold_position_distribution": {label: gold_positions[label] for label in ("A", "B", "C", "D")},
        "constraint_count_distribution": _counter_to_sorted_dict(constraint_counts),
        "constraint_polarity_distribution": _counter_to_sorted_dict(polarity_counts),
        "attribute_usage_frequency": _counter_to_sorted_dict(attribute_usage),
        "attribute_required_value_distribution": {
            attribute: _counter_to_sorted_dict(counter)
            for attribute, counter in sorted(attribute_required_value_distribution.items())
        },
        "wrong_option_violation_count_distribution": _counter_to_sorted_dict(wrong_violation_counts),
        "constraint_exclusion_count_distribution": _counter_to_sorted_dict(exclusion_count_distribution),
        "per_item_constraint_exclusion_counts": per_item_exclusions,
        "semantic_validation_failures": int(generation_report.get("semantic_validation_failures", 0)),
        "structural_validation_failures": int(generation_report.get("validation_failures", 0)),
        "invalid_polarity_failures": int(generation_report.get("invalid_polarity_failures", 0)),
        "scenario_compatibility_failures": int(generation_report.get("scenario_compatibility_failures", 0)),
        "generation_report": dict(generation_report),
        "generation_failures": int(generation_report.get("generation_failures", 0)),
        "generation_retries": int(generation_report.get("retries", 0)),
        "validation_pass_rate": validation_pass_rate,
        "forbidden_positive_constraints": anomalies["forbidden_positive_constraints"],
        "forbidden_negative_constraints": anomalies["forbidden_negative_constraints"],
        "scenario_attribute_mismatches": anomalies["scenario_attribute_mismatches"],
        "strict_semantic_audit": strict_audit,
        "forbidden_constraint_count": int(strict_audit["forbidden_requirement_count"]),
        "disabled_attribute_count": int(strict_audit["disabled_attribute_count"]),
        "chinese_character_count": int(strict_audit["chinese_character_count"]),
    }
