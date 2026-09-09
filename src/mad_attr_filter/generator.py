"""Deterministic generator for boolean attribute filtering samples."""

from __future__ import annotations

import random
from collections import Counter
from typing import Any

from mad_attr_filter.attributes import ATTRIBUTE_POOL, serialized_attribute_pool
from mad_attr_filter.matrix import compute_constraint_matrix, compute_violation_signatures
from mad_attr_filter.models import Candidate, ConstraintSpec, GenerationReport, ScenarioSpec
from mad_attr_filter.scenarios import SCENARIOS, SCENARIO_BY_KEY, is_allowed_by_scenario, serialized_scenarios
from mad_attr_filter.templates import render_candidate, render_constraint, render_question
from mad_attr_filter.validation import ValidationError, validate_sample

LABELS = ("A", "B", "C", "D")
OPTION_CLOSENESS_LEVELS = ("easy", "medium", "hard")
GENERATOR_VERSION = "3.0-en"

NAMES: tuple[str, ...] = (
    "Morgan",
    "Taylor",
    "Jordan",
    "Casey",
    "Riley",
    "Avery",
    "Quinn",
    "Cameron",
    "Drew",
    "Emerson",
    "Finley",
    "Harper",
    "Jamie",
    "Kendall",
    "Logan",
    "Parker",
    "Reese",
    "Rowan",
    "Sawyer",
    "Skyler",
    "Blair",
    "Devon",
    "Elliot",
    "Hayden",
    "Jules",
    "Lane",
    "Marley",
    "Noel",
    "Payton",
    "Robin",
    "Sage",
    "Tatum",
    "Wren",
    "Arden",
    "Briar",
    "Ellis",
    "Gray",
    "Indigo",
    "Kris",
    "Milan",
)


class GenerationError(RuntimeError):
    """Raised when a valid sample cannot be generated."""


def _constraint_type(required_value: bool) -> str:
    return "required_positive_attribute" if required_value else "required_negative_attribute"


def _structural_complexity(num_constraints: int) -> str:
    mapping = {3: "low", 4: "medium", 5: "high"}
    try:
        return mapping[num_constraints]
    except KeyError as exc:
        raise GenerationError(f"Unsupported number of constraints: {num_constraints}") from exc


def _feasible_constraint_counts(option_closeness: str) -> tuple[int, ...]:
    if option_closeness == "hard":
        return (3,)
    if option_closeness == "medium":
        return (3, 4)
    if option_closeness == "easy":
        return (3, 4, 5)
    raise GenerationError(f"Unknown option_closeness: {option_closeness}")


def _eligible_attributes(scenario: ScenarioSpec) -> list[Any]:
    return [
        attribute
        for attribute in ATTRIBUTE_POOL
        if attribute.eligible_for_constraint_sampling
        and scenario.key in attribute.compatible_scenarios
        and is_allowed_by_scenario(attribute.key, attribute.category, scenario.key)
    ]


def _sample_constraints(scenario: ScenarioSpec, num_constraints: int, rng: random.Random) -> list[ConstraintSpec]:
    attributes = _eligible_attributes(scenario)
    if len(attributes) < num_constraints:
        raise GenerationError(f"Scenario {scenario.key} has only {len(attributes)} eligible attributes")
    sampled_attributes = rng.sample(attributes, num_constraints)
    values: dict[str, bool] = {}
    for attribute in sampled_attributes:
        allowed_values = list(attribute.allowed_required_values)
        if not allowed_values:
            raise GenerationError(f"No semantically valid value left for {attribute.key}")
        values[attribute.key] = rng.choice(allowed_values)

    constraints: list[ConstraintSpec] = []
    for index, attribute in enumerate(sampled_attributes, start=1):
        required_value = values[attribute.key]
        constraints.append(
            ConstraintSpec(
                id=f"C{index}",
                attribute=attribute.key,
                required_value=required_value,
                type=_constraint_type(required_value),
                natural_language=render_constraint(attribute.key, required_value, rng),
            )
        )
    return constraints


