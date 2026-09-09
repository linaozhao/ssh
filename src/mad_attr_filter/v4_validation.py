"""Independent validation for factorized v4 attribute-filtering items."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

from mad_attr_filter.attributes import ATTRIBUTE_BY_KEY
from mad_attr_filter.difficulty import (
    DifficultyConfig,
    DifficultyConfigError,
    all_difficulty_configs,
    validate_distractor_signatures,
)
from mad_attr_filter.matrix import compute_constraint_matrix, compute_violation_signatures
from mad_attr_filter.models import ConstraintSpec
from mad_attr_filter.non_target_facts import NON_TARGET_FACT_BY_KEY
from mad_attr_filter.semantic_validator import SemanticValidationError, validate_semantics


class V4ValidationError(ValueError):
    """Raised when a v4 item violates its formal or factorized contract."""


def _constraints_from_item(item: Mapping[str, Any]) -> list[ConstraintSpec]:
    raw_constraints = item.get("constraints")
    if not isinstance(raw_constraints, Sequence) or isinstance(raw_constraints, (str, bytes)):
        raise V4ValidationError("constraints must be a list")
    constraints: list[ConstraintSpec] = []
    for raw_constraint in raw_constraints:
        if not isinstance(raw_constraint, Mapping):
            raise V4ValidationError("Every constraint must be an object")
        try:
            constraints.append(
                ConstraintSpec(
                    id=str(raw_constraint["id"]),
                    attribute=str(raw_constraint["attribute"]),
                    required_value=bool(raw_constraint["required_value"]),
                    type=str(raw_constraint["type"]),
                    natural_language=str(raw_constraint["natural_language"]),
                )
            )
        except KeyError as exc:
            raise V4ValidationError(f"Constraint is missing field: {exc.args[0]}") from exc
    return constraints


def _validate_generation_metadata(
    item: Mapping[str, Any],
    expected_warnings: Sequence[str],
) -> None:
    metadata = item.get("generation_metadata")
    if not isinstance(metadata, Mapping):
        raise V4ValidationError("generation_metadata must be an object")
    if metadata.get("generator_version") != "4.1":
        raise V4ValidationError("generation_metadata.generator_version must be '4.1'")
    if not isinstance(metadata.get("seed"), int) or isinstance(metadata.get("seed"), bool):
        raise V4ValidationError("generation_metadata.seed must be an integer")
    if not str(metadata.get("template_id", "")).strip():
        raise V4ValidationError("generation_metadata.template_id must be nonempty")
    warnings = metadata.get("warnings")
    if not isinstance(warnings, Sequence) or isinstance(warnings, (str, bytes)):
        raise V4ValidationError("generation_metadata.warnings must be a list")
    if [str(warning) for warning in warnings] != list(expected_warnings):
        raise V4ValidationError("generation_metadata.warnings does not match factor validation")


def _validate_non_target_facts(
    item: Mapping[str, Any],
    config: DifficultyConfig,
    candidate_attributes: Mapping[str, Mapping[str, bool]],
    constraints: list[ConstraintSpec],
    recomputed_matrix: Mapping[str, Mapping[str, bool]],
) -> None:
    entities = item["entities"]
    options = item["options"]
    augmented_attributes: dict[str, dict[str, bool]] = {}

    for label in ("A", "B", "C", "D"):
        entity = entities[label]
        if "irrelevant_facts" in entity:
            raise V4ValidationError(
                f"Entity {label} uses deprecated irrelevant_facts instead of non_target_facts"
            )
        raw_facts = entity.get("non_target_facts")
        if not isinstance(raw_facts, Sequence) or isinstance(raw_facts, (str, bytes)):
            raise V4ValidationError(f"Entity {label} must contain a non_target_facts list")
        facts = list(raw_facts)
        if config.information_load == "IL1_low" and facts:
            raise V4ValidationError(f"IL1_low entity {label} contains non-target facts")
        if config.information_load == "IL2_high" and len(facts) != 2:
            raise V4ValidationError(f"IL2_high entity {label} must contain exactly two non-target facts")

        extra_values: dict[str, bool] = {}
        seen_keys: set[str] = set()
        option_text = str(options[label])
        for fact in facts:
            if not isinstance(fact, Mapping):
                raise V4ValidationError(f"Entity {label} has a malformed non-target fact")
            key = str(fact.get("key", ""))
            category = str(fact.get("category", ""))
            text = str(fact.get("text", ""))
            if not key or not text:
                raise V4ValidationError(f"Entity {label} has an empty non-target fact")
            if key in ATTRIBUTE_BY_KEY:
                raise V4ValidationError(f"Non-target fact {key} overlaps the formal attribute pool")
            if key not in NON_TARGET_FACT_BY_KEY:
                raise V4ValidationError(f"Unknown non-target fact: {key}")
            fact_spec = NON_TARGET_FACT_BY_KEY[key]
            if str(item.get("scenario")) not in fact_spec.compatible_scenarios:
                raise V4ValidationError(
                    f"Non-target fact {key} is not domain-relevant to {item.get('scenario')}"
                )
            if category != fact_spec.category:
                raise V4ValidationError(f"Non-target fact {key} has incorrect category")
            if key in seen_keys:
                raise V4ValidationError(f"Entity {label} repeats non-target fact {key}")
            name = str(entity.get("name", ""))
            allowed_texts = {
                template.format(name=name) for template in fact_spec.templates
            }
            if text not in allowed_texts:
                raise V4ValidationError(f"Non-target fact {key} has invalid realization")
            if text not in option_text:
                raise V4ValidationError(f"Entity {label} option omits non-target fact text: {text}")
            seen_keys.add(key)
            extra_values[key] = True
        lowered_option = option_text.lower()
        if "as background information" in lowered_option or "irrelevant" in lowered_option:
            raise V4ValidationError(f"Entity {label} explicitly marks non-target facts as irrelevant")
        augmented_attributes[label] = {**candidate_attributes[label], **extra_values}

    augmented_matrix = compute_constraint_matrix(augmented_attributes, constraints)
    if augmented_matrix != recomputed_matrix:
        raise V4ValidationError("Non-target facts changed constraint evaluation")


def validate_v4_item(item: Mapping[str, Any]) -> None:
    """Validate one v4 item without applying any v3 difficulty assumptions."""
    labels = ("A", "B", "C", "D")
    if item.get("generator_version") != "4.1":
        raise V4ValidationError("generator_version must be '4.1'")
    if item.get("task_family") != "multi_constraint" or item.get("task_type") != "attribute_filter":
        raise V4ValidationError("Unexpected task family or task type")
    if item.get("language") != "en":
        raise V4ValidationError("v4 items must use language='en'")

    options = item.get("options")
    entities = item.get("entities")
    if not isinstance(options, Mapping) or set(options) != set(labels):
        raise V4ValidationError("Item must contain exactly four options A-D")
    if not isinstance(entities, Mapping) or set(entities) != set(labels):
        raise V4ValidationError("Item must contain exactly four entities A-D")

    raw_factors = item.get("difficulty_factors")
    if not isinstance(raw_factors, Mapping):
        raise V4ValidationError("difficulty_factors must be an object")
    try:
        config = DifficultyConfig.from_mapping(raw_factors)
    except DifficultyConfigError as exc:
        raise V4ValidationError(f"Invalid difficulty factors: {exc}") from exc

    constraints = _constraints_from_item(item)
    if len(constraints) != config.num_constraints:
        raise V4ValidationError(
            f"Expected {config.num_constraints} constraints for {config.constraint_load}, got {len(constraints)}"
        )
    constraint_ids = [constraint.id for constraint in constraints]
    constraint_attributes = [constraint.attribute for constraint in constraints]
    if constraint_ids != [f"C{index}" for index in range(1, len(constraints) + 1)]:
        raise V4ValidationError("Constraint IDs must be consecutive and ordered")
    if len(set(constraint_attributes)) != len(constraint_attributes):
        raise V4ValidationError("Constrained attributes must be unique")

    names = [str(entities[label].get("name", "")) for label in labels]
    if any(not name for name in names) or len(set(names)) != 4:
        raise V4ValidationError("Candidate names must be nonempty and unique")

    candidate_attributes: dict[str, dict[str, bool]] = {}
    expected_signatures: dict[str, list[str]] = {}
    for label in labels:
        entity = entities[label]
        raw_attributes = entity.get("attributes")
        if not isinstance(raw_attributes, Mapping):
            raise V4ValidationError(f"Entity {label} is missing attributes")
        candidate_attributes[label] = {
            str(key): bool(value) for key, value in raw_attributes.items()
        }
        if any(attribute not in candidate_attributes[label] for attribute in constraint_attributes):
            raise V4ValidationError(f"Entity {label} is missing a constrained attribute")
        raw_expected = entity.get("expected_violation_signature")
        if not isinstance(raw_expected, Sequence) or isinstance(raw_expected, (str, bytes)):
            raise V4ValidationError(f"Entity {label} has an invalid expected signature")
        expected_signatures[label] = [str(value) for value in raw_expected]

    recomputed_matrix = compute_constraint_matrix(candidate_attributes, constraints)
    recomputed_signatures = compute_violation_signatures(recomputed_matrix)
    if item.get("option_constraint_matrix") != recomputed_matrix:
        raise V4ValidationError("Stored option_constraint_matrix does not match recomputation")
    if item.get("option_violation_signature") != recomputed_signatures:
        raise V4ValidationError("Stored option_violation_signature does not match recomputation")
    if expected_signatures != recomputed_signatures:
        raise V4ValidationError("Expected violation signatures do not match recomputation")

    valid_labels = [label for label in labels if not recomputed_signatures[label]]
    if len(valid_labels) != 1:
        raise V4ValidationError(f"Expected exactly one Gold candidate, got {valid_labels}")
    gold_label = valid_labels[0]
    if item.get("gold_answer") != gold_label:
        raise V4ValidationError("gold_answer does not identify the unique satisfying candidate")
    marked_gold = [label for label in labels if entities[label].get("is_gold") is True]
    if marked_gold != [gold_label]:
        raise V4ValidationError("Entity Gold marker does not match gold_answer")

    wrong_signatures = [
        recomputed_signatures[label] for label in labels if label != gold_label
    ]
    try:
        signature_warnings = validate_distractor_signatures(config, wrong_signatures)
    except DifficultyConfigError as exc:
        raise V4ValidationError(f"Distractor pattern does not match factors: {exc}") from exc

    _validate_non_target_facts(
        item,
        config,
        candidate_attributes,
        constraints,
        recomputed_matrix,
    )
    _validate_generation_metadata(item, signature_warnings)
    question = str(item.get("question", ""))
    if not question.strip() or any(str(options[label]) not in question for label in labels):
        raise V4ValidationError("Question must contain all complete option descriptions")
    try:
        validate_semantics(item)
    except SemanticValidationError as exc:
        raise V4ValidationError(f"Semantic validation failed: {exc}") from exc


def validate_v4_pool(
    items: Sequence[Mapping[str, Any]],
    *,
    expected_items_per_cell: int | None = None,
) -> dict[str, object]:
    """Validate a v4 pool and return its factor-distribution summary."""
    cell_counts: Counter[str] = Counter()
    gold_counts: Counter[str] = Counter()
    scenario_counts: Counter[str] = Counter()
    item_ids: set[str] = set()
    for index, item in enumerate(items, start=1):
        try:
            validate_v4_item(item)
        except V4ValidationError as exc:
            raise V4ValidationError(f"{item.get('item_id', f'item #{index}')}: {exc}") from exc
        item_id = str(item.get("item_id", ""))
        if not item_id or item_id in item_ids:
            raise V4ValidationError(f"Duplicate or empty item_id: {item_id}")
        item_ids.add(item_id)
        config = DifficultyConfig.from_mapping(item["difficulty_factors"])
        cell_counts[config.cell_id] += 1
        gold_counts[str(item["gold_answer"])] += 1
        scenario_counts[str(item["scenario"])] += 1

    if expected_items_per_cell is not None:
        if expected_items_per_cell < 1:
            raise V4ValidationError("expected_items_per_cell must be positive")
        expected_cells = {config.cell_id for config in all_difficulty_configs()}
        if set(cell_counts) != expected_cells:
            missing = sorted(expected_cells - set(cell_counts))
            extra = sorted(set(cell_counts) - expected_cells)
            raise V4ValidationError(f"Pool cells mismatch; missing={missing}, extra={extra}")
        wrong_counts = {
            cell_id: count
            for cell_id, count in cell_counts.items()
            if count != expected_items_per_cell
        }
        if wrong_counts:
            raise V4ValidationError(f"Unexpected per-cell counts: {wrong_counts}")

    return {
        "total_items": len(items),
        "validated_items": len(items),
        "validation_pass_rate": 1.0 if items else 0.0,
        "difficulty_cell_distribution": dict(sorted(cell_counts.items())),
        "gold_position_distribution": {
            label: gold_counts[label] for label in ("A", "B", "C", "D")
        },
        "scenario_distribution": dict(sorted(scenario_counts.items())),
    }
