"""Cell-level confound audit for the v4.1 factorized prototype."""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from statistics import mean
from typing import Any

from mad_attr_filter.attributes import ATTRIBUTE_BY_KEY
from mad_attr_filter.difficulty import (
    DifficultyConfig,
    DifficultyConfigError,
    all_difficulty_configs,
    far_violation_threshold,
    validate_distractor_signatures,
)
from mad_attr_filter.io import write_json
from mad_attr_filter.non_target_facts import NON_TARGET_FACT_BY_KEY
from mad_attr_filter.v4_validation import V4ValidationError, validate_v4_item

WORD_RE = re.compile(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)*")


def _word_count(text: object) -> int:
    return len(WORD_RE.findall(str(text)))


def _counter_payload(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): counter[key] for key in sorted(counter, key=str)}


def _required_value_payload(counter: Counter[bool]) -> dict[str, object]:
    total = counter[True] + counter[False]
    return {
        "required_true": counter[True],
        "required_false": counter[False],
        "required_true_ratio": round(counter[True] / total, 6) if total else 0.0,
        "required_false_ratio": round(counter[False] / total, 6) if total else 0.0,
    }


def _audit_il_item(item: Mapping[str, Any], config: DifficultyConfig) -> list[str]:
    errors: list[str] = []
    scenario = str(item.get("scenario"))
    entities = item.get("entities", {})
    expected_count = 0 if config.information_load == "IL1_low" else 2
    for label in ("A", "B", "C", "D"):
        entity = entities.get(label, {})
        facts = entity.get("non_target_facts", [])
        if len(facts) != expected_count:
            errors.append(
                f"{label}: expected {expected_count} non-target facts, got {len(facts)}"
            )
            continue
        for fact in facts:
            key = str(fact.get("key", ""))
            if key in ATTRIBUTE_BY_KEY:
                errors.append(f"{label}: non-target key {key} overlaps ATTRIBUTE_POOL")
                continue
            spec = NON_TARGET_FACT_BY_KEY.get(key)
            if spec is None:
                errors.append(f"{label}: unknown non-target key {key}")
            elif scenario not in spec.compatible_scenarios:
                errors.append(f"{label}: {key} is not compatible with {scenario}")
        option_text = str(item.get("options", {}).get(label, "")).lower()
        if "as background information" in option_text or "irrelevant" in option_text:
            errors.append(f"{label}: candidate text explicitly cues irrelevance")
    return errors


def _audit_cell(cell_items: Sequence[Mapping[str, Any]]) -> dict[str, object]:
    scenario_counter: Counter[str] = Counter()
    gold_counter: Counter[str] = Counter()
    attribute_counter: Counter[str] = Counter()
    required_value_counter: Counter[bool] = Counter()
    template_counter: Counter[str] = Counter()
    violation_count_counter: Counter[int] = Counter()
    question_lengths: list[int] = []
    option_lengths: list[int] = []
    ds_errors: list[dict[str, str]] = []
    il_errors: list[dict[str, str]] = []
    validation_errors: list[dict[str, str]] = []

    for item in cell_items:
        item_id = str(item.get("item_id"))
        config = DifficultyConfig.from_mapping(item["difficulty_factors"])
        scenario_counter[str(item.get("scenario"))] += 1
        gold_counter[str(item.get("gold_answer"))] += 1
        template_counter[str(item.get("generation_metadata", {}).get("template_id"))] += 1
        question_lengths.append(_word_count(item.get("question", "")))
        option_lengths.extend(
            _word_count(option) for option in item.get("options", {}).values()
        )
        for constraint in item.get("constraints", []):
            attribute_counter[str(constraint.get("attribute"))] += 1
            required_value_counter[bool(constraint.get("required_value"))] += 1

        wrong_signatures = [
            signature
            for label, signature in item.get("option_violation_signature", {}).items()
            if label != item.get("gold_answer")
        ]
        violation_count_counter.update(len(signature) for signature in wrong_signatures)
        try:
            validate_distractor_signatures(config, wrong_signatures)
        except DifficultyConfigError as exc:
            ds_errors.append({"item_id": item_id, "error": str(exc)})

        for error in _audit_il_item(item, config):
            il_errors.append({"item_id": item_id, "error": error})
        try:
            validate_v4_item(item)
        except V4ValidationError as exc:
            validation_errors.append({"item_id": item_id, "error": str(exc)})

    return {
        "num_items": len(cell_items),
        "scenario_distribution": _counter_payload(scenario_counter),
        "gold_position_distribution": {
            label: gold_counter[label] for label in ("A", "B", "C", "D")
        },
        "constraint_attribute_frequency": _counter_payload(attribute_counter),
        "required_value_distribution": _required_value_payload(required_value_counter),
        "average_question_length_words": round(mean(question_lengths), 3),
        "average_option_length_words": round(mean(option_lengths), 3),
        "template_frequency": _counter_payload(template_counter),
        "violation_count_distribution": _counter_payload(violation_count_counter),
        "ds_level_verification": {
            "passed": not ds_errors,
            "checked_items": len(cell_items),
            "failure_count": len(ds_errors),
            "failures": ds_errors,
        },
        "il_level_verification": {
            "passed": not il_errors,
            "checked_items": len(cell_items),
            "failure_count": len(il_errors),
            "failures": il_errors,
        },
        "full_item_validation": {
            "passed": not validation_errors,
            "failure_count": len(validation_errors),
            "failures": validation_errors,
        },
    }