def _gold_attributes(constraints: list[ConstraintSpec], rng: random.Random) -> dict[str, bool]:
    attributes = {attribute.key: rng.choice((True, False)) for attribute in ATTRIBUTE_POOL}
    for constraint in constraints:
        attributes[constraint.attribute] = constraint.required_value
    return attributes


def _fallback_simple_signatures(ids: list[str]) -> list[list[str]]:
    first = ids[:2]
    if len(ids) == 3:
        second = [ids[1], ids[2]]
        third = [ids[0], ids[2]]
    else:
        second = ids[2:4]
        covered = set(first) | set(second)
        third = [constraint_id for constraint_id in ids if constraint_id not in covered]
        for constraint_id in ids:
            if len(third) >= 2:
                break
            if constraint_id not in third:
                third.append(constraint_id)
    return [first, second, third]


def _sample_simple_signatures(ids: list[str], rng: random.Random) -> list[list[str]]:
    target = set(ids)
    for _ in range(100):
        first = sorted(rng.sample(ids, 2), key=ids.index)
        second = sorted(rng.sample(ids, 2), key=ids.index)
        third_size = rng.randint(2, len(ids))
        third = sorted(rng.sample(ids, third_size), key=ids.index)
        signatures = [first, second, third]
        if len({tuple(signature) for signature in signatures}) != 3:
            continue
        if set().union(*(set(signature) for signature in signatures)) == target:
            return signatures
    return _fallback_simple_signatures(ids)


def _violation_signatures(
    constraints: list[ConstraintSpec],
    option_closeness: str,
    rng: random.Random,
) -> list[list[str]]:
    ids = [constraint.id for constraint in constraints]
    rng.shuffle(ids)
    if option_closeness == "hard":
        if len(ids) != 3:
            raise GenerationError("Hard option_closeness requires exactly 3 constraints")
        return [[ids[0]], [ids[1]], [ids[2]]]
    if option_closeness == "medium":
        if len(ids) == 3:
            return [[ids[0]], [ids[1]], sorted([ids[2], ids[0]], key=ids.index)]
        if len(ids) == 4:
            return [[ids[0]], [ids[1]], [ids[2], ids[3]]]
        raise GenerationError("Medium option_closeness requires 3 or 4 constraints")
    if option_closeness == "easy":
        return _sample_simple_signatures(ids, rng)
    raise GenerationError(f"Unknown option_closeness: {option_closeness}")


def _candidate_from_signature(
    name: str,
    gold_attributes: dict[str, bool],
    constraints: list[ConstraintSpec],
    signature: list[str],
) -> Candidate:
    constraint_by_id = {constraint.id: constraint for constraint in constraints}
    attributes = dict(gold_attributes)
    for constraint_id in signature:
        constraint = constraint_by_id[constraint_id]
        attributes[constraint.attribute] = not constraint.required_value
    sorted_signature = [constraint.id for constraint in constraints if constraint.id in set(signature)]
    return Candidate(
        name=name,
        attributes=attributes,
        expected_violation_signature=sorted_signature,
        is_gold=False,
    )


def _assign_labels(
    gold_candidate: Candidate,
    wrong_candidates: list[Candidate],
    rng: random.Random,
    gold_label: str | None,
) -> dict[str, Candidate]:
    if gold_label is not None and gold_label not in LABELS:
        raise GenerationError(f"Invalid gold label: {gold_label}")

    shuffled_wrongs = list(wrong_candidates)
    rng.shuffle(shuffled_wrongs)
    if gold_label is None:
        candidates = [gold_candidate, *shuffled_wrongs]
        labels = list(LABELS)
        rng.shuffle(labels)
        return {label: candidate for label, candidate in zip(labels, candidates)}

    assigned: dict[str, Candidate] = {gold_label: gold_candidate}
    wrong_labels = [label for label in LABELS if label != gold_label]
    rng.shuffle(wrong_labels)
    for label, candidate in zip(wrong_labels, shuffled_wrongs):
        assigned[label] = candidate
    return assigned


