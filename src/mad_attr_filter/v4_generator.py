"""Independent v4 generator with factorized difficulty controls."""

from __future__ import annotations

import random
from collections import Counter
from itertools import combinations
from typing import Any

from mad_attr_filter.attributes import ATTRIBUTE_POOL
from mad_attr_filter.difficulty import (
    DifficultyConfig,
    all_difficulty_configs,
    far_violation_threshold,
    validate_distractor_signatures,
)
from mad_attr_filter.generator import (
    LABELS,
    NAMES,
    GenerationError,
    _assign_labels,
    _candidate_from_signature,
    _gold_attributes,
    _sample_constraints,
)
from mad_attr_filter.non_target_facts import (
    render_non_target_fact_sentences,
    sample_non_target_facts,
)
from mad_attr_filter.matrix import compute_constraint_matrix, compute_violation_signatures
from mad_attr_filter.models import Candidate, ConstraintSpec, ScenarioSpec
from mad_attr_filter.scenarios import SCENARIOS, SCENARIO_BY_KEY
from mad_attr_filter.templates import QUESTION_ENDINGS, render_candidate
from mad_attr_filter.v4_validation import V4ValidationError, validate_v4_item, validate_v4_pool

GENERATOR_VERSION = "4.1"


def _sample_unique_signatures(
    constraint_ids: list[str],
    *,
    minimum_size: int,
    count: int,
    rng: random.Random,
) -> list[list[str]]:
    """Sample unique subsets while allowing repetition only when unavoidable."""
    candidates = [
        list(signature)
        for size in range(minimum_size, len(constraint_ids) + 1)
        for signature in combinations(constraint_ids, size)
    ]
    if not candidates:
        raise GenerationError("No feasible distractor signature exists")
    if len(candidates) >= count:
        return rng.sample(candidates, count)
    return [list(candidates[index % len(candidates)]) for index in range(count)]


def _v4_violation_signatures(
    constraint_ids: list[str],
    config: DifficultyConfig,
    rng: random.Random,
) -> list[list[str]]:
    """Generate three wrong-option signatures for one DS factor level."""
    num_constraints = len(constraint_ids)
    if num_constraints != config.num_constraints:
        raise GenerationError(
            f"Expected {config.num_constraints} constraint IDs, got {num_constraints}"
        )

    if config.distractor_similarity == "DS1_far":
        signatures = _sample_unique_signatures(
            constraint_ids,
            minimum_size=far_violation_threshold(num_constraints),
            count=3,
            rng=rng,
        )
    elif config.distractor_similarity == "DS2_medium":
        near = [rng.choice(constraint_ids)]
        obvious = _sample_unique_signatures(
            constraint_ids,
            minimum_size=2,
            count=2,
            rng=rng,
        )
        signatures = [near, *obvious]
    else:
        selected_ids = rng.sample(constraint_ids, 3)
        signatures = [[constraint_id] for constraint_id in selected_ids]

    rng.shuffle(signatures)
    return signatures


def _render_v4_options(
    candidates_by_label: dict[str, Candidate],
    constraints: list[ConstraintSpec],
    config: DifficultyConfig,
    scenario_key: str,
    rng: random.Random,
) -> tuple[dict[str, str], dict[str, dict[str, object]]]:
    """Render target facts and optional domain-relevant non-target facts."""
    options: dict[str, str] = {}
    entities: dict[str, dict[str, object]] = {}
    for label in LABELS:
        candidate = candidates_by_label[label]
        text, display_order, displayed_facts = render_candidate(
            candidate.name,
            constraints,
            candidate.attributes,
            rng,
        )
        non_target_facts = (
            sample_non_target_facts(candidate.name, scenario_key, rng, count=2)
            if config.information_load == "IL2_high"
            else []
        )
        non_target_text = render_non_target_fact_sentences(non_target_facts)
        if non_target_text:
            text = f"{text} {non_target_text}"
        options[label] = text
        entity = candidate.to_entity_dict()
        entity["display_order"] = display_order
        entity["displayed_facts"] = displayed_facts
        entity["non_target_facts"] = non_target_facts
        entities[label] = entity
    return options, entities


