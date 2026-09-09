"""Analysis utilities for English single-agent screening outputs."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from mad_attr_filter.attributes import ATTRIBUTE_BY_KEY, NEGATIVE_ONLY_ATTRIBUTES

VALID_OPTIONS = ("A", "B", "C", "D")
MODEL_ALIASES = ("qwen", "llama")


def _safe_mean(values: Sequence[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _valid_answer(record: Mapping[str, Any]) -> str | None:
    answer = record.get("answer")
    return str(answer) if answer in VALID_OPTIONS else None


def _accuracy(records: Sequence[Mapping[str, Any]]) -> float:
    return sum(1 for record in records if record.get("correct") is True) / len(records) if records else 0.0


def _flag_rate(records: Sequence[Mapping[str, Any]], key: str) -> float:
    return sum(1 for record in records if record.get(key) is True) / len(records) if records else 0.0


def _confidence_values(records: Sequence[Mapping[str, Any]]) -> list[float]:
    values: list[float] = []
    for record in records:
        confidence = record.get("confidence")
        if isinstance(confidence, (int, float)):
            values.append(float(confidence))
    return values


def _answer_distribution(records: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counter = Counter(_valid_answer(record) for record in records)
    return {label: counter[label] for label in VALID_OPTIONS} | {"invalid": counter[None]}


def _records_by_item(records: Iterable[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[str(record["item_id"])].append(record)
    return grouped


def _records_by_model(records: Iterable[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[str(record["model_alias"])].append(record)
    return grouped


def _records_by_seed(records: Iterable[Mapping[str, Any]]) -> dict[int, list[Mapping[str, Any]]]:
    grouped: dict[int, list[Mapping[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[int(record["seed"])].append(record)
    return grouped


def _records_by_run_id(records: Iterable[Mapping[str, Any]]) -> dict[int, list[Mapping[str, Any]]]:
    grouped: dict[int, list[Mapping[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[int(record.get("run_id", record.get("seed", 0)))].append(record)
    return grouped


def _has_negative_risk_constraint(sample: Mapping[str, Any]) -> bool:
    return any(str(constraint["attribute"]) in NEGATIVE_ONLY_ATTRIBUTES for constraint in sample["constraints"])


def _signature_key(signature: Sequence[Any]) -> str:
    return "[]" if not signature else ",".join(str(item) for item in signature)


def screening_category(num_correct: int) -> str:
    """Map six independent runs to the screening category."""
    if num_correct == 6:
        return "stable_correct"
    if num_correct == 5:
        return "mildly_vulnerable"
    if 2 <= num_correct <= 4:
        return "mixed_correctness"
    return "mostly_wrong"


def empirical_difficulty(num_correct: int) -> str:
    """Map six independent runs to empirical difficulty labels."""
    if num_correct == 6:
        return "very_easy"
    if num_correct == 5:
        return "easy"
    if 2 <= num_correct <= 4:
        return "medium"
    if num_correct == 1:
        return "hard"
    return "very_hard"


def _model_answer_distribution(records: Sequence[Mapping[str, Any]], model_alias: str) -> dict[str, int]:
    return _answer_distribution([record for record in records if str(record["model_alias"]) == model_alias])


def _has_cross_model_disagreement(records: Sequence[Mapping[str, Any]]) -> bool:
    distributions: list[tuple[int, ...]] = []
    for model_alias in MODEL_ALIASES:
        model_records = [record for record in records if str(record["model_alias"]) == model_alias]
        valid_answers = [_valid_answer(record) for record in model_records if _valid_answer(record) is not None]
        if valid_answers:
            counter = Counter(valid_answers)
            distributions.append(tuple(counter[label] for label in VALID_OPTIONS))
    return len(distributions) >= 2 and len(set(distributions)) > 1


def _has_within_model_disagreement(records: Sequence[Mapping[str, Any]], model_alias: str) -> bool:
    answers = {
        _valid_answer(record)
        for record in records
        if str(record["model_alias"]) == model_alias and _valid_answer(record) is not None
    }
    return len(answers) > 1


def build_item_analysis(
    samples: Sequence[Mapping[str, Any]],
    outputs: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Build per-item analysis records."""
    outputs_by_item = _records_by_item(outputs)
    analyses: list[dict[str, Any]] = []
    for sample in samples:
        item_id = str(sample["item_id"])
        records = outputs_by_item.get(item_id, [])
        answer_counter = Counter(_valid_answer(record) for record in records)
        unique_answers = sorted(label for label in VALID_OPTIONS if answer_counter[label] > 0)
        wrong_records = [
            record for record in records if _valid_answer(record) is not None and record.get("correct") is not True
        ]
        observed_wrong_options = sorted({_valid_answer(record) for record in wrong_records if _valid_answer(record)})
        observed_wrong_violation_signatures: dict[str, list[str]] = {}
        wrong_signature_counts: Counter[str] = Counter()
        for record in wrong_records:
            answer = _valid_answer(record)
            signature = list(record.get("selected_option_violation_signature", []))
            if answer is not None:
                observed_wrong_violation_signatures[answer] = signature
            wrong_signature_counts[_signature_key(signature)] += 1

        qwen_records = [record for record in records if str(record["model_alias"]) == "qwen"]
        llama_records = [record for record in records if str(record["model_alias"]) == "llama"]
        num_runs = len(records)
        num_correct = sum(1 for record in records if record.get("correct") is True)
        has_within_qwen = _has_within_model_disagreement(records, "qwen")
        has_within_llama = _has_within_model_disagreement(records, "llama")
        analysis = {
            "item_id": item_id,
            "num_runs": num_runs,
            "num_correct": num_correct,
            "num_wrong": num_runs - num_correct,
            "empirical_accuracy": _accuracy(records),
            "qwen_correct": sum(1 for record in qwen_records if record.get("correct") is True),
            "qwen_accuracy": _accuracy(qwen_records),
            "llama_correct": sum(1 for record in llama_records if record.get("correct") is True),
            "llama_accuracy": _accuracy(llama_records),
            "answer_distribution": {label: answer_counter[label] for label in VALID_OPTIONS},
            "unique_answers": unique_answers,
            "has_any_disagreement": len(unique_answers) >= 2,
            "has_cross_model_disagreement": _has_cross_model_disagreement(records),
            "has_within_qwen_disagreement": has_within_qwen,
            "has_within_llama_disagreement": has_within_llama,
            "has_within_model_disagreement": has_within_qwen or has_within_llama,
            "qwen_answer_distribution": _model_answer_distribution(records, "qwen"),
            "llama_answer_distribution": _model_answer_distribution(records, "llama"),
            "observed_wrong_options": observed_wrong_options,
            "observed_wrong_answers": observed_wrong_options,
            "observed_wrong_violation_signatures": observed_wrong_violation_signatures,
            "observed_violation_signatures": observed_wrong_violation_signatures,
            "wrong_violation_signatures": dict(sorted(wrong_signature_counts.items())),
            "parse_success_runs": sum(1 for record in records if record.get("parse_success") is True),
            "strict_json_success_runs": sum(1 for record in records if record.get("strict_json_success") is True),
            "fallback_parse_success_runs": sum(1 for record in records if record.get("fallback_parse_success") is True),
            "screening_category": screening_category(num_correct),
            "empirical_difficulty": empirical_difficulty(num_correct),
            "scenario": sample["scenario"],
            "option_closeness": sample["option_closeness"],
            "structural_complexity": sample["structural_complexity"],
            "num_constraints": sample["metadata"]["num_constraints"],
            "gold_answer": sample["gold_answer"],
            "has_negative_risk_constraint": _has_negative_risk_constraint(sample),
        }
        analyses.append(analysis)
    return analyses