def generate_item(
    item_index: int,
    option_closeness: str,
    seed: int,
    *,
    gold_label: str | None = None,
    num_constraints: int | None = None,
    scenario_key: str | None = None,
) -> dict[str, Any]:
    """Generate one JSON-ready English v3 sample and validate it before returning."""
    rng = random.Random(seed)
    if num_constraints is None:
        num_constraints = rng.choice(_feasible_constraint_counts(option_closeness))
    if num_constraints not in _feasible_constraint_counts(option_closeness):
        raise GenerationError(f"{num_constraints} constraints is not feasible for {option_closeness}")
    scenario = SCENARIO_BY_KEY[scenario_key] if scenario_key else rng.choice(SCENARIOS)
    constraints = _sample_constraints(scenario, num_constraints, rng)
    gold_attributes = _gold_attributes(constraints, rng)
    names = rng.sample(list(NAMES), 4)
    gold_candidate = Candidate(
        name=names[0],
        attributes=gold_attributes,
        expected_violation_signature=[],
        is_gold=True,
    )
    signatures = _violation_signatures(constraints, option_closeness, rng)
    wrong_candidates = [
        _candidate_from_signature(name, gold_attributes, constraints, signature)
        for name, signature in zip(names[1:], signatures)
    ]
    candidates_by_label = _assign_labels(gold_candidate, wrong_candidates, rng, gold_label)
    sorted_candidates = {label: candidates_by_label[label] for label in LABELS}
    candidate_attributes = {label: candidate.attributes for label, candidate in sorted_candidates.items()}
    matrix = compute_constraint_matrix(candidate_attributes, constraints)
    violation_signatures = compute_violation_signatures(matrix)

    options: dict[str, str] = {}
    entities: dict[str, dict[str, object]] = {}
    for label, candidate in sorted_candidates.items():
        text, display_order, displayed_facts = render_candidate(candidate.name, constraints, candidate.attributes, rng)
        options[label] = text
        entity = candidate.to_entity_dict()
        entity["display_order"] = display_order
        entity["displayed_facts"] = displayed_facts
        entities[label] = entity

    gold_answer = next(label for label, candidate in sorted_candidates.items() if candidate.is_gold)
    base_item_id = f"attr_en_{item_index:06d}"
    sample: dict[str, Any] = {
        "item_id": f"{base_item_id}_original",
        "base_item_id": base_item_id,
        "generator_version": GENERATOR_VERSION,
        "task_family": "multi_constraint",
        "task_type": "attribute_filter",
        "scenario": scenario.key,
        "language": "en",
        "variant_type": "original",
        "option_closeness": option_closeness,
        "structural_complexity": _structural_complexity(len(constraints)),
        "empirical_difficulty": None,
        "question": render_question(scenario, constraints, options, rng),
        "options": options,
        "gold_answer": gold_answer,
        "constraints": [constraint.to_dict() for constraint in constraints],
        "entities": entities,
        "option_constraint_matrix": matrix,
        "option_violation_signature": violation_signatures,
        "metadata": {
            "seed": seed,
            "num_constraints": len(constraints),
            "formal_language": "boolean_attributes",
            "attribute_pool_size": len(ATTRIBUTE_POOL),
            "semantic_validation_passed": True,
            "difficulty_definition": "option_closeness_only",
            "constrained_attributes": [constraint.attribute for constraint in constraints],
            "available_scenarios": [scenario.key for scenario in SCENARIOS],
        },
    }
    validate_sample(sample)
    return sample