def build_factor_audit(items: Sequence[Mapping[str, Any]]) -> dict[str, object]:
    """Build the full cell-level v4.1 factor audit."""
    items_by_cell: dict[str, list[Mapping[str, Any]]] = {
        config.cell_id: [] for config in all_difficulty_configs()
    }
    for item in items:
        config = DifficultyConfig.from_mapping(item["difficulty_factors"])
        items_by_cell.setdefault(config.cell_id, []).append(item)

    cells = {
        cell_id: _audit_cell(cell_items)
        for cell_id, cell_items in sorted(items_by_cell.items())
    }
    cell_sizes = [int(cell["num_items"]) for cell in cells.values()]
    scenario_spreads = [
        max(cell["scenario_distribution"].values())
        - min(cell["scenario_distribution"].values())
        for cell in cells.values()
        if cell["scenario_distribution"]
    ]
    gold_spreads = [
        max(cell["gold_position_distribution"].values())
        - min(cell["gold_position_distribution"].values())
        for cell in cells.values()
    ]
    template_diversities = [
        len(cell["template_frequency"]) for cell in cells.values()
    ]
    true_ratios = [
        float(cell["required_value_distribution"]["required_true_ratio"])
        for cell in cells.values()
        if cell["num_items"]
    ]

    scenario_counter = Counter(str(item.get("scenario")) for item in items)
    gold_counter = Counter(str(item.get("gold_answer")) for item in items)
    cl_counter = Counter(
        str(item["difficulty_factors"]["constraint_load"]) for item in items
    )
    ds_counter = Counter(
        str(item["difficulty_factors"]["distractor_similarity"]) for item in items
    )
    il_counter = Counter(
        str(item["difficulty_factors"]["information_load"]) for item in items
    )
    validation_failures = sum(
        int(cell["full_item_validation"]["failure_count"]) for cell in cells.values()
    )
    ds_failures = sum(
        int(cell["ds_level_verification"]["failure_count"]) for cell in cells.values()
    )
    il_failures = sum(
        int(cell["il_level_verification"]["failure_count"]) for cell in cells.values()
    )

    warnings: list[str] = []
    if true_ratios and max(true_ratios) - min(true_ratios) > 0.25:
        warnings.append(
            "Required-value ratios vary by more than 0.25 across cells; inspect attribute sampling."
        )
    checks = {
        "all_18_cells_present": len(cells) == 18 and all(cell_sizes),
        "equal_items_per_cell": len(set(cell_sizes)) == 1,
        "scenario_max_count_spread_per_cell": max(scenario_spreads, default=0),
        "scenario_balance_within_one": max(scenario_spreads, default=0) <= 1,
        "gold_position_max_count_spread_per_cell": max(gold_spreads, default=0),
        "gold_position_balance_within_one": max(gold_spreads, default=0) <= 1,
        "minimum_template_variants_per_cell": min(template_diversities, default=0),
        "all_ds_levels_verified": ds_failures == 0,
        "all_il_levels_verified": il_failures == 0,
        "all_items_fully_valid": validation_failures == 0,
    }
    no_obvious_confounding = all(
        (
            checks["all_18_cells_present"],
            checks["equal_items_per_cell"],
            checks["scenario_balance_within_one"],
            checks["gold_position_balance_within_one"],
            checks["minimum_template_variants_per_cell"] >= 3,
            checks["all_ds_levels_verified"],
            checks["all_il_levels_verified"],
            checks["all_items_fully_valid"],
        )
    ) and not warnings

    return {
        "audit_version": "4.1",
        "total_items": len(items),
        "num_difficulty_cells": len(cells),
        "overall_distribution": {
            "constraint_load": _counter_payload(cl_counter),
            "distractor_similarity": _counter_payload(ds_counter),
            "information_load": _counter_payload(il_counter),
            "scenario": _counter_payload(scenario_counter),
            "gold_position": {
                label: gold_counter[label] for label in ("A", "B", "C", "D")
            },
        },
        "ds1_thresholds": {
            "CL1": far_violation_threshold(3),
            "CL2": far_violation_threshold(5),
            "CL3": far_violation_threshold(7),
        },
        "confound_checks": checks,
        "no_obvious_confounding_detected": no_obvious_confounding,
        "warnings": warnings,
        "cells": cells,
    }