def _render_v4_question(
    scenario: ScenarioSpec,
    constraints: list[ConstraintSpec],
    options: dict[str, str],
    rng: random.Random,
    template_indices: tuple[int, int] | None,
) -> tuple[str, str]:
    """Render a v4.1 question and return the exact intro/ending template ID."""
    introductions = scenario.introduction_templates
    endings = QUESTION_ENDINGS[scenario.key]
    if template_indices is None:
        intro_index = rng.randrange(len(introductions))
        ending_index = rng.randrange(len(endings))
    else:
        intro_index, ending_index = template_indices
        if not 0 <= intro_index < len(introductions):
            raise GenerationError(f"Invalid introduction template index: {intro_index}")
        if not 0 <= ending_index < len(endings):
            raise GenerationError(f"Invalid ending template index: {ending_index}")

    constraint_lines = "\n".join(
        f"{index}. {constraint.natural_language}"
        for index, constraint in enumerate(constraints, start=1)
    )
    option_lines = "\n".join(
        f"{label}. {options[label]}" for label in LABELS
    )
    question = (
        f"{introductions[intro_index]}\n"
        "The selected person must satisfy all of the following requirements:\n\n"
        "Requirements:\n"
        f"{constraint_lines}\n\n"
        "Candidates:\n"
        f"{option_lines}\n\n"
        f"{endings[ending_index]}"
    )
    template_id = (
        f"{scenario.key}:intro_{intro_index + 1}:ending_{ending_index + 1}"
    )
    return question, template_id


def generate_v4_item(
    item_index: int,
    difficulty_config: DifficultyConfig,
    seed: int,
    *,
    gold_label: str | None = None,
    scenario_key: str | None = None,
    question_template_indices: tuple[int, int] | None = None,
) -> dict[str, Any]:
    """Generate and independently validate one English factorized v4.1 item."""
    rng = random.Random(seed)
    scenario = SCENARIO_BY_KEY[scenario_key] if scenario_key else rng.choice(SCENARIOS)
    constraints = _sample_constraints(scenario, difficulty_config.num_constraints, rng)
    gold_attributes = _gold_attributes(constraints, rng)
    names = rng.sample(list(NAMES), 4)
    gold_candidate = Candidate(
        name=names[0],
        attributes=gold_attributes,
        expected_violation_signature=[],
        is_gold=True,
    )
    signatures = _v4_violation_signatures(
        [constraint.id for constraint in constraints],
        difficulty_config,
        rng,
    )
    generation_warnings = validate_distractor_signatures(
        difficulty_config,
        signatures,
    )
    wrong_candidates = [
        _candidate_from_signature(name, gold_attributes, constraints, signature)
        for name, signature in zip(names[1:], signatures)
    ]
    candidates_by_label = _assign_labels(
        gold_candidate,
        wrong_candidates,
        rng,
        gold_label,
    )
    sorted_candidates = {label: candidates_by_label[label] for label in LABELS}
    candidate_attributes = {
        label: candidate.attributes for label, candidate in sorted_candidates.items()
    }
    matrix = compute_constraint_matrix(candidate_attributes, constraints)
    violation_signatures = compute_violation_signatures(matrix)
    options, entities = _render_v4_options(
        sorted_candidates,
        constraints,
        difficulty_config,
        scenario.key,
        rng,
    )
    question, template_id = _render_v4_question(
        scenario,
        constraints,
        options,
        rng,
        question_template_indices,
    )
    gold_answer = next(
        label for label, candidate in sorted_candidates.items() if candidate.is_gold
    )
    base_item_id = f"attr_v4_1_{item_index:06d}"
    item: dict[str, Any] = {
        "item_id": f"{base_item_id}_original",
        "base_item_id": base_item_id,
        "generator_version": GENERATOR_VERSION,
        "task_family": "multi_constraint",
        "task_type": "attribute_filter",
        "scenario": scenario.key,
        "language": "en",
        "variant_type": "original",
        "difficulty_factors": difficulty_config.to_dict(),
        "empirical_difficulty": None,
        "question": question,
        "options": options,
        "gold_answer": gold_answer,
        "constraints": [constraint.to_dict() for constraint in constraints],
        "entities": entities,
        "option_constraint_matrix": matrix,
        "option_violation_signature": violation_signatures,
        "generation_metadata": {
            "generator_version": GENERATOR_VERSION,
            "seed": seed,
            "template_id": template_id,
            "warnings": list(generation_warnings),
        },
        "metadata": {
            "seed": seed,
            "num_constraints": len(constraints),
            "formal_language": "boolean_attributes",
            "attribute_pool_size": len(ATTRIBUTE_POOL),
            "semantic_validation_passed": True,
            "difficulty_definition": "factorized_v4_1",
            "difficulty_cell": difficulty_config.cell_id,
            "constrained_attributes": [
                constraint.attribute for constraint in constraints
            ],
        },
    }
    validate_v4_item(item)
    return item


