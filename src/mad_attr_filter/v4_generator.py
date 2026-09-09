"""Independent v4 generator with factorized difficulty controls."""

from __future__ import annotations

import random
from collections import Counter
from itertools import combinations
from typing import Any

from mad_attr_filter.attributes import ATTRIBUTE_POOL
from mad_attr_filter.difficulty import DifficultyConfig, all_difficulty_configs
from mad_attr_filter.generator import (
    LABELS,
    NAMES,
    GenerationError,
    _assign_labels,
    _candidate_from_signature,
    _gold_attributes,
    _sample_constraints,
)
from mad_attr_filter.irrelevant_facts import (
    render_irrelevant_fact_sentence,
    sample_irrelevant_facts,
)
from mad_attr_filter.matrix import compute_constraint_matrix, compute_violation_signatures
from mad_attr_filter.models import Candidate
from mad_attr_filter.scenarios import SCENARIOS, SCENARIO_BY_KEY
from mad_attr_filter.templates import render_candidate, render_question
from mad_attr_filter.v4_validation import V4ValidationError, validate_v4_item, validate_v4_pool

GENERATOR_VERSION = "4.0"
TEMPLATE_ID = "factorized_english_v4_01"


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
            minimum_size=3,
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
    constraints: list[Any],
    config: DifficultyConfig,
    rng: random.Random,
) -> tuple[dict[str, str], dict[str, dict[str, object]]]:
    """Render relevant facts and optional non-evaluative background facts."""
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
        irrelevant_facts = (
            sample_irrelevant_facts(candidate.name, rng, count=2)
            if config.information_load == "IL2_high"
            else []
        )
        background_sentence = render_irrelevant_fact_sentence(irrelevant_facts)
        if background_sentence:
            text = f"{text} {background_sentence}"
        options[label] = text
        entity = candidate.to_entity_dict()
        entity["display_order"] = display_order
        entity["displayed_facts"] = displayed_facts
        entity["irrelevant_facts"] = irrelevant_facts
        entities[label] = entity
    return options, entities


def generate_v4_item(
    item_index: int,
    difficulty_config: DifficultyConfig,
    seed: int,
    *,
    gold_label: str | None = None,
    scenario_key: str | None = None,
) -> dict[str, Any]:
    """Generate and independently validate one English factorized v4 item."""
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
        rng,
    )
    gold_answer = next(
        label for label, candidate in sorted_candidates.items() if candidate.is_gold
    )
    base_item_id = f"attr_v4_{item_index:06d}"
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
        "question": render_question(scenario, constraints, options, rng),
        "options": options,
        "gold_answer": gold_answer,
        "constraints": [constraint.to_dict() for constraint in constraints],
        "entities": entities,
        "option_constraint_matrix": matrix,
        "option_violation_signature": violation_signatures,
        "generation_metadata": {
            "generator_version": GENERATOR_VERSION,
            "seed": seed,
            "template_id": TEMPLATE_ID,
        },
        "metadata": {
            "seed": seed,
            "num_constraints": len(constraints),
            "formal_language": "boolean_attributes",
            "attribute_pool_size": len(ATTRIBUTE_POOL),
            "semantic_validation_passed": True,
            "difficulty_definition": "factorized_v4",
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

    for cell_index, config in enumerate(configs):
        for within_cell_index in range(items_per_cell):
            item_index = len(items) + 1
            scenario = SCENARIOS[(cell_index + within_cell_index) % len(SCENARIOS)]
            gold_label = LABELS[(cell_index * items_per_cell + within_cell_index) % len(LABELS)]
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
        **validation_summary,
    }
    return items, report