def _balanced_gold_labels(total_items: int, rng: random.Random) -> list[str]:
    base = total_items // 4
    labels: list[str] = []
    for label in LABELS:
        labels.extend([label] * base)
    remaining = total_items - len(labels)
    extras = list(LABELS)
    rng.shuffle(extras)
    labels.extend(extras[:remaining])
    rng.shuffle(labels)
    return labels


def _expand_counts(counts: dict[Any, int], ordered_keys: tuple[Any, ...]) -> list[Any]:
    unknown = set(counts) - set(ordered_keys)
    if unknown:
        raise GenerationError(f"Unknown schedule keys: {sorted(unknown)}")
    schedule: list[Any] = []
    for key in ordered_keys:
        count = int(counts.get(key, 0))
        if count < 0:
            raise GenerationError(f"Negative count for {key}: {count}")
        schedule.extend([key] * count)
    return schedule


def _default_constraint_counts(option_closeness_counts: dict[str, int]) -> dict[int, int]:
    total = sum(option_closeness_counts.values())
    target_high = round(total * 0.2)
    target_low = round(total * 0.4)
    hard = option_closeness_counts.get("hard", 0)
    easy = option_closeness_counts.get("easy", 0)
    medium = option_closeness_counts.get("medium", 0)
    high = min(easy, target_high)
    low = max(hard, target_low)
    medium_count = total - high - low
    if medium_count < 0:
        raise GenerationError("Cannot derive feasible default constraint counts")
    if low - hard > medium:
        low = hard + medium
        medium_count = total - high - low
    return {3: low, 4: medium_count, 5: high}


def _pair_closeness_with_constraint_counts(
    option_closeness_counts: dict[str, int],
    constraint_count_counts: dict[int, int],
    rng: random.Random,
) -> list[tuple[str, int]]:
    remaining = Counter({int(key): int(value) for key, value in constraint_count_counts.items()})
    pairs: list[tuple[str, int]] = []

    hard_count = int(option_closeness_counts.get("hard", 0))
    if remaining[3] < hard_count:
        raise GenerationError("Hard items require more 3-constraint slots than available")
    for _ in range(hard_count):
        pairs.append(("hard", 3))
        remaining[3] -= 1

    easy_count = int(option_closeness_counts.get("easy", 0))
    for _ in range(easy_count):
        chosen = next((count for count in (5, 4, 3) if remaining[count] > 0), None)
        if chosen is None:
            raise GenerationError("No feasible constraint-count slot for easy item")
        pairs.append(("easy", chosen))
        remaining[chosen] -= 1

    medium_count = int(option_closeness_counts.get("medium", 0))
    for _ in range(medium_count):
        chosen = 4 if remaining[4] > 0 else 3
        if remaining[chosen] <= 0:
            raise GenerationError("No feasible constraint-count slot for medium item")
        pairs.append(("medium", chosen))
        remaining[chosen] -= 1

    if sum(remaining.values()) != 0:
        raise GenerationError(f"Unused constraint-count slots remain: {dict(remaining)}")
    rng.shuffle(pairs)
    return pairs


def _default_scenario_counts(total_items: int) -> dict[str, int]:
    base = total_items // len(SCENARIOS)
    counts = {scenario.key: base for scenario in SCENARIOS}
    for scenario in SCENARIOS[: total_items - base * len(SCENARIOS)]:
        counts[scenario.key] += 1
    return counts


def _scenario_schedule(scenario_counts: dict[str, int], rng: random.Random) -> list[str]:
    schedule = _expand_counts(scenario_counts, tuple(scenario.key for scenario in SCENARIOS))
    rng.shuffle(schedule)
    return [str(item) for item in schedule]


