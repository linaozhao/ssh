"""Model-separated analysis for the v4.1 single-agent calibration."""

from __future__ import annotations

import csv
import json
import math
import random
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from mad_attr_filter.attributes import ATTRIBUTE_BY_KEY
from mad_attr_filter.single_agent import model_alias
from mad_attr_filter.v4_calibration import PARSER_REVISION

VALID_OPTIONS = ("A", "B", "C", "D")
FACTOR_FIELDS = ("constraint_load", "distractor_similarity", "information_load")


def _ratio(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 6) if denominator else None


def _valid_answer(record: Mapping[str, Any]) -> str | None:
    answer = record.get("answer")
    return str(answer) if record.get("answer_extractable") is True and answer in VALID_OPTIONS else None


def _request_success(record: Mapping[str, Any]) -> bool:
    return record.get("request_error") is None


def run_key(record: Mapping[str, Any]) -> tuple[str, str, int]:
    """Return the unique item/model/run key for one observation."""
    return (
        str(record.get("item_id")),
        str(record.get("model_alias")),
        int(record.get("run_id", 0)),
    )


def audit_run_inventory(
    samples: Sequence[Mapping[str, Any]],
    outputs: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
    experiment_fingerprint: str,
) -> dict[str, Any]:
    """Audit missing, duplicate, unknown, and fingerprint-mismatched runs."""
    expected = {
        (str(sample["item_id"]), model_alias(model), run_id)
        for sample in samples
        for model in config["models"]
        for run_id, _ in enumerate(config["seeds"], start=1)
    }
    observed_counts = Counter(run_key(record) for record in outputs)
    observed = set(observed_counts)
    duplicate = sorted(key for key, count in observed_counts.items() if count > 1)
    unknown = sorted(observed - expected)
    missing = sorted(expected - observed)
    mismatches = [
        run_key(record)
        for record in outputs
        if record.get("experiment_fingerprint") != experiment_fingerprint
    ]
    return {
        "expected_runs": len(expected),
        "completed_records": len(outputs),
        "unique_completed_runs": len(observed),
        "missing_run_count": len(missing),
        "duplicate_run_count": len(duplicate),
        "unknown_run_count": len(unknown),
        "fingerprint_mismatch_count": len(mismatches),
        "missing_runs": [list(key) for key in missing],
        "duplicate_runs": [list(key) for key in duplicate],
        "unknown_runs": [list(key) for key in unknown],
        "fingerprint_mismatches": [list(key) for key in mismatches],
        "complete": not (missing or duplicate or unknown or mismatches),
    }