def _group_accuracy(
    samples_by_id: Mapping[str, Mapping[str, Any]],
    outputs: Sequence[Mapping[str, Any]],
    field_name: str,
) -> dict[str, dict[str, float | int | None]]:
    groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for output in outputs:
        sample = samples_by_id[str(output["item_id"])]
        if field_name == "model":
            key = str(output["model_alias"])
        elif field_name == "num_constraints":
            key = str(sample["metadata"]["num_constraints"])
        elif field_name == "gold_position":
            key = str(sample["gold_answer"])
        elif field_name == "has_negative_risk_constraint":
            key = str(_has_negative_risk_constraint(sample)).lower()
        else:
            key = str(sample[field_name])
        groups[key].append(output)
    return {
        key: {
            "total_runs": len(records),
            "accuracy": _accuracy(records),
            "parse_success_rate": _flag_rate(records, "parse_success"),
            "strict_json_success_rate": _flag_rate(records, "strict_json_success"),
            "fallback_parse_success_rate": _flag_rate(records, "fallback_parse_success"),
            "mean_confidence": _safe_mean(_confidence_values(records)),
        }
        for key, records in sorted(groups.items())
    }


def build_overall_statistics(outputs: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    """Build per-model overall statistics."""
    model_stats: dict[str, dict[str, Any]] = {}
    for model_alias, records in sorted(_records_by_model(outputs).items()):
        by_seed = {
            str(seed): {
                "runs": len(seed_records),
                "accuracy": _accuracy(seed_records),
                "parse_success_rate": _flag_rate(seed_records, "parse_success"),
            }
            for seed, seed_records in sorted(_records_by_seed(records).items())
        }
        by_run_id = {
            str(run_id): {
                "runs": len(run_records),
                "accuracy": _accuracy(run_records),
                "parse_success_rate": _flag_rate(run_records, "parse_success"),
            }
            for run_id, run_records in sorted(_records_by_run_id(records).items())
        }
        parse_rate = _flag_rate(records, "parse_success")
        model_stats[model_alias] = {
            "total_runs": len(records),
            "accuracy": _accuracy(records),
            "parse_success_rate": parse_rate,
            "strict_json_success_rate": _flag_rate(records, "strict_json_success"),
            "fallback_parse_success_rate": _flag_rate(records, "fallback_parse_success"),
            "total_parse_success_rate": parse_rate,
            "mean_confidence": _safe_mean(_confidence_values(records)),
            "accuracy_by_seed": by_seed,
            "accuracy_by_run_id": by_run_id,
            "answer_distribution": _answer_distribution(records),
            "seed_agreement_rate": _seed_agreement_rate(records),
        }
    return model_stats


def _seed_agreement_rate(records: Sequence[Mapping[str, Any]]) -> float | None:
    item_groups = _records_by_item(records)
    values: list[float] = []
    for item_records in item_groups.values():
        answers = [_valid_answer(record) for record in item_records if _valid_answer(record) is not None]
        if answers:
            values.append(1.0 if len(set(answers)) == 1 else 0.0)
    return _safe_mean(values)


def _expected_keys(
    samples: Sequence[Mapping[str, Any]],
    expected_model_aliases: Sequence[str] | None,
    expected_run_ids: Sequence[int] | None,
    outputs: Sequence[Mapping[str, Any]],
) -> set[tuple[str, str, int]]:
    aliases = list(expected_model_aliases or sorted({str(record["model_alias"]) for record in outputs}))
    run_ids = list(expected_run_ids or sorted({int(record.get("run_id", 0)) for record in outputs}))
    return {
        (str(sample["item_id"]), alias, int(run_id))
        for sample in samples
        for alias in aliases
        for run_id in run_ids
    }


def _predictiveness(grouped_accuracy: Mapping[str, Mapping[str, Any]], order: Sequence[str]) -> dict[str, Any]:
    accuracies = {key: float(grouped_accuracy[key]["accuracy"]) for key in order if key in grouped_accuracy}
    if len(accuracies) < 2:
        return {
            "accuracy_by_level": accuracies,
            "accuracy_span": 0.0,
            "monotonic_expected_order": None,
            "interpretation": "insufficient_data",
        }
    ordered_values = [accuracies[key] for key in order if key in accuracies]
    span = max(ordered_values) - min(ordered_values)
    monotonic = all(left >= right for left, right in zip(ordered_values, ordered_values[1:]))
    if monotonic and span >= 0.05:
        interpretation = "predictive_in_expected_direction"
    elif span < 0.03:
        interpretation = "weak_or_no_observed_relationship"
    else:
        interpretation = "mixed_or_non_monotonic_relationship"
    return {
        "accuracy_by_level": accuracies,
        "accuracy_span": span,
        "monotonic_expected_order": monotonic,
        "interpretation": interpretation,
    }


def _constraint_by_id(sample: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {str(constraint["id"]): constraint for constraint in sample["constraints"]}


def build_constraint_error_statistics(
    samples: Sequence[Mapping[str, Any]],
    outputs: Sequence[Mapping[str, Any]],
    *,
    expected_runs_per_item: int = 6,
) -> dict[str, Any]:
    """Build normalized attribute-level error statistics from wrong selected options."""
    samples_by_id = {str(sample["item_id"]): sample for sample in samples}
    containing_items: Counter[str] = Counter()
    for sample in samples:
        attributes = {str(constraint["attribute"]) for constraint in sample["constraints"]}
        for attribute in attributes:
            containing_items[attribute] += 1

    violation_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    required_value_counts: Counter[str] = Counter()
    wrong_violation_count_distribution: Counter[str] = Counter()
    invalid_wrong_answer_count = 0
    total_wrong_answers = 0

    for output in outputs:
        if output.get("correct") is True:
            continue
        answer = _valid_answer(output)
        if answer is None:
            invalid_wrong_answer_count += 1
            continue
        total_wrong_answers += 1
        signature = [str(item) for item in output.get("selected_option_violation_signature", [])]
        if len(signature) == 1:
            wrong_violation_count_distribution["1_constraint"] += 1
        elif len(signature) == 2:
            wrong_violation_count_distribution["2_constraints"] += 1
        else:
            wrong_violation_count_distribution["3_or_more_constraints"] += 1
        sample = samples_by_id[str(output["item_id"])]
        constraints = _constraint_by_id(sample)
        for constraint_id in signature:
            constraint = constraints[constraint_id]
            attribute_key = str(constraint["attribute"])
            attribute = ATTRIBUTE_BY_KEY[attribute_key]
            violation_counts[attribute_key] += 1
            category_counts[attribute.category] += 1
            required_value_counts["required_true" if constraint["required_value"] is True else "required_false"] += 1

    attribute_rows: list[dict[str, Any]] = []
    for attribute, item_count in sorted(containing_items.items()):
        selected_wrong_count = violation_counts[attribute]
        run_exposure = item_count * expected_runs_per_item
        attribute_rows.append(
            {
                "attribute": attribute,
                "category": ATTRIBUTE_BY_KEY[attribute].category,
                "number_of_times_violated_by_selected_wrong_answer": selected_wrong_count,
                "number_of_items_containing_attribute": item_count,
                "run_exposure": run_exposure,
                "normalized_error_rate": selected_wrong_count / run_exposure if run_exposure else 0.0,
                "error_count_per_containing_item": selected_wrong_count / item_count if item_count else 0.0,
            }
        )
    attribute_rows.sort(
        key=lambda row: (
            -float(row["normalized_error_rate"]),
            -int(row["number_of_times_violated_by_selected_wrong_answer"]),
            str(row["attribute"]),
        )
    )
    single = wrong_violation_count_distribution["1_constraint"]
    multi = wrong_violation_count_distribution["2_constraints"] + wrong_violation_count_distribution["3_or_more_constraints"]
    return {
        "total_wrong_answers": total_wrong_answers,
        "invalid_wrong_answer_count": invalid_wrong_answer_count,
        "wrong_option_violation_count_distribution": dict(sorted(wrong_violation_count_distribution.items())),
        "single_constraint_error_rate": single / total_wrong_answers if total_wrong_answers else 0.0,
        "multi_constraint_error_rate": multi / total_wrong_answers if total_wrong_answers else 0.0,
        "attribute_error_statistics": attribute_rows,
        "most_frequently_missed_attributes": {
            row["attribute"]: row["number_of_times_violated_by_selected_wrong_answer"]
            for row in sorted(attribute_rows, key=lambda r: -int(r["number_of_times_violated_by_selected_wrong_answer"]))[:20]
        },
        "most_vulnerable_attributes_normalized": {
            row["attribute"]: row["normalized_error_rate"] for row in attribute_rows[:20]
        },
        "category_violation_counts": dict(category_counts.most_common()),
        "required_value_violation_counts": dict(required_value_counts.most_common()),
    }


def build_empirical_dataset(
    samples: Sequence[Mapping[str, Any]],
    item_analyses: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Return samples with empirical difficulty and screening category added."""
    analysis_by_id = {str(analysis["item_id"]): analysis for analysis in item_analyses}
    enriched: list[dict[str, Any]] = []
    for sample in samples:
        copied = json.loads(json.dumps(sample, ensure_ascii=False))
        analysis = analysis_by_id[str(sample["item_id"])]
        copied["empirical_difficulty"] = analysis["empirical_difficulty"]
        copied.setdefault("metadata", {})["single_agent_accuracy"] = analysis["empirical_accuracy"]
        copied["metadata"]["single_agent_correct_runs"] = analysis["num_correct"]
        copied["metadata"]["single_agent_total_runs"] = analysis["num_runs"]
        copied["metadata"]["screening_category"] = analysis["screening_category"]
        enriched.append(copied)
    return enriched


def _mad_priority(analysis: Mapping[str, Any]) -> str:
    mixed = int(analysis["num_correct"]) > 0 and int(analysis["num_wrong"]) > 0
    has_multiple_answers = len(analysis["unique_answers"]) >= 2
    has_single_constraint_error = any(
        len(signature) == 1 for signature in analysis["observed_wrong_violation_signatures"].values()
    )
    if mixed and has_multiple_answers and has_single_constraint_error:
        return "high"
    if mixed:
        return "medium"
    return "low"


def select_candidate_items(
    samples: Sequence[Mapping[str, Any]],
    outputs: Sequence[Mapping[str, Any]],
    item_analyses: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Assign every item a MAD priority and preserve controls."""
    del outputs
    sample_by_id = {str(sample["item_id"]): sample for sample in samples}
    candidates: list[dict[str, Any]] = []
    for analysis in item_analyses:
        priority = _mad_priority(analysis)
        reasons: list[str] = [str(analysis["screening_category"])]
        if analysis["has_cross_model_disagreement"]:
            reasons.append("cross_model_disagreement")
        if analysis["has_within_model_disagreement"]:
            reasons.append("within_model_disagreement")
        if any(len(signature) == 1 for signature in analysis["observed_wrong_violation_signatures"].values()):
            reasons.append("single_constraint_error_observed")
        if any(len(signature) >= 2 for signature in analysis["observed_wrong_violation_signatures"].values()):
            reasons.append("multi_constraint_error_observed")
        sample = sample_by_id[str(analysis["item_id"])]
        candidate = dict(sample)
        candidate.update(
            {
                "item_id": analysis["item_id"],
                "empirical_difficulty": analysis["empirical_difficulty"],
                "screening_category": analysis["screening_category"],
                "empirical_accuracy": analysis["empirical_accuracy"],
                "has_cross_model_disagreement": analysis["has_cross_model_disagreement"],
                "has_within_model_disagreement": analysis["has_within_model_disagreement"],
                "has_within_qwen_disagreement": analysis["has_within_qwen_disagreement"],
                "has_within_llama_disagreement": analysis["has_within_llama_disagreement"],
                "observed_wrong_options": analysis["observed_wrong_options"],
                "observed_wrong_violation_signatures": analysis["observed_wrong_violation_signatures"],
                "mad_priority": priority,
                "selection_reason": reasons,
                "num_correct": analysis["num_correct"],
                "num_wrong": analysis["num_wrong"],
                "num_runs": analysis["num_runs"],
                "scenario": sample["scenario"],
                "option_closeness": sample["option_closeness"],
                "structural_complexity": sample["structural_complexity"],
                "num_constraints": sample["metadata"]["num_constraints"],
                "gold_answer": sample["gold_answer"],
            }
        )
        candidates.append(candidate)
    return candidates


def build_statistics_payload(
    samples: Sequence[Mapping[str, Any]],
    outputs: Sequence[Mapping[str, Any]],
    item_analyses: Sequence[Mapping[str, Any]],
    candidate_items: Sequence[Mapping[str, Any]],
    constraint_error_statistics: Mapping[str, Any],
    *,
    expected_model_aliases: Sequence[str] | None = None,
    expected_run_ids: Sequence[int] | None = None,
) -> dict[str, Any]:
    """Build the single-agent statistics JSON."""
    samples_by_id = {str(sample["item_id"]): sample for sample in samples}
    expected = _expected_keys(samples, expected_model_aliases, expected_run_ids, outputs)
    observed = {
        (str(record["item_id"]), str(record["model_alias"]), int(record.get("run_id", record.get("seed", 0))))
        for record in outputs
    }
    grouped_accuracy = {
        "model": _group_accuracy(samples_by_id, outputs, "model"),
        "scenario": _group_accuracy(samples_by_id, outputs, "scenario"),
        "option_closeness": _group_accuracy(samples_by_id, outputs, "option_closeness"),
        "structural_complexity": _group_accuracy(samples_by_id, outputs, "structural_complexity"),
        "num_constraints": _group_accuracy(samples_by_id, outputs, "num_constraints"),
        "gold_position": _group_accuracy(samples_by_id, outputs, "gold_position"),
        "has_negative_risk_constraint": _group_accuracy(samples_by_id, outputs, "has_negative_risk_constraint"),
    }
    category_counts = Counter(str(analysis["screening_category"]) for analysis in item_analyses)
    priority_counts = Counter(str(item["mad_priority"]) for item in candidate_items)
    item_summary = {
        "items": len(item_analyses),
        "stable_correct": category_counts["stable_correct"],
        "mildly_vulnerable": category_counts["mildly_vulnerable"],
        "mixed_correctness": category_counts["mixed_correctness"],
        "mostly_wrong": category_counts["mostly_wrong"],
        "items_with_any_disagreement": sum(1 for analysis in item_analyses if analysis["has_any_disagreement"]),
        "items_with_cross_model_disagreement": sum(
            1 for analysis in item_analyses if analysis["has_cross_model_disagreement"]
        ),
        "items_with_qwen_internal_disagreement": sum(
            1 for analysis in item_analyses if analysis["has_within_qwen_disagreement"]
        ),
        "items_with_llama_internal_disagreement": sum(
            1 for analysis in item_analyses if analysis["has_within_llama_disagreement"]
        ),
    }
    api_failures = sum(1 for record in outputs if record.get("metadata", {}).get("request_error"))
    parse_failures = sum(1 for record in outputs if record.get("parse_success") is not True)
    overall = {
        "dataset_items": len(samples),
        "expected_runs": len(expected),
        "completed_runs": len(outputs),
        "attempted_runs": len(outputs),
        "unique_run_keys": len(observed),
        "duplicate_run_count": max(0, len(outputs) - len(observed)),
        "missing_run_count": len(expected - observed),
        "api_failures": api_failures,
        "parse_failures": parse_failures,
        "valid_runs": sum(
            1 for record in outputs if record.get("parse_success") is True and _valid_answer(record) is not None
        ),
        "combined_accuracy": _accuracy(outputs),
        "strict_json_success_rate": _flag_rate(outputs, "strict_json_success"),
        "fallback_parse_success_rate": _flag_rate(outputs, "fallback_parse_success"),
        "total_parse_success_rate": _flag_rate(outputs, "parse_success"),
        "combined_parse_success_rate": _flag_rate(outputs, "parse_success"),
        "combined_mean_confidence": _safe_mean(_confidence_values(outputs)),
        "all_successful_runs_have_valid_option": all(
            _valid_answer(record) is not None for record in outputs if record.get("parse_success") is True
        ),
    }
    return {
        "overall": overall,
        "overall_by_model": build_overall_statistics(outputs),
        "grouped_accuracy": grouped_accuracy,
        "group_accuracy": grouped_accuracy,
        "predictiveness": {
            "option_closeness": _predictiveness(grouped_accuracy["option_closeness"], ("easy", "medium", "hard")),
            "structural_complexity": _predictiveness(
                grouped_accuracy["structural_complexity"],
                ("low", "medium", "high"),
            ),
            "num_constraints": _predictiveness(grouped_accuracy["num_constraints"], ("3", "4", "5")),
        },
        "screening_category_distribution": dict(category_counts),
        "item_level_summary": item_summary,
        "mad_priority_distribution": dict(priority_counts),
        "constraint_error_statistics": constraint_error_statistics,
        "reasoning_diagnostics": _reasoning_diagnostics_summary(outputs),
    }


def _reasoning_diagnostics_summary(outputs: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    diagnostics = [
        record.get("reasoning_diagnostics", {})
        for record in outputs
        if isinstance(record.get("reasoning_diagnostics"), dict)
    ]
    return {
        "mean_reasoning_word_count": _safe_mean(
            [
                float(diag.get("word_count", 0))
                for diag in diagnostics
                if isinstance(diag.get("word_count"), (int, float))
            ]
        ),
        "mentions_all_candidate_labels_rate": _safe_mean(
            [1.0 if diag.get("mentions_all_candidate_labels") else 0.0 for diag in diagnostics]
        ),
        "mentions_selected_option_rate": _safe_mean(
            [1.0 if diag.get("mentions_selected_option") else 0.0 for diag in diagnostics]
        ),
    }


def write_jsonl(path: str | Path, records: Sequence[Mapping[str, Any]]) -> None:
    """Write JSONL records."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            file.write("\n")


def _format_rate(value: float | None) -> str:
    return "NA" if value is None else f"{value:.3f}"


def _format_json(data: Any) -> str:
    return "```json\n" + json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n```"


def _report_result(statistics: Mapping[str, Any]) -> tuple[str, str]:
    overall = statistics["overall"]
    summary = statistics["item_level_summary"]
    wrong_stats = statistics["constraint_error_statistics"]
    combined_accuracy = float(overall["combined_accuracy"])
    stable_ratio = int(summary["stable_correct"]) / max(1, int(summary["items"]))
    mixed_or_mild = int(summary["mildly_vulnerable"]) + int(summary["mixed_correctness"])
    disagreement = int(summary["items_with_any_disagreement"])
    single_constraint_rate = float(wrong_stats["single_constraint_error_rate"])
    if combined_accuracy < 0.50 or int(summary["mostly_wrong"]) >= 50:
        return (
            "RESULT: TASK TOO DIFFICULT FOR CLEAN DRIFT ANALYSIS",
            "The models show insufficient base solving ability, so later interaction failures would be hard to attribute cleanly to debate.",
        )
    if stable_ratio >= 0.85 and mixed_or_mild < 10 and disagreement < 10:
        return (
            "RESULT: TASK TOO EASY FOR PRIMARY MAD DIAGNOSIS",
            "The dataset is useful as a stable-control pool, but primary drift diagnosis needs additional difficulty mechanisms.",
        )
    if mixed_or_mild >= 10 and disagreement >= 10 and single_constraint_rate >= 0.50:
        return (
            "RESULT: SUITABLE FOR BASELINE MAD PILOT",
            "The data show base competence plus natural instability, and many mistakes are single-constraint violations.",
        )
    if combined_accuracy >= 0.95 and disagreement < 10:
        return (
            "RESULT: TASK TOO EASY FOR PRIMARY MAD DIAGNOSIS",
            "The overall accuracy is very high and natural disagreement is limited.",
        )
    return (
        "RESULT: SUITABLE FOR BASELINE MAD PILOT",
        "The pilot has enough non-stable behavior to justify a small baseline MAD trial, while preserving stable controls.",
    )


def build_report_markdown(
    statistics: Mapping[str, Any],
    item_analyses: Sequence[Mapping[str, Any]],
    candidate_items: Sequence[Mapping[str, Any]],
) -> str:
    """Build the final screening report."""
    del item_analyses
    overall = statistics["overall"]
    by_model = statistics["overall_by_model"]
    summary = statistics["item_level_summary"]
    constraint_stats = statistics["constraint_error_statistics"]
    prediction = statistics["predictiveness"]
    priority = statistics["mad_priority_distribution"]
    result_line, result_reason = _report_result(statistics)
    qwen = by_model.get("qwen", {})
    llama = by_model.get("llama", {})
    top_raw = constraint_stats["most_frequently_missed_attributes"]
    top_norm = constraint_stats["most_vulnerable_attributes_normalized"]
    high_priority = sum(1 for item in candidate_items if item["mad_priority"] == "high")
    medium_priority = sum(1 for item in candidate_items if item["mad_priority"] == "medium")
    mixed_plus_mild = int(summary["mildly_vulnerable"]) + int(summary["mixed_correctness"])
    single_errors = constraint_stats["wrong_option_violation_count_distribution"].get("1_constraint", 0)

    return "\n".join(
        [
            "# Single-Agent Screening Report",
            "",
            "## Run Summary",
            _format_json(overall),
            "",
            "## Dataset Difficulty",
            f"1. Qwen overall accuracy: `{_format_rate(qwen.get('accuracy'))}`.",
            f"2. Llama overall accuracy: `{_format_rate(llama.get('accuracy'))}`.",
            f"3. Combined accuracy: `{_format_rate(overall.get('combined_accuracy'))}`.",
            f"4. `stable_correct`: `{summary['stable_correct']}`.",
            f"5. `mildly_vulnerable`: `{summary['mildly_vulnerable']}`.",
            f"6. `mixed_correctness`: `{summary['mixed_correctness']}`.",
            f"7. `mostly_wrong`: `{summary['mostly_wrong']}`.",
            "",
            "## Natural Disagreement",
            f"8. Items with any natural disagreement: `{summary['items_with_any_disagreement']}`.",
            f"9. Items with cross-model disagreement: `{summary['items_with_cross_model_disagreement']}`.",
            f"10. Items with Qwen internal disagreement: `{summary['items_with_qwen_internal_disagreement']}`.",
            f"11. Items with Llama internal disagreement: `{summary['items_with_llama_internal_disagreement']}`.",
            "",
            "## Diagnostic Value",
            f"12. Total wrong answers: `{constraint_stats['total_wrong_answers']}`.",
            (
                "13. Share of wrong answers violating exactly one constraint: "
                f"`{_format_rate(constraint_stats['single_constraint_error_rate'])}`."
            ),
            "14. Most frequent raw attributes for wrong answers:",
            _format_json(top_raw),
            "15. Most vulnerable normalized attributes:",
            _format_json(top_norm),
            "16. Constraint type/category error summary:",
            _format_json(
                {
                    "category_violation_counts": constraint_stats["category_violation_counts"],
                    "required_value_violation_counts": constraint_stats["required_value_violation_counts"],
                }
            ),
            "",
            "## Difficulty Design",
            (
                "17. option_closeness accuracy relationship: "
                f"`{prediction['option_closeness']['interpretation']}`."
            ),
            _format_json(prediction["option_closeness"]),
            (
                "18. 3/4/5 constraint accuracy relationship: "
                f"`{prediction['num_constraints']['interpretation']}`."
            ),
            _format_json(prediction["num_constraints"]),
            (
                "19. structural_complexity relationship with empirical difficulty: "
                f"`{prediction['structural_complexity']['interpretation']}`."
            ),
            _format_json(prediction["structural_complexity"]),
            (
                "20. Current generator difficulty validity: "
                "treat as useful only if the grouped relationships above are monotonic and the span is non-trivial; "
                "otherwise it should be considered structural metadata rather than empirical difficulty."
            ),
            "",
            "## Suitability For MAD",
            f"21. High-priority MAD candidates: `{high_priority}`.",
            f"22. Medium-priority MAD candidates: `{medium_priority}`.",
            f"23. Items with correct + wrong coexistence: `{mixed_plus_mild}`.",
            f"24. Single-constraint wrong answers observed: `{single_errors}`.",
            f"25. Current recommendation: {result_reason}",
            "",
            "## Model-Level Statistics",
            _format_json(by_model),
            "",
            "## Grouped Accuracy",
            _format_json(statistics["grouped_accuracy"]),
            "",
            "## Screening Category Distribution",
            _format_json(statistics["screening_category_distribution"]),
            "",
            "## MAD Priority Distribution",
            _format_json(priority),
            "",
            "## Final Result",
            result_line,
        ]
    )


def build_examples_markdown(
    samples: Sequence[Mapping[str, Any]],
    outputs: Sequence[Mapping[str, Any]],
    item_analyses: Sequence[Mapping[str, Any]],
    candidate_items: Sequence[Mapping[str, Any]],
) -> str:
    """Build a manual inspection file with representative screening examples."""
    sample_by_id = {str(sample["item_id"]): sample for sample in samples}
    outputs_by_item = _records_by_item(outputs)
    candidate_by_id = {str(candidate["item_id"]): candidate for candidate in candidate_items}
    targets = {
        "stable_correct": 5,
        "mildly_vulnerable": 5,
        "mixed_correctness": 10,
        "mostly_wrong": 5,
    }
    selected: list[Mapping[str, Any]] = []
    for category, limit in targets.items():
        category_items = [analysis for analysis in item_analyses if analysis["screening_category"] == category]
        selected.extend(category_items[:limit])

    lines = [
        "# Single-Agent Screening Examples",
        "",
        "Representative items for manual inspection. Reasoning text is copied from model outputs without automatic judging.",
        "",
    ]
    for analysis in selected:
        item_id = str(analysis["item_id"])
        sample = sample_by_id[item_id]
        candidate = candidate_by_id[item_id]
        lines.extend(
            [
                f"## {item_id}",
                "",
                f"- screening_category: `{analysis['screening_category']}`",
                f"- MAD priority: `{candidate['mad_priority']}`",
                f"- Gold: `{sample['gold_answer']}`",
                f"- empirical_accuracy: `{analysis['empirical_accuracy']:.4f}`",
                "",
                "### Question",
                "",
                str(sample["question"]),
                "",
                "### Six Runs",
                "",
            ]
        )
        for record in sorted(outputs_by_item.get(item_id, []), key=lambda r: (str(r["model_alias"]), int(r["run_id"]))):
            answer = record.get("answer")
            signature = record.get("selected_option_violation_signature", [])
            lines.extend(
                [
                    (
                        f"- `{record['model_alias']}` run `{record.get('run_id')}` seed `{record.get('seed')}`: "
                        f"answer=`{answer}`, correct=`{record.get('correct')}`, "
                        f"confidence=`{record.get('confidence')}`, violation=`{signature}`"
                    ),
                    f"  reasoning: {record.get('reasoning', '')}",
                ]
            )
        lines.extend(
            [
                "",
                f"Qwen answers: `{analysis['qwen_answer_distribution']}`",
                f"Llama answers: `{analysis['llama_answer_distribution']}`",
                f"Observed wrong options: `{analysis['observed_wrong_options']}`",
                f"Observed wrong violation signatures: `{analysis['observed_wrong_violation_signatures']}`",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"