def generate_dataset(
    option_closeness_counts: dict[str, int],
    *,
    global_seed: int = 42,
    max_retries_per_item: int = 1000,
    balanced_gold: bool = True,
    constraint_count_counts: dict[int, int] | None = None,
    scenario_counts: dict[str, int] | None = None,
) -> tuple[list[dict[str, Any]], GenerationReport]:
    """Generate a validated v3 dataset with exact option-closeness counts."""
    rng = random.Random(global_seed)
    total_items = sum(int(value) for value in option_closeness_counts.values())
    if constraint_count_counts is None:
        constraint_count_counts = _default_constraint_counts(option_closeness_counts)
    if sum(int(value) for value in constraint_count_counts.values()) != total_items:
        raise GenerationError("constraint_count_counts must sum to total item count")
    if scenario_counts is None:
        scenario_counts = _default_scenario_counts(total_items)
    if sum(int(value) for value in scenario_counts.values()) != total_items:
        raise GenerationError("scenario_counts must sum to total item count")

    pairs = _pair_closeness_with_constraint_counts(option_closeness_counts, constraint_count_counts, rng)
    scenarios = _scenario_schedule(scenario_counts, rng)
    gold_labels = _balanced_gold_labels(total_items, rng) if balanced_gold else [None] * total_items
    samples: list[dict[str, Any]] = []
    attempts = 0
    generation_failures = 0
    validation_failures = 0
    semantic_validation_failures = 0
    invalid_polarity_failures = 0
    scenario_compatibility_failures = 0
    failure_reasons: Counter[str] = Counter()

    for item_index, ((option_closeness, num_constraints), scenario_key, gold_label) in enumerate(
        zip(pairs, scenarios, gold_labels),
        start=1,
    ):
        item_generated = False
        for _ in range(max_retries_per_item):
            attempts += 1
            item_seed = rng.randrange(1, 2**31 - 1)
            try:
                sample = generate_item(
                    item_index,
                    option_closeness,
                    item_seed,
                    gold_label=gold_label,
                    num_constraints=num_constraints,
                    scenario_key=scenario_key,
                )
            except GenerationError as exc:
                generation_failures += 1
                failure_reasons[type(exc).__name__] += 1
                continue
            except ValidationError as exc:
                validation_failures += 1
                message = str(exc)
                if "polarity" in message or "forbidden value" in message or "requires positive" in message:
                    invalid_polarity_failures += 1
                if "compatible" in message or "scenario" in message:
                    scenario_compatibility_failures += 1
                if "Semantic" in message or "natural language" in message or "display" in message:
                    semantic_validation_failures += 1
                failure_reasons[message.split(":", 1)[0]] += 1
                continue
            samples.append(sample)
            item_generated = True
            break
        if not item_generated:
            raise GenerationError(
                f"Failed to generate item {item_index} after {max_retries_per_item} retries"
            )

    report = GenerationReport(
        requested_items=total_items,
        generated_items=len(samples),
        attempts=attempts,
        retries=attempts - len(samples),
        generation_failures=generation_failures,
        validation_failures=validation_failures,
        semantic_validation_failures=semantic_validation_failures,
        invalid_polarity_failures=invalid_polarity_failures,
        scenario_compatibility_failures=scenario_compatibility_failures,
        failure_reasons=dict(failure_reasons),
    )
    return samples, report


def default_pilot_counts() -> dict[str, int]:
    """Return the requested 100-item pilot option-closeness distribution."""
    return {"easy": 20, "medium": 60, "hard": 20}


def default_pilot_constraint_counts() -> dict[int, int]:
    """Return the requested 100-item pilot structural complexity distribution."""
    return {3: 40, 4: 40, 5: 20}


def default_pilot_scenario_counts() -> dict[str, int]:
    """Return a near-balanced 100-item scenario distribution."""
    return {"expert_recruitment": 34, "project_assignment": 33, "availability_selection": 33}


def attribute_pool_payload() -> list[dict[str, object]]:
    """Expose the formal attribute pool for metadata or downstream tools."""
    return serialized_attribute_pool()


def scenario_payload() -> list[dict[str, object]]:
    """Expose scenario definitions for metadata or downstream tools."""
    return serialized_scenarios()