def generate_v4_pool(
    items_per_cell: int,
    *,
    global_seed: int = 42,
    max_retries_per_item: int = 100,
) -> tuple[list[dict[str, Any]], dict[str, object]]:
    """Generate a balanced full-factorial pool with a fixed count per cell."""
    if items_per_cell < 1:
        raise GenerationError("items_per_cell must be positive")
    if max_retries_per_item < 1:
        raise GenerationError("max_retries_per_item must be positive")

    rng = random.Random(global_seed)
    configs = all_difficulty_configs()
    items: list[dict[str, Any]] = []
    attempts = 0
    generation_failures = 0
    validation_failures = 0
    failure_reasons: Counter[str] = Counter()
    generation_warnings: Counter[str] = Counter()

    for cell_index, config in enumerate(configs):
        for within_cell_index in range(items_per_cell):
            item_index = len(items) + 1
            scenario = SCENARIOS[(cell_index + within_cell_index) % len(SCENARIOS)]
            scenario_index = next(
                index for index, value in enumerate(SCENARIOS) if value.key == scenario.key
            )
            gold_label = LABELS[(cell_index * items_per_cell + within_cell_index) % len(LABELS)]
            template_group = within_cell_index // len(SCENARIOS)
            question_template_indices = (
                (template_group + cell_index) % 3,
                (template_group + scenario_index + cell_index) % 3,
            )
            generated = False
            for _ in range(max_retries_per_item):
                attempts += 1
                item_seed = rng.randrange(1, 2**31 - 1)
                try:
                    item = generate_v4_item(
                        item_index,
                        config,
                        item_seed,
                        gold_label=gold_label,
                        scenario_key=scenario.key,
                        question_template_indices=question_template_indices,
                    )
                except GenerationError as exc:
                    generation_failures += 1
                    failure_reasons[str(exc)] += 1
                    continue
                except V4ValidationError as exc:
                    validation_failures += 1
                    failure_reasons[str(exc)] += 1
                    continue
                items.append(item)
                generation_warnings.update(item["generation_metadata"]["warnings"])
                generated = True
                break
            if not generated:
                raise GenerationError(
                    f"Failed to generate item {item_index} for {config.cell_id} after "
                    f"{max_retries_per_item} attempts"
                )

    validation_summary = validate_v4_pool(
        items,
        expected_items_per_cell=items_per_cell,
    )
    report: dict[str, object] = {
        "generator_version": GENERATOR_VERSION,
        "global_seed": global_seed,
        "num_cells": len(configs),
        "items_per_cell": items_per_cell,
        "requested_items": len(configs) * items_per_cell,
        "generated_items": len(items),
        "attempts": attempts,
        "retries": attempts - len(items),
        "generation_failures": generation_failures,
        "validation_failures": validation_failures,
        "failure_reasons": dict(sorted(failure_reasons.items())),
        "generation_warning_count": sum(generation_warnings.values()),
        "generation_warnings": dict(sorted(generation_warnings.items())),
        **validation_summary,
    }
    return items, report
