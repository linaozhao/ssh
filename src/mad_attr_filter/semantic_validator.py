"""Semantic validation for English v3 attribute-filtering samples."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from mad_attr_filter.attributes import (
    ATTRIBUTE_BY_KEY,
    DISABLED_CONSTRAINT_ATTRIBUTES,
    FORBIDDEN_REQUIREMENTS,
    NEGATIVE_ONLY_ATTRIBUTES,
    POSITIVE_ONLY_ATTRIBUTES,
    TIME_AVAILABILITY_ATTRIBUTES,
    attribute_constraint_templates,
    attribute_display_templates,
)
from mad_attr_filter.scenarios import SCENARIO_BY_KEY, is_allowed_by_scenario


class SemanticValidationError(ValueError):
    """Raised when a sample violates semantic consistency rules."""


class InvalidPolarityError(SemanticValidationError):
    """Raised when a constraint uses a forbidden required value."""


class ScenarioCompatibilityError(SemanticValidationError):
    """Raised when an attribute is incompatible with the sampled scenario."""


class SemanticConflictError(SemanticValidationError):
    """Raised when a sample contains an internally inconsistent attribute pair."""


NEGATIVE_PREFERENCE_REQUIREMENTS: frozenset[tuple[str, bool]] = frozenset(
    {
        ("accepts_flexible_hours", False),
        ("willing_to_travel", False),
        ("prefers_long_term_project", False),
        ("prefers_on_site_work", False),
    }
)

CHINESE_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")

FORBIDDEN_REQUIREMENT_PHRASES: tuple[str, ...] = (
    "must be unavailable",
    "must not be available",
    "must be unwilling",
    "must not participate",
    "must prefer not",
    "must not want",
)


def _constraint_id(constraint: Mapping[str, Any]) -> str:
    return str(constraint.get("id", "<unknown>"))


def count_chinese_characters(text: str) -> int:
    """Count CJK ideographs in a text string."""
    return len(CHINESE_RE.findall(text))


def sample_chinese_character_count(sample: Mapping[str, Any]) -> int:
    """Count Chinese characters in user-facing fields of one sample."""
    total = count_chinese_characters(str(sample.get("question", "")))
    options = sample.get("options", {})
    if isinstance(options, Mapping):
        total += sum(count_chinese_characters(str(value)) for value in options.values())
    for constraint in sample.get("constraints", []):
        total += count_chinese_characters(str(constraint.get("natural_language", "")))
    return total


def _validate_constraint_semantics(sample: Mapping[str, Any]) -> None:
    if sample.get("language") != "en":
        raise SemanticValidationError("English benchmark items must use language='en'")
    if sample_chinese_character_count(sample) != 0:
        raise SemanticValidationError("English benchmark item contains Chinese characters")

    scenario_key = str(sample.get("scenario"))
    if scenario_key not in SCENARIO_BY_KEY:
        raise ScenarioCompatibilityError(f"Unknown scenario: {scenario_key}")

    constrained_values: dict[str, bool] = {}
    for constraint in sample.get("constraints", []):
        if not isinstance(constraint, Mapping):
            raise SemanticValidationError("Constraint must be an object")
        attribute_key = str(constraint.get("attribute"))
        if attribute_key not in ATTRIBUTE_BY_KEY:
            raise SemanticValidationError(f"Unknown attribute: {attribute_key}")
        attribute = ATTRIBUTE_BY_KEY[attribute_key]
        required_value = bool(constraint.get("required_value"))

        if attribute_key in DISABLED_CONSTRAINT_ATTRIBUTES:
            raise SemanticValidationError(f"{_constraint_id(constraint)} uses disabled attribute: {attribute_key}")
        if not attribute.eligible_for_constraint_sampling:
            raise SemanticValidationError(f"{_constraint_id(constraint)} uses ineligible attribute: {attribute_key}")
        if (attribute_key, required_value) in FORBIDDEN_REQUIREMENTS:
            raise InvalidPolarityError(
                f"{_constraint_id(constraint)} uses forbidden requirement: {attribute_key}={required_value}"
            )
        if attribute_key in TIME_AVAILABILITY_ATTRIBUTES and required_value is not True:
            raise InvalidPolarityError(f"{_constraint_id(constraint)} requires unavailable time: {attribute_key}")

        if required_value not in attribute.allowed_required_values:
            raise InvalidPolarityError(
                f"{_constraint_id(constraint)} requires forbidden value {required_value} for {attribute_key}"
            )
        if attribute_key in NEGATIVE_ONLY_ATTRIBUTES and required_value is True:
            raise InvalidPolarityError(f"{_constraint_id(constraint)} requires negative attribute true: {attribute_key}")
        if attribute_key in POSITIVE_ONLY_ATTRIBUTES and required_value is False:
            raise InvalidPolarityError(f"{_constraint_id(constraint)} requires positive attribute false: {attribute_key}")

        if scenario_key not in attribute.compatible_scenarios:
            raise ScenarioCompatibilityError(f"{attribute_key} is not compatible with {scenario_key}")
        if not is_allowed_by_scenario(attribute_key, attribute.category, scenario_key):
            raise ScenarioCompatibilityError(f"{attribute_key} is not allowed by scenario {scenario_key}")

        natural_language = str(constraint.get("natural_language", ""))
        if not natural_language.strip():
            raise SemanticValidationError(f"{_constraint_id(constraint)} has empty English constraint text")
        if natural_language not in attribute_constraint_templates(attribute_key, required_value):
            raise SemanticValidationError(
                f"{_constraint_id(constraint)} natural language does not match {attribute_key}={required_value}"
            )
        if any(phrase in natural_language.lower() for phrase in FORBIDDEN_REQUIREMENT_PHRASES):
            raise SemanticValidationError(
                f"{_constraint_id(constraint)} natural language contains forbidden requirement wording"
            )
        constrained_values[attribute_key] = required_value

    if constrained_values.get("can_work_remote") is True and constrained_values.get("can_work_onsite") is True:
        return


def _validate_candidate_semantics(sample: Mapping[str, Any]) -> None:
    constraints = list(sample.get("constraints", []))
    constrained_attributes = [str(constraint["attribute"]) for constraint in constraints]
    options = sample.get("options")
    entities = sample.get("entities")
    if not isinstance(options, Mapping) or not isinstance(entities, Mapping):
        raise SemanticValidationError("Sample is missing options or entities")

    for label in ("A", "B", "C", "D"):
        option_text = str(options.get(label, ""))
        if not option_text.strip():
            raise SemanticValidationError(f"Option {label} has empty English candidate text")
        entity = entities.get(label)
        if not isinstance(entity, Mapping):
            raise SemanticValidationError(f"Entity {label} must be an object")
        attributes = entity.get("attributes")
        if not isinstance(attributes, Mapping):
            raise SemanticValidationError(f"Entity {label} is missing attributes")
        display_order = entity.get("display_order")
        displayed_facts = entity.get("displayed_facts")
        if not isinstance(display_order, Sequence) or isinstance(display_order, (str, bytes)):
            raise SemanticValidationError(f"Entity {label} is missing display_order")
        if not isinstance(displayed_facts, Sequence) or isinstance(displayed_facts, (str, bytes)):
            raise SemanticValidationError(f"Entity {label} is missing displayed_facts")

        display_order_list = [str(item) for item in display_order]
        if set(display_order_list) != set(constrained_attributes) or len(display_order_list) != len(constrained_attributes):
            raise SemanticValidationError(f"Entity {label} display_order does not cover constrained attributes")
        if display_order_list == constrained_attributes and len(constrained_attributes) > 1:
            raise SemanticValidationError(f"Entity {label} display_order is identical to constraint order")
        if len(displayed_facts) != len(constrained_attributes):
            raise SemanticValidationError(f"Entity {label} displayed_facts length mismatch")

        for fact in displayed_facts:
            if not isinstance(fact, Mapping):
                raise SemanticValidationError(f"Entity {label} displayed fact must be an object")
            attribute_key = str(fact.get("attribute"))
            if attribute_key not in constrained_attributes:
                raise SemanticValidationError(f"Entity {label} displays unconstrained attribute {attribute_key}")
            if attribute_key not in attributes:
                raise SemanticValidationError(f"Entity {label} missing displayed attribute {attribute_key}")
            value = bool(fact.get("value"))
            if value != bool(attributes[attribute_key]):
                raise SemanticValidationError(f"Entity {label} displayed value mismatch for {attribute_key}")
            text = str(fact.get("text", ""))
            name = str(entity.get("name", ""))
            allowed_texts = {
                template.format(name=name) for template in attribute_display_templates(attribute_key, value)
            }
            if text not in allowed_texts:
                raise SemanticValidationError(f"Entity {label} uses invalid display text for {attribute_key}: {text}")
            if text not in option_text:
                raise SemanticValidationError(f"Entity {label} option text omits displayed fact: {text}")


def validate_semantics(sample: Mapping[str, Any]) -> None:
    """Validate polarity, scenario compatibility, and candidate text consistency."""
    _validate_constraint_semantics(sample)
    _validate_candidate_semantics(sample)


def collect_semantic_anomalies(samples: Sequence[Mapping[str, Any]]) -> dict[str, list[dict[str, object]]]:
    """Collect semantic anomaly lists used by the v2 statistics report."""
    forbidden_positive_constraints: list[dict[str, object]] = []
    forbidden_negative_constraints: list[dict[str, object]] = []
    scenario_attribute_mismatches: list[dict[str, object]] = []

    for sample in samples:
        scenario_key = str(sample.get("scenario"))
        for constraint in sample.get("constraints", []):
            attribute_key = str(constraint.get("attribute"))
            required_value = bool(constraint.get("required_value"))
            record = {
                "item_id": sample.get("item_id"),
                "constraint_id": constraint.get("id"),
                "attribute": attribute_key,
                "required_value": required_value,
                "scenario": scenario_key,
            }
            attribute = ATTRIBUTE_BY_KEY.get(attribute_key)
            if attribute is None:
                scenario_attribute_mismatches.append(record)
                continue
            if attribute_key in DISABLED_CONSTRAINT_ATTRIBUTES or not attribute.eligible_for_constraint_sampling:
                scenario_attribute_mismatches.append(record)
            if attribute_key in NEGATIVE_ONLY_ATTRIBUTES and required_value is True:
                forbidden_positive_constraints.append(record)
            if attribute_key in POSITIVE_ONLY_ATTRIBUTES and required_value is False:
                forbidden_negative_constraints.append(record)
            if scenario_key not in attribute.compatible_scenarios or not is_allowed_by_scenario(
                attribute_key, attribute.category, scenario_key
            ):
                scenario_attribute_mismatches.append(record)

    return {
        "forbidden_positive_constraints": forbidden_positive_constraints,
        "forbidden_negative_constraints": forbidden_negative_constraints,
        "scenario_attribute_mismatches": scenario_attribute_mismatches,
    }


def collect_strict_semantic_audit(samples: Sequence[Mapping[str, Any]]) -> dict[str, object]:
    """Return strict v3 semantic audit counts and offending records."""
    forbidden_requirement_records: list[dict[str, object]] = []
    disabled_attribute_records: list[dict[str, object]] = []
    negative_availability_records: list[dict[str, object]] = []
    negative_preference_records: list[dict[str, object]] = []
    semantic_error_records: list[dict[str, object]] = []
    chinese_character_count = 0

    for sample in samples:
        chinese_character_count += sample_chinese_character_count(sample)
        for constraint in sample.get("constraints", []):
            attribute_key = str(constraint.get("attribute"))
            required_value = bool(constraint.get("required_value"))
            record = {
                "item_id": sample.get("item_id"),
                "constraint_id": constraint.get("id"),
                "attribute": attribute_key,
                "required_value": required_value,
                "scenario": sample.get("scenario"),
                "natural_language": constraint.get("natural_language"),
            }
            if (attribute_key, required_value) in FORBIDDEN_REQUIREMENTS:
                forbidden_requirement_records.append(record)
            if attribute_key in DISABLED_CONSTRAINT_ATTRIBUTES:
                disabled_attribute_records.append(record)
            if attribute_key in TIME_AVAILABILITY_ATTRIBUTES and required_value is False:
                negative_availability_records.append(record)
            if (attribute_key, required_value) in NEGATIVE_PREFERENCE_REQUIREMENTS:
                negative_preference_records.append(record)
            natural_language = str(constraint.get("natural_language", ""))
            if any(phrase in natural_language.lower() for phrase in FORBIDDEN_REQUIREMENT_PHRASES):
                forbidden_requirement_records.append(record)
        try:
            validate_semantics(sample)
        except SemanticValidationError as exc:
            semantic_error_records.append({"item_id": sample.get("item_id"), "error": str(exc)})

    total = len(samples)
    semantic_validation_pass_rate = (total - len(semantic_error_records)) / total if total else 0.0
    return {
        "total_samples": total,
        "forbidden_requirement_count": len(forbidden_requirement_records),
        "disabled_attribute_count": len(disabled_attribute_records),
        "negative_availability_count": len(negative_availability_records),
        "negative_preference_count": len(negative_preference_records),
        "semantic_error_count": len(semantic_error_records),
        "chinese_character_count": chinese_character_count,
        "semantic_validation_pass_rate": semantic_validation_pass_rate,
        "forbidden_requirements": forbidden_requirement_records,
        "disabled_attributes": disabled_attribute_records,
        "negative_availability_requirements": negative_availability_records,
        "negative_preference_requirements": negative_preference_records,
        "semantic_errors": semantic_error_records,
    }
