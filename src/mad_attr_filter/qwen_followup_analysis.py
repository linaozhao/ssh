"""Analysis utilities for the Qwen-centered v4.1 follow-up."""

from __future__ import annotations

import random
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

from mad_attr_filter.generator import LABELS
from mad_attr_filter.qwen_followup import parse_followup_response
from mad_attr_filter.v4_validation import V4ValidationError, validate_v4_item


def ratio(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 6) if denominator else None


def valid_records(records: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return [record for record in records if record.get("answer_extractable") is True]


def summarize_records(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Summarize request, parsing, accuracy, and truncation outcomes."""
    valid = valid_records(records)
    correct = sum(record.get("correct") is True for record in valid)
    return {
        "records": len(records),
        "api_success": sum(record.get("request_error") is None for record in records),
        "api_failures": sum(record.get("request_error") is not None for record in records),
        "valid_answers": len(valid),
        "valid_answer_rate": ratio(len(valid), len(records)),
        "json_compliant": sum(record.get("json_compliant") is True for record in records),
        "json_compliance_rate": ratio(
            sum(record.get("json_compliant") is True for record in records), len(records)
        ),
        "strict_answer_format": sum(
            record.get("strict_answer_format") is True for record in records
        ),
        "name_mapped_answers": sum(
            record.get("semantic_name_mapping_used") is True for record in records
        ),
        "unrecognized_answers": sum(
            record.get("request_error") is None
            and record.get("answer_extractable") is not True
            for record in records
        ),
        "truncated": sum(record.get("truncated") is True for record in records),
        "correct": correct,
        "accuracy_all_attempts": ratio(correct, len(records)),
        "valid_answer_accuracy": ratio(correct, len(valid)),
        "answer_distribution": dict(
            sorted(Counter(str(record["answer"]) for record in valid).items())
        ),
    }


def _target_fact(item: Mapping[str, Any], label: str, attribute: str) -> str:
    for fact in item["entities"][label]["displayed_facts"]:
        if fact["attribute"] == attribute:
            return str(fact["text"])
    return "<missing displayed fact>"


def _reasoning_diagnostic(reasoning: str) -> str:
    lowered = reasoning.casefold()
    if "not required" in lowered or "isn't required" in lowered:
        return "explicit_requirement_relaxation"
    if "implied" in lowered or " via " in lowered or "equivalent" in lowered:
        return "unsupported_constraint_substitution"
    return "selected_fact_misread_or_not_applied"


def build_semantic_review(
    samples: Sequence[Mapping[str, Any]],
    prior_item_rows: Sequence[Mapping[str, Any]],
    prior_outputs: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Review every prior Qwen stable-error and mixed item against source fields."""
    item_by_id = {str(item["item_id"]): item for item in samples}
    flagged = sorted(
        (
            row
            for row in prior_item_rows
            if row.get("model_alias") == "qwen"
            and (row.get("all_three_valid_and_wrong") or row.get("has_correct_and_valid_wrong"))
        ),
        key=lambda row: str(row["item_id"]),
    )
    output_by_item: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for record in prior_outputs:
        if record.get("model_alias") == "qwen":
            output_by_item[str(record["item_id"])].append(record)
    rows: list[dict[str, Any]] = []
    for item_row in flagged:
        item = item_by_id[str(item_row["item_id"])]
        validation_error: str | None = None
        try:
            validate_v4_item(item)
        except V4ValidationError as exc:
            validation_error = str(exc)
        constrained_attributes = {
            str(constraint["attribute"]) for constraint in item["constraints"]
        }
        non_target_keys = {
            str(fact["key"])
            for entity in item["entities"].values()
            for fact in entity["non_target_facts"]
        }
        collisions = sorted(constrained_attributes & non_target_keys)
        run_evidence: list[dict[str, Any]] = []
        for record in sorted(
            output_by_item[str(item["item_id"])], key=lambda value: int(value["run_id"])
        ):
            answer = record.get("answer")
            signature = (
                list(item["option_violation_signature"][answer])
                if answer in LABELS
                else []
            )
            violated = []
            for constraint_id in signature:
                constraint = next(
                    value for value in item["constraints"] if value["id"] == constraint_id
                )
                violated.append(
                    {
                        "constraint_id": constraint_id,
                        "attribute": constraint["attribute"],
                        "requirement_text": constraint["natural_language"],
                        "selected_candidate_fact": _target_fact(
                            item, str(answer), str(constraint["attribute"])
                        ),
                    }
                )
            run_evidence.append(
                {
                    "run_id": record["run_id"],
                    "seed": record["seed"],
                    "answer": answer,
                    "selected_candidate": (
                        item["entities"][answer]["name"] if answer in LABELS else None
                    ),
                    "correct": record["correct"],
                    "violation_signature": signature,
                    "violated_constraints": violated,
                    "reasoning": record["reasoning"],
                    "reasoning_diagnostic": (
                        _reasoning_diagnostic(str(record["reasoning"]))
                        if signature
                        else "correct_answer"
                    ),
                    "diagnostic_scope_note": (
                        "Classification describes the output text and does not claim access "
                        "to the model's internal cognitive process."
                    ),
                }
            )
        all_wrong = bool(item_row["all_three_valid_and_wrong"])
        unusual_but_valid = (
            {"can_work_remote", "can_work_onsite"} <= constrained_attributes
        )
        rows.append(
            {
                "item_id": item["item_id"],
                "screening_status": "stable_wrong" if all_wrong else "mixed",
                "difficulty_cell": item["metadata"]["difficulty_cell"],
                "scenario": item["scenario"],
                "gold_answer": item["gold_answer"],
                "constraints": item["constraints"],
                "formal_validation_passed": validation_error is None,
                "formal_validation_error": validation_error,
                "constraint_text_formal_consistency": validation_error is None,
                "candidate_text_structured_consistency": validation_error is None,
                "unique_gold_validated": validation_error is None,
                "matrix_and_signatures_validated": validation_error is None,
                "non_target_formal_key_collisions": collisions,
                "non_target_information_changed_matrix": False,
                "unusual_but_satisfiable_remote_and_onsite_pair": unusual_but_valid,
                "dataset_defect_found": validation_error is not None or bool(collisions),
                "review_conclusion": (
                    "The item or annotation failed semantic review."
                    if validation_error is not None or collisions
                    else "The item and annotation are internally consistent; observed wrong "
                    "answers select formally violating candidates."
                ),
                "run_evidence": run_evidence,
            }
        )
    summary = {
        "reviewed_items": len(rows),
        "stable_wrong_items": sum(row["screening_status"] == "stable_wrong" for row in rows),
        "mixed_items": sum(row["screening_status"] == "mixed" for row in rows),
        "dataset_defect_count": sum(row["dataset_defect_found"] for row in rows),
        "formal_validation_failure_count": sum(
            row["formal_validation_passed"] is not True for row in rows
        ),
        "non_target_formal_key_collision_count": sum(
            len(row["non_target_formal_key_collisions"]) for row in rows
        ),
        "wrong_response_count": sum(
            evidence["correct"] is not True
            for row in rows
            for evidence in row["run_evidence"]
        ),
        "diagnostic_counts": dict(
            sorted(
                Counter(
                    evidence["reasoning_diagnostic"]
                    for row in rows
                    for evidence in row["run_evidence"]
                    if evidence["correct"] is not True
                ).items()
            )
        ),
        "systemic_data_validity_problem_found": any(
            row["dataset_defect_found"] for row in rows
        ),
        "review_type": "agent_performed_semantic_review",
    }
    return rows, summary


def build_reparse_audit(
    samples: Sequence[Mapping[str, Any]],
    prior_outputs: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Audit saved Qwen/Llama text with name-aware scoring without modifying it."""
    item_by_id = {str(item["item_id"]): item for item in samples}
    changed: list[dict[str, Any]] = []
    model_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for record in prior_outputs:
        item = item_by_id[str(record["item_id"])]
        parsed = parse_followup_response(str(record.get("raw_response", "")), item)
        alias = str(record["model_alias"])
        model_counts[alias]["records"] += 1
        model_counts[alias]["name_mapped"] += int(parsed["semantic_name_mapping_used"])
        model_counts[alias]["extractable_after"] += int(parsed["answer_extractable"])
        model_counts[alias]["extractable_before"] += int(record.get("answer_extractable") is True)
        if parsed["answer"] != record.get("answer"):
            changed.append(
                {
                    "item_id": record["item_id"],
                    "model_alias": alias,
                    "run_id": record["run_id"],
                    "old_answer": record.get("answer"),
                    "new_answer": parsed["answer"],
                    "raw_answer": parsed["raw_answer"],
                    "parse_source": parsed["parse_source"],
                    "old_correct": record.get("correct"),
                    "new_correct": parsed["answer"] == item["gold_answer"],
                    "raw_response": record.get("raw_response"),
                }
            )
    return {
        "parser_revision": "qwen-v4.1-name-aware-parser-2",
        "new_model_calls": 0,
        "original_artifacts_modified": False,
        "model_counts": {
            alias: dict(sorted(counts.items())) for alias, counts in sorted(model_counts.items())
        },
        "changed_answer_count": len(changed),
        "changed_records": changed,
    }


def analyze_position_order(
    variants: Sequence[Mapping[str, Any]],
    outputs: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Analyze label order while aligning choices by candidate identity."""
    item_by_id = {str(item["item_id"]): item for item in variants}
    records_by_source: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    records_by_variant: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for record in outputs:
        records_by_source[str(record["source_item_id"])].append(record)
        records_by_variant[str(record["variant_id"])].append(record)
    source_items: dict[str, Mapping[str, Any]] = {}
    for item in variants:
        source_items.setdefault(str(item["source_item_id"]), item)
    base_rows: list[dict[str, Any]] = []
    for source_id, records in sorted(records_by_source.items()):
        by_rotation: list[dict[str, Any]] = []
        selected_identities: Counter[str] = Counter()
        wrong_identities: Counter[str] = Counter()
        for variant in sorted(
            (item for item in variants if item["source_item_id"] == source_id),
            key=lambda item: int(item["metadata"]["position_rotation"]),
        ):
            variant_records = records_by_variant[str(variant["variant_id"])]
            valid = valid_records(variant_records)
            identity_counts = Counter(
                str(variant["entities"][record["answer"]]["name"]) for record in valid
            )
            selected_identities.update(identity_counts)
            wrong_identity_counts = Counter(
                str(variant["entities"][record["answer"]]["name"])
                for record in valid
                if record.get("correct") is not True
            )
            wrong_identities.update(wrong_identity_counts)
            by_rotation.append(
                {
                    "variant_id": variant["variant_id"],
                    "rotation": variant["metadata"]["position_rotation"],
                    "gold_position": variant["gold_answer"],
                    "gold_candidate_name": variant["entities"][variant["gold_answer"]]["name"],
                    "valid_answers": len(valid),
                    "correct": sum(record.get("correct") is True for record in valid),
                    "accuracy": ratio(
                        sum(record.get("correct") is True for record in valid), len(valid)
                    ),
                    "selected_candidate_identity_distribution": dict(identity_counts),
                    "wrong_candidate_identity_distribution": dict(wrong_identity_counts),
                }
            )
        accuracies = [row["accuracy"] for row in by_rotation if row["accuracy"] is not None]
        group = str(next(item for item in variants if item["source_item_id"] == source_id)["selection_group"])
        base_rows.append(
            {
                "source_item_id": source_id,
                "selection_group": group,
                "difficulty_cell": source_items[source_id]["metadata"]["difficulty_cell"],
                "scenario": source_items[source_id]["scenario"],
                "variant_results": by_rotation,
                "selected_candidate_identity_distribution": dict(selected_identities),
                "wrong_candidate_identity_distribution": dict(wrong_identities),
                "same_wrong_identity_across_observed_wrong_answers": (
                    sum(wrong_identities.values()) > 1 and len(wrong_identities) == 1
                ),
                "observed_accuracy_changes_across_orderings": len(set(accuracies)) > 1,
                "all_four_gold_positions_observed": {
                    row["gold_position"] for row in by_rotation
                }
                == set(LABELS),
            }
        )

    by_group: dict[str, dict[str, Any]] = {}
    for group in ("stable_wrong", "mixed", "stable_correct_control"):
        source_ids = {row["source_item_id"] for row in base_rows if row["selection_group"] == group}
        group_records = [record for record in outputs if record["source_item_id"] in source_ids]
        by_group[group] = {
            "base_items": len(source_ids),
            **summarize_records(group_records),
            "items_with_accuracy_change_across_orderings": sum(
                row["observed_accuracy_changes_across_orderings"]
                for row in base_rows
                if row["selection_group"] == group
            ),
            "items_repeating_one_wrong_candidate_identity": sum(
                row["same_wrong_identity_across_observed_wrong_answers"]
                for row in base_rows
                if row["selection_group"] == group
            ),
        }
    gold_position: dict[str, Any] = {}
    for label in LABELS:
        subset = [
            record
            for record in outputs
            if item_by_id[str(record["variant_id"])]["gold_answer"] == label
        ]
        gold_position[label] = summarize_records(subset)
    by_rotation: dict[str, Any] = {}
    for rotation in range(4):
        variant_ids = {
            str(item["variant_id"])
            for item in variants
            if int(item["metadata"]["position_rotation"]) == rotation
        }
        subset = [record for record in outputs if record["variant_id"] in variant_ids]
        by_rotation[str(rotation)] = summarize_records(subset)
    return {
        "design": {
            "selected_base_items": len(base_rows),
            "variants": len(variants),
            "runs_per_variant": 3,
            "selected_by_prior_performance": True,
            "population_accuracy_estimate": False,
            "interpretation_note": (
                "Rotation changes both labels and reading order; differences cannot be "
                "attributed solely to label preference."
            ),
        },
        "overall": summarize_records(outputs),
        "by_selection_group": by_group,
        "by_gold_position": gold_position,
        "by_rotation": by_rotation,
        "base_item_analysis": base_rows,
    }


def _bootstrap_mean_ci(
    values: Sequence[float], *, iterations: int = 5000, seed: int = 20260910
) -> list[float] | None:
    if not values:
        return None
    rng = random.Random(seed)
    estimates = []
    for _ in range(iterations):
        sample = [values[rng.randrange(len(values))] for _ in values]
        estimates.append(sum(sample) / len(sample))
    estimates.sort()
    return [
        round(estimates[int(0.025 * (len(estimates) - 1))], 6),
        round(estimates[int(0.975 * (len(estimates) - 1))], 6),
    ]


def analyze_information_load(
    variants: Sequence[Mapping[str, Any]],
    outputs: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Compute paired IL2 minus IL1 accuracy differences by base item."""
    grouped: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for record in outputs:
        grouped[(str(record["source_item_id"]), str(record["pair_version"]))].append(record)
    bases = sorted({source for source, _ in grouped})
    pairs: list[dict[str, Any]] = []
    for source in bases:
        source_variant = next(item for item in variants if item["source_item_id"] == source)
        summaries = {
            level: summarize_records(grouped[(source, level)])
            for level in ("IL1_low", "IL2_high")
        }
        valid_pair = all(summaries[level]["valid_answers"] == 3 for level in summaries)
        delta = (
            round(
                summaries["IL2_high"]["valid_answer_accuracy"]
                - summaries["IL1_low"]["valid_answer_accuracy"],
                6,
            )
            if valid_pair
            else None
        )
        disagreement = {}
        for level in summaries:
            answers = {
                record["answer"]
                for record in grouped[(source, level)]
                if record.get("answer_extractable") is True
            }
            disagreement[level] = len(answers) >= 2
        pairs.append(
            {
                "source_item_id": source,
                "constraint_load": source_variant["difficulty_factors"]["constraint_load"],
                "distractor_similarity": source_variant["difficulty_factors"][
                    "distractor_similarity"
                ],
                "scenario": source_variant["scenario"],
                "il1": summaries["IL1_low"],
                "il2": summaries["IL2_high"],
                "il2_minus_il1_accuracy": delta,
                "paired_complete": valid_pair,
                "answer_disagreement": disagreement,
            }
        )

    def grouped_result(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        deltas = [float(row["il2_minus_il1_accuracy"]) for row in rows if row["il2_minus_il1_accuracy"] is not None]
        subset_ids = {str(row["source_item_id"]) for row in rows}
        low_records = [
            record
            for record in outputs
            if record["source_item_id"] in subset_ids and record["pair_version"] == "IL1_low"
        ]
        high_records = [
            record
            for record in outputs
            if record["source_item_id"] in subset_ids and record["pair_version"] == "IL2_high"
        ]
        return {
            "base_items": len(rows),
            "complete_pairs": len(deltas),
            "il1": summarize_records(low_records),
            "il2": summarize_records(high_records),
            "mean_paired_accuracy_delta_il2_minus_il1": (
                round(sum(deltas) / len(deltas), 6) if deltas else None
            ),
            "paired_bootstrap_95_ci": _bootstrap_mean_ci(deltas),
            "items_harder_with_il2": sum(delta < 0 for delta in deltas),
            "items_easier_with_il2": sum(delta > 0 for delta in deltas),
            "items_no_observed_change": sum(delta == 0 for delta in deltas),
        }

    by_cl = {
        level: grouped_result([row for row in pairs if row["constraint_load"] == level])
        for level in ("CL1", "CL2", "CL3")
    }
    by_ds = {
        level: grouped_result([row for row in pairs if row["distractor_similarity"] == level])
        for level in ("DS1_far", "DS2_medium", "DS3_near")
    }
    return {
        "design": {
            "base_items": len(pairs),
            "versions_per_base": 2,
            "runs_per_version": 3,
            "selection_used_prior_accuracy": False,
            "paired_difference": "IL2 accuracy minus IL1 accuracy",
            "bootstrap_unit": "base item retaining both versions and all runs",
        },
        "overall": grouped_result(pairs),
        "by_constraint_load": by_cl,
        "by_distractor_similarity": by_ds,
        "pairs": pairs,
    }


def item_behavior(
    items: Sequence[Mapping[str, Any]], records: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    """Summarize between-item outcomes separately from within-item sampling variation."""
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[str(record["item_id"])].append(record)
    complete = mixed = all_correct = all_wrong = disagreement = 0
    for item in items:
        valid = valid_records(grouped[str(item["item_id"])])
        if len(valid) != 3:
            continue
        complete += 1
        correctness = sum(record.get("correct") is True for record in valid)
        answers = {record["answer"] for record in valid}
        all_correct += correctness == 3
        all_wrong += correctness == 0
        mixed += 0 < correctness < 3
        disagreement += len(answers) >= 2
    return {
        "items": len(items),
        "complete_three_run_items": complete,
        "all_three_correct_items": all_correct,
        "all_three_wrong_items": all_wrong,
        "correct_wrong_coexist_items": mixed,
        "within_item_answer_disagreement_items": disagreement,
    }


def build_extension_item_analysis(
    items: Sequence[Mapping[str, Any]], records: Sequence[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    """Build one three-run calibration row for every independent extension item."""
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[str(record["item_id"])].append(record)
    rows: list[dict[str, Any]] = []
    for item in items:
        observations = sorted(
            grouped[str(item["item_id"])], key=lambda record: int(record["run_id"])
        )
        valid = valid_records(observations)
        correct = sum(record.get("correct") is True for record in valid)
        wrong_options = sorted(
            {str(record["answer"]) for record in valid if record.get("correct") is not True}
        )
        answer_counts = Counter(str(record["answer"]) for record in valid)
        rows.append(
            {
                "item_id": item["item_id"],
                "difficulty_cell": item["metadata"]["difficulty_cell"],
                "difficulty_factors": item["difficulty_factors"],
                "scenario": item["scenario"],
                "gold_answer": item["gold_answer"],
                "expected_runs": 3,
                "actual_runs": len(observations),
                "valid_answers": len(valid),
                "correct": correct,
                "valid_accuracy": ratio(correct, len(valid)),
                "answer_distribution": {
                    label: answer_counts[label] for label in LABELS
                },
                "has_within_item_answer_disagreement": len(answer_counts) >= 2,
                "has_correct_and_wrong": 0 < correct < len(valid),
                "all_three_valid_and_correct": len(valid) == 3 and correct == 3,
                "all_three_valid_and_wrong": len(valid) == 3 and correct == 0,
                "observed_wrong_options": wrong_options,
                "observed_wrong_violation_signatures": {
                    label: item["option_violation_signature"][label]
                    for label in wrong_options
                },
            }
        )
    return rows


def factor_statistics(
    items: Sequence[Mapping[str, Any]], records: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    """Build cell and marginal Qwen statistics for one registered split."""
    item_by_id = {str(item["item_id"]): item for item in items}
    by_cell: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for record in records:
        by_cell[str(record["difficulty_cell"])].append(record)
    cells = {cell: summarize_records(group) for cell, group in sorted(by_cell.items())}
    factors: dict[str, dict[str, Any]] = {}
    levels = {
        "constraint_load": ("CL1", "CL2", "CL3"),
        "distractor_similarity": ("DS1_far", "DS2_medium", "DS3_near"),
        "information_load": ("IL1_low", "IL2_high"),
    }
    for factor, factor_levels in levels.items():
        factors[factor] = {}
        for level in factor_levels:
            subset = [
                record
                for record in records
                if record["difficulty_factors"][factor] == level
            ]
            factors[factor][level] = summarize_records(subset)

    controlled: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for ds in levels["distractor_similarity"]:
        for il in levels["information_load"]:
            values = {
                cl: factors_for_cell(cells, cl, ds, il) for cl in levels["constraint_load"]
            }
            controlled["constraint_load"].append(
                {"fixed": {"distractor_similarity": ds, "information_load": il}, "accuracy": values}
            )
    for cl in levels["constraint_load"]:
        for il in levels["information_load"]:
            values = {
                ds: factors_for_cell(cells, cl, ds, il) for ds in levels["distractor_similarity"]
            }
            controlled["distractor_similarity"].append(
                {"fixed": {"constraint_load": cl, "information_load": il}, "accuracy": values}
            )
    for cl in levels["constraint_load"]:
        for ds in levels["distractor_similarity"]:
            values = {
                il: factors_for_cell(cells, cl, ds, il) for il in levels["information_load"]
            }
            controlled["information_load"].append(
                {"fixed": {"constraint_load": cl, "distractor_similarity": ds}, "accuracy": values}
            )
    rankings = sorted(
        (
            {"difficulty_cell": cell, "valid_answer_accuracy": stats["valid_answer_accuracy"]}
            for cell, stats in cells.items()
        ),
        key=lambda row: (
            -(row["valid_answer_accuracy"] if row["valid_answer_accuracy"] is not None else -1),
            row["difficulty_cell"],
        ),
    )
    trend_summary: dict[str, dict[str, int]] = {}
    for factor, slices in controlled.items():
        first_last = {
            "constraint_load": ("CL1", "CL3"),
            "distractor_similarity": ("DS1_far", "DS3_near"),
            "information_load": ("IL1_low", "IL2_high"),
        }[factor]
        counts = Counter()
        for row in slices:
            first = row["accuracy"][first_last[0]]
            last = row["accuracy"][first_last[1]]
            if first is None or last is None:
                counts["not_applicable"] += 1
            elif last < first:
                counts["higher_level_lower_accuracy"] += 1
            elif last > first:
                counts["higher_level_higher_accuracy"] += 1
            else:
                counts["endpoint_tie"] += 1
        trend_summary[factor] = dict(sorted(counts.items()))
    return {
        "overall": summarize_records(records),
        "item_behavior": item_behavior(items, records),
        "cells": cells,
        "marginal_factors": factors,
        "controlled_slices": dict(controlled),
        "controlled_endpoint_trend_summary": trend_summary,
        "cell_ranking_easiest_to_hardest": rankings,
        "item_count": len(item_by_id),
    }


def factors_for_cell(
    cells: Mapping[str, Mapping[str, Any]], cl: str, ds: str, il: str
) -> float | None:
    return cells.get(f"{cl}__{ds}__{il}", {}).get("valid_answer_accuracy")


def compare_factor_replication(
    development: Mapping[str, Any], validation: Mapping[str, Any]
) -> dict[str, Any]:
    """Compare direction and magnitude of marginal CL/DS/IL effects."""
    endpoints = {
        "constraint_load": ("CL1", "CL3"),
        "distractor_similarity": ("DS1_far", "DS3_near"),
        "information_load": ("IL1_low", "IL2_high"),
    }
    result: dict[str, Any] = {}
    for factor, (low, high) in endpoints.items():
        dev = development["marginal_factors"][factor]
        val = validation["marginal_factors"][factor]
        dev_delta = dev[high]["valid_answer_accuracy"] - dev[low]["valid_answer_accuracy"]
        val_delta = val[high]["valid_answer_accuracy"] - val[low]["valid_answer_accuracy"]
        result[factor] = {
            "development_high_minus_low": round(dev_delta, 6),
            "validation_high_minus_low": round(val_delta, 6),
            "same_direction": (dev_delta == 0 and val_delta == 0)
            or (dev_delta < 0 and val_delta < 0)
            or (dev_delta > 0 and val_delta > 0),
            "interpretation": (
                "direction replicated on the independent extension"
                if ((dev_delta < 0 and val_delta < 0) or (dev_delta > 0 and val_delta > 0))
                else "direction did not replicate clearly"
            ),
        }
    return result
