"""Dataclasses used by the attribute filtering generator."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AttributeSpec:
    """Definition of one boolean attribute in the task pool."""

    key: str
    category: str
    allowed_required_values: tuple[bool, ...]
    compatible_scenarios: tuple[str, ...]
    constraint_true_templates: tuple[str, ...]
    constraint_false_templates: tuple[str, ...]
    candidate_true_templates: tuple[str, ...]
    candidate_false_templates: tuple[str, ...]
    eligible_for_constraint_sampling: bool = True

    def to_dict(self) -> dict[str, object]:
        """Serialize the attribute definition."""
        return {
            "key": self.key,
            "category": self.category,
            "allowed_required_values": list(self.allowed_required_values),
            "compatible_scenarios": list(self.compatible_scenarios),
            "constraint_true_templates": list(self.constraint_true_templates),
            "constraint_false_templates": list(self.constraint_false_templates),
            "candidate_true_templates": list(self.candidate_true_templates),
            "candidate_false_templates": list(self.candidate_false_templates),
            "eligible_for_constraint_sampling": self.eligible_for_constraint_sampling,
        }


@dataclass(frozen=True)
class ScenarioSpec:
    """Task scenario used to constrain attribute sampling and wording."""

    key: str
    title: str
    introduction_templates: tuple[str, ...]
    allowed_attribute_categories: tuple[str, ...]
    allowed_attribute_keys: tuple[str, ...] | None = None

    def to_dict(self) -> dict[str, object]:
        """Serialize the scenario definition."""
        return {
            "key": self.key,
            "title": self.title,
            "introduction_templates": list(self.introduction_templates),
            "allowed_attribute_categories": list(self.allowed_attribute_categories),
            "allowed_attribute_keys": list(self.allowed_attribute_keys) if self.allowed_attribute_keys else None,
        }


@dataclass(frozen=True)
class ConstraintSpec:
    """A required_true or required_false constraint over one attribute."""

    id: str
    attribute: str
    required_value: bool
    type: str
    natural_language: str

    def to_dict(self) -> dict[str, object]:
        """Serialize the constraint."""
        return {
            "id": self.id,
            "attribute": self.attribute,
            "required_value": self.required_value,
            "type": self.type,
            "natural_language": self.natural_language,
        }


@dataclass(frozen=True)
class Candidate:
    """A candidate option with complete attributes and expected violations."""

    name: str
    attributes: dict[str, bool]
    expected_violation_signature: list[str]
    is_gold: bool = False
    display_order: list[str] | None = None
    displayed_facts: list[dict[str, object]] | None = None

    def to_entity_dict(self) -> dict[str, object]:
        """Serialize candidate details for the JSONL entities field."""
        payload: dict[str, object] = {
            "name": self.name,
            "attributes": dict(self.attributes),
            "expected_violation_signature": list(self.expected_violation_signature),
            "is_gold": self.is_gold,
        }
        if self.display_order is not None:
            payload["display_order"] = list(self.display_order)
        if self.displayed_facts is not None:
            payload["displayed_facts"] = list(self.displayed_facts)
        return payload


@dataclass(frozen=True)
class GenerationReport:
    """Aggregate counters recorded while building a dataset."""

    requested_items: int
    generated_items: int
    attempts: int
    retries: int
    generation_failures: int
    validation_failures: int
    semantic_validation_failures: int
    invalid_polarity_failures: int
    scenario_compatibility_failures: int
    failure_reasons: dict[str, int]

    def to_dict(self) -> dict[str, object]:
        """Serialize the generation report."""
        return {
            "requested_items": self.requested_items,
            "generated_items": self.generated_items,
            "attempts": self.attempts,
            "retries": self.retries,
            "generation_failures": self.generation_failures,
            "validation_failures": self.validation_failures,
            "semantic_validation_failures": self.semantic_validation_failures,
            "invalid_polarity_failures": self.invalid_polarity_failures,
            "scenario_compatibility_failures": self.scenario_compatibility_failures,
            "failure_reasons": dict(self.failure_reasons),
        }