def build_item_model_analysis(
    samples: Sequence[Mapping[str, Any]],
    outputs: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Build one analysis row for each item and model (180 x 2)."""
    grouped: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for record in outputs:
        grouped[(str(record["item_id"]), str(record["model_alias"]))].append(record)
    rows: list[dict[str, Any]] = []
    for sample in samples:
        for model in config["models"]:
            alias = model_alias(model)
            records = sorted(
                grouped.get((str(sample["item_id"]), alias), []),
                key=lambda record: int(record["run_id"]),
            )
            valid_records = [record for record in records if _valid_answer(record) is not None]
            valid_wrong = [record for record in valid_records if record.get("correct") is not True]
            api_failures = [record for record in records if not _request_success(record)]
            unrecognized = [
                record
                for record in records
                if _request_success(record) and _valid_answer(record) is None
            ]
            answer_counts = Counter(_valid_answer(record) for record in valid_records)
            unique_answers = sorted(label for label in VALID_OPTIONS if answer_counts[label])
            wrong_options = sorted(
                {str(record["answer"]) for record in valid_wrong if record.get("answer") in VALID_OPTIONS}
            )
            expected_runs = len(config["seeds"])
            complete_valid = len(valid_records) == expected_runs
            num_correct = sum(record.get("correct") is True for record in valid_records)
            rows.append(
                {
                    "item_id": sample["item_id"],
                    "model_alias": alias,
                    "model_name": model["model_name"],
                    "expected_runs": expected_runs,
                    "actual_runs": len(records),
                    "api_success_count": len(records) - len(api_failures),
                    "api_failure_count": len(api_failures),
                    "valid_answer_count": len(valid_records),
                    "correct_count": num_correct,
                    "valid_wrong_count": len(valid_wrong),
                    "unrecognized_count": len(unrecognized),
                    "json_compliant_count": sum(
                        record.get("json_compliant") is True for record in records
                    ),
                    "truncated_count": sum(record.get("truncated") is True for record in records),
                    "answer_distribution": {
                        label: answer_counts[label] for label in VALID_OPTIONS
                    },
                    "unique_valid_answers": unique_answers,
                    "has_at_least_two_valid_answers": len(unique_answers) >= 2,
                    "has_correct_and_valid_wrong": bool(num_correct and valid_wrong),
                    "complete_valid_observation": complete_valid,
                    "all_three_valid_and_correct": complete_valid and num_correct == expected_runs,
                    "all_three_valid_and_wrong": complete_valid and num_correct == 0,
                    "observed_wrong_options": wrong_options,
                    "observed_wrong_violation_signatures": {
                        label: list(sample["option_violation_signature"][label])
                        for label in wrong_options
                    },
                    "wrong_observations": [
                        {
                            "run_id": int(record["run_id"]),
                            "seed": int(record["seed"]),
                            "answer": record["answer"],
                            "violation_signature": list(
                                record["selected_option_violation_signature"]
                            ),
                        }
                        for record in valid_wrong
                    ],
                    "gold_answer": sample["gold_answer"],
                    "scenario": sample["scenario"],
                    "difficulty_factors": dict(sample["difficulty_factors"]),
                    "difficulty_cell": sample["metadata"]["difficulty_cell"],
                }
            )
    return rows


def _cluster_bootstrap_ci(
    item_records: Sequence[Sequence[Mapping[str, Any]]],
    *,
    iterations: int = 1000,
    seed: int = 20260909,
) -> list[float] | None:
    """Bootstrap valid-answer accuracy by resampling items as clusters."""
    clusters = [list(records) for records in item_records if records]
    if not clusters:
        return None
    rng = random.Random(seed)
    estimates: list[float] = []
    for _ in range(iterations):
        sampled = [clusters[rng.randrange(len(clusters))] for _ in clusters]
        flattened = [record for cluster in sampled for record in cluster]
        valid = [record for record in flattened if _valid_answer(record) is not None]
        if valid:
            estimates.append(sum(record.get("correct") is True for record in valid) / len(valid))
    if not estimates:
        return None
    estimates.sort()
    low = estimates[int(0.025 * (len(estimates) - 1))]
    high = estimates[int(0.975 * (len(estimates) - 1))]
    return [round(low, 6), round(high, 6)]


def _cell_stat(
    alias: str,
    cell: str,
    samples: Sequence[Mapping[str, Any]],
    records: Sequence[Mapping[str, Any]],
    item_rows: Sequence[Mapping[str, Any]],
    expected_runs_per_item: int,
) -> dict[str, Any]:
    factors = dict(samples[0]["difficulty_factors"])
    expected_records = len(samples) * expected_runs_per_item
    api_success = sum(_request_success(record) for record in records)
    valid = [record for record in records if _valid_answer(record) is not None]
    valid_wrong = [record for record in valid if record.get("correct") is not True]
    correct = sum(record.get("correct") is True for record in valid)
    complete_rows = [row for row in item_rows if row["complete_valid_observation"]]
    disagreement = sum(row["has_at_least_two_valid_answers"] for row in complete_rows)
    coexist = sum(row["has_correct_and_valid_wrong"] for row in complete_rows)
    single_wrong = sum(
        len(record.get("selected_option_violation_signature", [])) == 1
        for record in valid_wrong
    )
    multi_wrong = sum(
        len(record.get("selected_option_violation_signature", [])) >= 2
        for record in valid_wrong
    )
    by_item: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for record in records:
        by_item[str(record["item_id"])].append(record)
    json_count = sum(record.get("json_compliant") is True for record in records)
    truncated_count = sum(record.get("truncated") is True for record in records)
    return {
        "model_alias": alias,
        "difficulty_cell": cell,
        **factors,
        "item_count": len(samples),
        "expected_record_count": expected_records,
        "actual_record_count": len(records),
        "api_success_count": api_success,
        "api_success_denominator": len(records),
        "api_success_rate": _ratio(api_success, len(records)),
        "valid_answer_count": len(valid),
        "valid_answer_denominator": len(records),
        "valid_answer_rate": _ratio(len(valid), len(records)),
        "json_compliant_count": json_count,
        "json_compliant_denominator": len(records),
        "json_compliant_rate": _ratio(json_count, len(records)),
        "truncated_count": truncated_count,
        "truncated_denominator": api_success,
        "truncated_rate": _ratio(truncated_count, api_success),
        "correct_count": correct,
        "accuracy_all_attempts_denominator": len(records),
        "accuracy_all_attempts": _ratio(correct, len(records)),
        "valid_accuracy_denominator": len(valid),
        "valid_answer_accuracy": _ratio(correct, len(valid)),
        "valid_accuracy_item_cluster_bootstrap_95_ci": _cluster_bootstrap_ci(
            list(by_item.values())
        ),
        "complete_valid_item_count": len(complete_rows),
        "incomplete_item_count": len(item_rows) - len(complete_rows),
        "disagreement_item_count": disagreement,
        "disagreement_denominator": len(complete_rows),
        "disagreement_rate": _ratio(disagreement, len(complete_rows)),
        "correct_wrong_coexist_item_count": coexist,
        "correct_wrong_coexist_denominator": len(complete_rows),
        "correct_wrong_coexist_rate": _ratio(coexist, len(complete_rows)),
        "all_three_valid_and_correct_item_count": sum(
            row["all_three_valid_and_correct"] for row in complete_rows
        ),
        "all_three_valid_and_wrong_item_count": sum(
            row["all_three_valid_and_wrong"] for row in complete_rows
        ),
        "valid_wrong_answer_count": len(valid_wrong),
        "single_constraint_wrong_count": single_wrong,
        "single_constraint_wrong_denominator": len(valid_wrong),
        "single_constraint_wrong_rate": _ratio(single_wrong, len(valid_wrong)),
        "multi_constraint_wrong_count": multi_wrong,
        "multi_constraint_wrong_denominator": len(valid_wrong),
        "multi_constraint_wrong_rate": _ratio(multi_wrong, len(valid_wrong)),
    }


def build_cell_model_statistics(
    samples: Sequence[Mapping[str, Any]],
    outputs: Sequence[Mapping[str, Any]],
    item_rows: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Build the 2 models x 18 cells core table."""
    samples_by_cell: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    records_by_cell_model: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    rows_by_cell_model: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for sample in samples:
        samples_by_cell[str(sample["metadata"]["difficulty_cell"])].append(sample)
    for record in outputs:
        records_by_cell_model[
            (str(record["difficulty_cell"]), str(record["model_alias"]))
        ].append(record)
    for row in item_rows:
        rows_by_cell_model[(str(row["difficulty_cell"]), str(row["model_alias"]))].append(row)
    result: list[dict[str, Any]] = []
    for model in config["models"]:
        alias = model_alias(model)
        for cell, cell_samples in sorted(samples_by_cell.items()):
            result.append(
                _cell_stat(
                    alias,
                    cell,
                    cell_samples,
                    records_by_cell_model.get((cell, alias), []),
                    rows_by_cell_model.get((cell, alias), []),
                    len(config["seeds"]),
                )
            )
    return result


def write_cell_statistics_csv(path: str | Path, rows: Sequence[Mapping[str, Any]]) -> None:
    """Write the core cell table as CSV."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        output.write_text("", encoding="utf-8")
        return
    with output.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: json.dumps(value) if isinstance(value, (list, dict)) else value
                    for key, value in row.items()
                }
            )


def _aggregate_records(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    valid = [record for record in records if _valid_answer(record) is not None]
    correct = sum(record.get("correct") is True for record in valid)
    return {
        "record_count": len(records),
        "valid_answer_count": len(valid),
        "correct_count": correct,
        "valid_answer_rate": _ratio(len(valid), len(records)),
        "valid_answer_accuracy": _ratio(correct, len(valid)),
    }


def _average_ranks(values: Mapping[str, float]) -> dict[str, float]:
    ordered = sorted(values.items(), key=lambda pair: pair[1])
    ranks: dict[str, float] = {}
    index = 0
    while index < len(ordered):
        end = index + 1
        while end < len(ordered) and ordered[end][1] == ordered[index][1]:
            end += 1
        average = ((index + 1) + end) / 2
        for cell, _ in ordered[index:end]:
            ranks[cell] = average
        index = end
    return ranks


def _spearman(first: Mapping[str, float], second: Mapping[str, float]) -> float | None:
    shared = sorted(set(first) & set(second))
    if len(shared) < 2:
        return None
    rank_a = _average_ranks({key: first[key] for key in shared})
    rank_b = _average_ranks({key: second[key] for key in shared})
    mean_a = sum(rank_a.values()) / len(shared)
    mean_b = sum(rank_b.values()) / len(shared)
    numerator = sum((rank_a[key] - mean_a) * (rank_b[key] - mean_b) for key in shared)
    denom_a = math.sqrt(sum((rank_a[key] - mean_a) ** 2 for key in shared))
    denom_b = math.sqrt(sum((rank_b[key] - mean_b) ** 2 for key in shared))
    return round(numerator / (denom_a * denom_b), 6) if denom_a and denom_b else None


def build_factor_analysis(
    outputs: Sequence[Mapping[str, Any]],
    cell_rows: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    """Build model-specific marginal and controlled factor comparisons."""
    by_model: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    cell_by_model: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for record in outputs:
        by_model[str(record["model_alias"])].append(record)
    for row in cell_rows:
        cell_by_model[str(row["model_alias"])].append(row)
    payload: dict[str, Any] = {
        "analysis_unit": "item clusters with three within-item samples",
        "warning": (
            "Each cell contains 10 distinct items. Cells are not paired rewrites of the same items; "
            "comparisons are preliminary between-item calibration evidence, not strict paired effects."
        ),
        "models": {},
    }
    accuracy_maps: dict[str, dict[str, float]] = {}
    for model in config["models"]:
        alias = model_alias(model)
        records = by_model.get(alias, [])
        marginal: dict[str, dict[str, Any]] = {}
        for factor in FACTOR_FIELDS:
            groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
            for record in records:
                groups[str(record["difficulty_factors"][factor])].append(record)
            marginal[factor] = {
                level: _aggregate_records(group) for level, group in sorted(groups.items())
            }
        controlled: dict[str, list[dict[str, Any]]] = {}
        for factor in FACTOR_FIELDS:
            controls = [field for field in FACTOR_FIELDS if field != factor]
            comparisons: dict[tuple[str, str], dict[str, Any]] = defaultdict(dict)
            for row in cell_by_model.get(alias, []):
                key = (str(row[controls[0]]), str(row[controls[1]]))
                comparisons[key][str(row[factor])] = {
                    "valid_answer_accuracy": row["valid_answer_accuracy"],
                    "disagreement_rate": row["disagreement_rate"],
                    "correct_wrong_coexist_rate": row["correct_wrong_coexist_rate"],
                    "bootstrap_95_ci": row["valid_accuracy_item_cluster_bootstrap_95_ci"],
                }
            controlled[factor] = [
                {
                    "fixed": {controls[0]: key[0], controls[1]: key[1]},
                    "levels": dict(sorted(levels.items())),
                }
                for key, levels in sorted(comparisons.items())
            ]
        cell_accuracy = {
            str(row["difficulty_cell"]): float(row["valid_answer_accuracy"])
            for row in cell_by_model.get(alias, [])
            if row["valid_answer_accuracy"] is not None
        }
        accuracy_maps[alias] = cell_accuracy
        trend_summary: dict[str, dict[str, int]] = {}
        level_orders = {
            "constraint_load": ("CL1", "CL2", "CL3"),
            "distractor_similarity": ("DS1_far", "DS2_medium", "DS3_near"),
            "information_load": ("IL1_low", "IL2_high"),
        }
        for factor, comparisons in controlled.items():
            counts: Counter[str] = Counter()
            order = level_orders[factor]
            for comparison in comparisons:
                values = [
                    comparison["levels"].get(level, {}).get("valid_answer_accuracy")
                    for level in order
                ]
                if any(value is None for value in values):
                    counts["incomplete"] += 1
                elif all(values[index] == values[0] for index in range(1, len(values))):
                    counts["flat"] += 1
                elif all(values[index] >= values[index + 1] for index in range(len(values) - 1)):
                    counts["higher_level_harder_or_equal"] += 1
                elif all(values[index] <= values[index + 1] for index in range(len(values) - 1)):
                    counts["higher_level_easier_or_equal"] += 1
                else:
                    counts["nonmonotonic"] += 1
            trend_summary[factor] = dict(sorted(counts.items()))
        payload["models"][alias] = {
            "overall": _aggregate_records(records),
            "json_compliance_rate": _ratio(
                sum(record.get("json_compliant") is True for record in records), len(records)
            ),
            "api_success_rate": _ratio(
                sum(_request_success(record) for record in records), len(records)
            ),
            "marginal_factor_statistics": marginal,
            "controlled_cell_comparisons": controlled,
            "controlled_trend_summary": trend_summary,
            "cell_ranking_easiest_to_hardest": [
                {"difficulty_cell": cell, "valid_answer_accuracy": accuracy}
                for cell, accuracy in sorted(
                    cell_accuracy.items(), key=lambda pair: (-pair[1], pair[0])
                )
            ],
        }
    aliases = [model_alias(model) for model in config["models"]]
    payload["cross_model_cell_rank_spearman"] = (
        _spearman(accuracy_maps.get(aliases[0], {}), accuracy_maps.get(aliases[1], {}))
        if len(aliases) == 2
        else None
    )
    return payload


def _diagnostic_scope(
    samples_by_id: Mapping[str, Mapping[str, Any]],
    records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    attributes = sorted(
        {
            str(constraint["attribute"])
            for sample in samples_by_id.values()
            for constraint in sample["constraints"]
        }
    )
    item_sets: dict[str, set[str]] = {attribute: set() for attribute in attributes}
    valid_exposure: Counter[str] = Counter()
    violatable_exposure: Counter[str] = Counter()
    error_counts: Counter[str] = Counter()
    signature_sizes: Counter[str] = Counter()
    for item_id, sample in samples_by_id.items():
        for constraint in sample["constraints"]:
            item_sets[str(constraint["attribute"])].add(item_id)
    for record in records:
        if _valid_answer(record) is None:
            continue
        sample = samples_by_id[str(record["item_id"])]
        constraint_attr = {
            str(constraint["id"]): str(constraint["attribute"])
            for constraint in sample["constraints"]
        }
        for attribute in constraint_attr.values():
            valid_exposure[attribute] += 1
        violatable_ids = {
            str(constraint_id)
            for label, signature in sample["option_violation_signature"].items()
            if label != sample["gold_answer"]
            for constraint_id in signature
        }
        for constraint_id in violatable_ids:
            violatable_exposure[constraint_attr[constraint_id]] += 1
        if record.get("correct") is not True:
            signature = list(record.get("selected_option_violation_signature", []))
            signature_sizes[str(len(signature)) if len(signature) < 3 else "3+"] += 1
            for constraint_id in signature:
                error_counts[constraint_attr[str(constraint_id)]] += 1
    rows = []
    for attribute in attributes:
        spec = ATTRIBUTE_BY_KEY[attribute]
        rows.append(
            {
                "attribute": attribute,
                "category": spec.category,
                "number_of_times_violated_by_selected_wrong_answer": error_counts[attribute],
                "number_of_items_containing_attribute": len(item_sets[attribute]),
                "valid_run_exposure": valid_exposure[attribute],
                "violatable_run_exposure": violatable_exposure[attribute],
                "normalized_error_rate_per_violatable_run": _ratio(
                    error_counts[attribute], violatable_exposure[attribute]
                ),
                "normalized_error_rate_per_valid_item_run": _ratio(
                    error_counts[attribute], valid_exposure[attribute]
                ),
            }
        )
    rows.sort(
        key=lambda row: (
            -(row["normalized_error_rate_per_violatable_run"] or 0),
            -row["number_of_times_violated_by_selected_wrong_answer"],
            row["attribute"],
        )
    )
    total_wrong = sum(signature_sizes.values())
    return {
        "valid_wrong_answer_count": total_wrong,
        "violation_signature_size_distribution": dict(sorted(signature_sizes.items())),
        "single_constraint_error_rate": _ratio(signature_sizes["1"], total_wrong),
        "attributes": rows,
    }


def build_constraint_diagnostics(
    samples: Sequence[Mapping[str, Any]],
    outputs: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    """Build exposure-normalized constraint diagnostics by model and overall."""
    samples_by_id = {str(sample["item_id"]): sample for sample in samples}
    return {
        "design_note": (
            "DS3_near makes every wrong option violate one constraint by construction. "
            "A high single-constraint share in DS3 is not independently discovered model behavior."
        ),
        "normalization_note": (
            "The primary rate divides selected violations by valid runs where the attribute "
            "was present and at least one wrong option could violate it."
        ),
        "overall": _diagnostic_scope(samples_by_id, outputs),
        "by_model": {
            model_alias(model): _diagnostic_scope(
                samples_by_id,
                [
                    record
                    for record in outputs
                    if str(record["model_alias"]) == model_alias(model)
                ],
            )
            for model in config["models"]
        },
    }


def build_parse_audit(outputs: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Return all formatting, extraction, request, or truncation anomalies."""
    fields = (
        "experiment_id", "experiment_fingerprint", "item_id", "difficulty_cell",
        "model_alias", "model_name", "run_id", "seed", "answer", "answer_extractable",
        "json_compliant", "strict_json_syntax", "parse_source", "fallback_used",
        "ambiguous_answer", "answer_candidates", "parse_error", "request_error",
        "finish_reason", "truncated", "raw_response",
    )
    return [
        {field: record.get(field) for field in fields}
        for record in outputs
        if record.get("json_compliant") is not True
        or record.get("answer_extractable") is not True
        or record.get("truncated") is True
        or record.get("request_error") is not None
        or record.get("fallback_used") is True
    ]


def _overall_model_summary(
    outputs: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    summaries: dict[str, dict[str, Any]] = {}
    for model in config["models"]:
        alias = model_alias(model)
        records = [record for record in outputs if str(record["model_alias"]) == alias]
        valid = [record for record in records if _valid_answer(record) is not None]
        correct = sum(record.get("correct") is True for record in valid)
        summaries[alias] = {
            "records": len(records),
            "api_failures": sum(not _request_success(record) for record in records),
            "unrecognized_answers": sum(
                _request_success(record) and _valid_answer(record) is None for record in records
            ),
            "valid_answers": len(valid),
            "json_compliant": sum(record.get("json_compliant") is True for record in records),
            "truncated": sum(record.get("truncated") is True for record in records),
            "correct": correct,
            "valid_answer_rate": _ratio(len(valid), len(records)),
            "json_compliance_rate": _ratio(
                sum(record.get("json_compliant") is True for record in records), len(records)
            ),
            "valid_answer_accuracy": _ratio(correct, len(valid)),
        }
    return summaries


def build_report_markdown(
    *,
    inventory: Mapping[str, Any],
    preflight_summary: Mapping[str, Any],
    outputs: Sequence[Mapping[str, Any]],
    item_rows: Sequence[Mapping[str, Any]],
    cell_rows: Sequence[Mapping[str, Any]],
    factor_analysis: Mapping[str, Any],
    diagnostics: Mapping[str, Any],
    parse_audit: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
) -> tuple[str, dict[str, Any]]:
    """Build a dynamic Chinese report and decision summary."""
    overall = _overall_model_summary(outputs, config)
    complete_rows = [row for row in item_rows if row["complete_valid_observation"]]
    behavior: dict[str, dict[str, int]] = {}
    for model in config["models"]:
        alias = model_alias(model)
        rows = [row for row in complete_rows if row["model_alias"] == alias]
        behavior[alias] = {
            "complete_items": len(rows),
            "answer_disagreement_items": sum(row["has_at_least_two_valid_answers"] for row in rows),
            "correct_wrong_coexist_items": sum(row["has_correct_and_valid_wrong"] for row in rows),
            "all_three_correct_items": sum(row["all_three_valid_and_correct"] for row in rows),
            "all_three_wrong_items": sum(row["all_three_valid_and_wrong"] for row in rows),
        }
    informative_rows = [
        row
        for row in cell_rows
        if row["valid_answer_accuracy"] is not None
        and 0.4 <= row["valid_answer_accuracy"] <= 0.95
        and row["disagreement_item_count"] > 0
    ]
    coexist_total = sum(row["has_correct_and_valid_wrong"] for row in complete_rows)
    informative_by_model = {
        model_alias(model): sum(
            row["model_alias"] == model_alias(model) for row in informative_rows
        )
        for model in config["models"]
    }
    coexist_by_model = {
        alias: values["correct_wrong_coexist_items"] for alias, values in behavior.items()
    }
    near_perfect = {
        alias: (
            summary["valid_answer_accuracy"] is not None
            and (
                summary["valid_answer_accuracy"] >= 0.98
                or (
                    behavior[alias]["complete_items"] > 0
                    and behavior[alias]["all_three_correct_items"]
                    / behavior[alias]["complete_items"]
                    >= 0.85
                )
            )
        )
        for alias, summary in overall.items()
    }
    process_complete = bool(inventory["complete"])
    min_accuracy = min(
        (
            summary["valid_answer_accuracy"]
            for summary in overall.values()
            if summary["valid_answer_accuracy"] is not None
        ),
        default=0.0,
    )
    if not process_complete:
        decision = "PROCESS INCOMPLETE"
        recommendation = "暂不扩充：先补齐或核查缺失、重复和指纹异常记录。"
    elif min_accuracy < 0.4:
        decision = "ADJUST BEFORE EXPANSION"
        recommendation = "暂不直接扩充：至少一个模型的基础求解能力不足，应先降低最难条件。"
    elif (
        all(count >= 2 for count in informative_by_model.values())
        and all(count >= 5 for count in coexist_by_model.values())
    ):
        decision = "CONDITIONAL EXPANSION SUPPORTED"
        recommendation = (
            "可有条件扩充到每格 30 题：保留 18 格设计，同时优先检查本轮差异最大的组合，"
            "并用新增 20 题/格独立复核趋势。"
        )
    else:
        decision = "REFINE BEFORE EXPANSION"
        recommendation = (
            "不建议按当前比例直接均匀扩充到 540 题。先保留已有区分信号的 CL/DS 设计，"
            "增强或重构对模型影响不稳定的 IL2，并人工复核两模型三次稳定答错的题目；"
            "完成一轮小样本复核后再扩充。"
        )
    lines = [
        "# v4.1 单智能体难度校准报告",
        "",
        "## 实验状态",
        "",
        f"- 实验标识：`{config['experiment_id']}`",
        f"- 正式预期记录：{inventory['expected_runs']}；实际记录：{inventory['completed_records']}；唯一记录：{inventory['unique_completed_runs']}。",
        f"- 缺失：{inventory['missing_run_count']}；重复：{inventory['duplicate_run_count']}；未知键：{inventory['unknown_run_count']}；指纹不一致：{inventory['fingerprint_mismatch_count']}。",
        f"- 预检记录：{preflight_summary.get('total_records', 0)}；覆盖组合：{preflight_summary.get('difficulty_cells', 0)}/18；截断：{preflight_summary.get('truncated', 0)}。",
        f"- 流程完成：{'是' if process_complete else '否'}。这与难度设计是否得到支持是两个独立判断。",
        "",
        "## 模型总体结果",
        "",
        "| 模型 | 有效答案/记录 | JSON 合规 | 正确/有效答案 | 有效答案准确率 | API 失败 | 不可识别 | 截断 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for alias, summary in overall.items():
        accuracy = summary["valid_answer_accuracy"]
        accuracy_text = "不适用" if accuracy is None else f"{accuracy:.3f}"
        lines.append(
            f"| {alias} | {summary['valid_answers']}/{summary['records']} | "
            f"{summary['json_compliant']}/{summary['records']} | "
            f"{summary['correct']}/{summary['valid_answers']} | "
            f"{accuracy_text} | {summary['api_failures']} | "
            f"{summary['unrecognized_answers']} | {summary['truncated']} |"
        )
    lines.extend(
        ["", "三次采样只表示本轮观测；“三次全对”不等于证明题目始终容易。", "", "## 模型内部稳定性", ""]
    )
    for alias, values in behavior.items():
        lines.append(
            f"- `{alias}`：完整观测 {values['complete_items']} 题；至少两个有效答案 "
            f"{values['answer_disagreement_items']} 题；正确与有效错误共存 "
            f"{values['correct_wrong_coexist_items']} 题；三次全对 "
            f"{values['all_three_correct_items']} 题；三次均有效且全错 "
            f"{values['all_three_wrong_items']} 题。"
        )
    parse_models = Counter(str(record.get("model_alias")) for record in parse_audit)
    parse_sources = Counter(str(record.get("parse_source")) for record in parse_audit)
    parse_truncated = sum(record.get("truncated") is True for record in parse_audit)
    lines.extend(
        [
            "",
            "## 36 个模型-组合结果",
            "",
            "主要分歧率仅以三次均得到有效答案的题目为分母；不完整题目单独报告。",
            "",
            "| 模型 | 组合 | 正确/有效 | 有效准确率 | 95% 聚类 bootstrap CI | 分歧题/完整题 | 正误共存/完整题 | 不完整题 |",
            "|---|---|---:|---:|---|---:|---:|---:|",
        ]
    )
    for row in cell_rows:
        ci = row["valid_accuracy_item_cluster_bootstrap_95_ci"]
        ci_text = "不适用" if ci is None else f"[{ci[0]:.3f}, {ci[1]:.3f}]"
        accuracy_text = (
            "不适用"
            if row["valid_answer_accuracy"] is None
            else f"{row['valid_answer_accuracy']:.3f}"
        )
        lines.append(
            f"| {row['model_alias']} | {row['difficulty_cell']} | "
            f"{row['correct_count']}/{row['valid_accuracy_denominator']} | {accuracy_text} | "
            f"{ci_text} | {row['disagreement_item_count']}/{row['disagreement_denominator']} | "
            f"{row['correct_wrong_coexist_item_count']}/{row['correct_wrong_coexist_denominator']} | "
            f"{row['incomplete_item_count']} |"
        )
    lines.extend(["", "## 因素校准", ""])
    for alias, model_data in factor_analysis["models"].items():
        lines.extend([f"### {alias}", ""])
        for factor, levels in model_data["marginal_factor_statistics"].items():
            formatted = ", ".join(
                f"{level}={stats['valid_answer_accuracy']:.3f} "
                f"({stats['correct_count']}/{stats['valid_answer_count']})"
                for level, stats in levels.items()
                if stats["valid_answer_accuracy"] is not None
            )
            lines.append(f"- `{factor}` 边际准确率：{formatted}。")
            lines.append(
                f"- `{factor}` 固定其余因素后的趋势计数："
                f"{model_data['controlled_trend_summary'][factor]}。"
            )
        rankings = model_data["cell_ranking_easiest_to_hardest"]
        easiest = ", ".join(entry["difficulty_cell"] for entry in rankings[:3])
        hardest = ", ".join(entry["difficulty_cell"] for entry in rankings[-3:])
        lines.extend([f"- 本轮最易三格：{easiest}；最难三格：{hardest}。", ""])
    rho = factor_analysis.get("cross_model_cell_rank_spearman")
    rho_text = "不适用" if rho is None else f"{rho:.3f}"
    lines.extend(
        [
            f"- 两模型 18 格准确率排序的 Spearman 相关：{rho_text}。",
            "- 受控切片的 CL、DS、IL 逐格结果保存在 `factor_analysis.json`。不得预设单调性；本原型各格不是同题改写，因此只能作组间初步校准。",
        ]
    )
    factor_support: dict[str, str] = {}
    aliases = list(factor_analysis["models"])
    for factor, low, high in (
        ("constraint_load", "CL1", "CL3"),
        ("distractor_similarity", "DS1_far", "DS3_near"),
        ("information_load", "IL1_low", "IL2_high"),
    ):
        deltas = {}
        for alias in aliases:
            levels = factor_analysis["models"][alias]["marginal_factor_statistics"][factor]
            low_accuracy = levels[low]["valid_answer_accuracy"]
            high_accuracy = levels[high]["valid_answer_accuracy"]
            deltas[alias] = (
                None
                if low_accuracy is None or high_accuracy is None
                else round(high_accuracy - low_accuracy, 6)
            )
        if all(delta is not None and delta < -0.02 for delta in deltas.values()):
            interpretation = "两模型的边际结果均显示高水平更难，但受控切片并非全部单调"
        elif any(delta is not None and delta < -0.02 for delta in deltas.values()):
            interpretation = "仅部分模型显示明确下降，模型间证据不一致"
        else:
            interpretation = "未观察到稳定的难度增加信号"
        factor_support[factor] = interpretation
        lines.append(f"- `{factor}` 结论：{interpretation}；高减低准确率差为 {deltas}。")
    if informative_rows:
        informative_text = "；".join(
            f"{row['model_alias']}:{row['difficulty_cell']}"
            f"(acc={row['valid_answer_accuracy']:.3f}, disagreement="
            f"{row['disagreement_item_count']}/{row['disagreement_denominator']})"
            for row in informative_rows
        )
        lines.append(f"- 同时显示基本解题能力与自然分歧的组合：{informative_text}。")
    else:
        lines.append("- 本轮没有模型-组合同时达到预设的基本能力与自然分歧观察条件。")
    lines.extend(["", "## 稳定错误案例", ""])
    for model in config["models"]:
        alias = model_alias(model)
        stable_wrong = [
            row
            for row in complete_rows
            if row["model_alias"] == alias and row["all_three_valid_and_wrong"]
        ]
        examples = stable_wrong[:5]
        if not examples:
            lines.append(f"- `{alias}`：本轮没有三次均有效且全错的题目。")
            continue
        rendered = "；".join(
            f"{row['item_id']}({row['difficulty_cell']}, "
            f"wrong={row['observed_wrong_violation_signatures']})"
            for row in examples
        )
        lines.append(f"- `{alias}`：共 {len(stable_wrong)} 题；示例：{rendered}。")
    lines.extend(["", "## 约束违反诊断", ""])
    overall_diag = diagnostics["overall"]
    single_rate = overall_diag["single_constraint_error_rate"]
    lines.append(
        f"- 有效错误答案共 {overall_diag['valid_wrong_answer_count']} 个；其中单约束违反比例 "
        f"{single_rate if single_rate is not None else '不适用'}。"
    )
    lines.append("- 归一化分母为：属性在题目中出现，且至少一个错误选项可违反该属性时的有效运行次数。")
    top_attributes = [
        row
        for row in overall_diag["attributes"]
        if row["number_of_times_violated_by_selected_wrong_answer"] > 0
    ][:8]
    for row in top_attributes:
        lines.append(
            f"- `{row['attribute']}`：被选中违反 "
            f"{row['number_of_times_violated_by_selected_wrong_answer']} 次；可违反暴露 "
            f"{row['violatable_run_exposure']}；归一化率 "
            f"{row['normalized_error_rate_per_violatable_run']}。"
        )
    lines.extend(
        [
            "- DS3 的错误选项按设计均只违反一个约束；DS3 中单约束错误占比高不能单独解释为模型新行为。",
            "",
            "## 解析与输出审计",
            "",
            f"- 解析器版本：`{PARSER_REVISION}`；所有变化仅重解析已保存原文，没有追加模型调用。",
            f"- 需要人工审查的格式、备用解析、截断或请求异常记录：{len(parse_audit)}。",
            f"- 按模型：{dict(sorted(parse_models.items()))}；按解析来源：{dict(sorted(parse_sources.items()))}；其中截断 {parse_truncated} 条。",
            "- 明确答案和完整 JSON 合规分别统计；缺少 confidence 但答案明确时仍保留答案。",
            "- 备用解析只接受裸 A/B/C/D 或明确 final-answer 声明；解释中普通的 Option/Candidate 提及不会被当作答案，冲突声明标为不可确定。",
            "",
            "## 不确定性与限制",
            "",
            "- 每格只有 10 道题，置信区间按题目聚类重采样，同题三次响应整体保留。",
            "- 组合之间不是逐题配对版本，因素差异可能仍包含属性、场景和模板构成差异。",
            "- 后端接收 seed，但不能据此宣称采样在所有软硬件状态下完全可复现。",
            "- 本轮没有任何辩论轨迹，因此错误选项的约束违反不是“辩论引起的漂移”。",
            "",
            "## 扩充建议",
            "",
            f"**{decision}**",
            "",
            recommendation,
            "",
            "若后续扩充，应使用与 `attr_v4_1_*` 不冲突的新 ID 区间，并保存规范化题目内容哈希去重；每格新增 20 题作为独立验证集，不用新增题回填或优化本轮统计。",
            "",
            f"Qwen 接近全对：{'是' if near_perfect.get('qwen', False) else '否'}。"
            f"本轮兼具基本能力和自然分歧的模型-组合行数为 {len(informative_rows)}/36。",
        ]
    )
    decision_summary = {
        "decision": decision,
        "recommendation": recommendation,
        "process_complete": process_complete,
        "qwen_near_perfect": near_perfect.get("qwen"),
        "informative_cell_model_rows": len(informative_rows),
        "informative_cell_model_rows_by_model": informative_by_model,
        "correct_wrong_coexist_item_model_count": coexist_total,
        "correct_wrong_coexist_by_model": coexist_by_model,
        "factor_support": factor_support,
        "overall_by_model": overall,
        "within_model_behavior": behavior,
    }
    return "\n".join(lines) + "\n", decision_summary