def write_factor_audit(path: str | Path, items: Sequence[Mapping[str, Any]]) -> dict[str, object]:
    """Build and write the v4.1 audit JSON."""
    payload = build_factor_audit(items)
    write_json(path, payload)
    return payload


def build_refinement_report(
    items: Sequence[Mapping[str, Any]],
    audit: Mapping[str, Any],
) -> str:
    """Build the required v4.1 refinement summary."""
    checks = audit["confound_checks"]
    distribution = audit["overall_distribution"]
    lines = [
        "# V4.1 Refinement Report",
        "",
        "## 1. Changes",
        "",
        "- Replaced the fixed DS1 threshold with `ceil(number_of_constraints / 2)`.",
        "- Replaced hobby noise and explicit background cues with scenario-compatible non-target work facts.",
        "- Added exact question-template IDs and a per-cell factor confound audit.",
        "- Kept v3 generation, Gold construction, matrix computation, and violation-signature computation unchanged.",
        "",
        "## 2. DS1 Definition",
        "",
        "DS1 distractors must each violate at least `ceil(k/2)` constraints. The thresholds are "
        "CL1=2, CL2=3, and CL3=4. Signatures are sampled without replacement whenever at least "
        "three valid subsets exist.",
        "",
        "## 3. IL2 Definition",
        "",
        "IL2 adds two domain-relevant non-target facts per candidate. These facts are compatible "
        "with the current scenario, use keys outside the formal `ATTRIBUTE_POOL`, appear naturally "
        "in candidate prose, and are excluded from Gold, matrix, and violation-signature evaluation.",
        "",
        "## 4. Prototype Generation",
        "",
        f"- Items: {len(items)}",
        f"- Cells: {audit['num_difficulty_cells']}",
        f"- Constraint load: `{distribution['constraint_load']}`",
        f"- Distractor similarity: `{distribution['distractor_similarity']}`",
        f"- Information load: `{distribution['information_load']}`",
        f"- Scenario: `{distribution['scenario']}`",
        f"- Gold position: `{distribution['gold_position']}`",
        "",
        "## 5. Audit Summary",
        "",
        f"- All 18 cells present: {checks['all_18_cells_present']}",
        f"- Equal cell sizes: {checks['equal_items_per_cell']}",
        f"- Scenario balance within one item per cell: {checks['scenario_balance_within_one']}",
        f"- Gold balance within one item per cell: {checks['gold_position_balance_within_one']}",
        f"- Minimum template variants per cell: {checks['minimum_template_variants_per_cell']}",
        f"- DS verification: {checks['all_ds_levels_verified']}",
        f"- IL verification: {checks['all_il_levels_verified']}",
        f"- Full validation: {checks['all_items_fully_valid']}",
        f"- No obvious factor confounding detected: {audit['no_obvious_confounding_detected']}",
        f"- Warnings: `{audit['warnings']}`",
        "",
        "## 6. Remaining Limitations",
        "",
        "- Factor levels remain generation controls, not empirically calibrated model difficulty.",
        "- Non-target facts are deterministic templates and may not distract all model families equally.",
        "- Constraint attributes are sampled randomly within scenario rules, so the audit reports residual frequency variation.",
        "- Question and option lengths intentionally differ across CL and IL levels; those are treatment effects, not balancing variables.",
        "- No model inference or MAD experiment was run.",
        "",
    ]
    return "\n".join(lines)


def write_refinement_report(
    path: str | Path,
    items: Sequence[Mapping[str, Any]],
    audit: Mapping[str, Any],
) -> None:
    """Write the required Markdown refinement report."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_refinement_report(items, audit), encoding="utf-8")
