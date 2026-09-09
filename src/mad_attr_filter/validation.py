"""Independent validation for generated samples and datasets."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from mad_attr_filter.matrix import compute_constraint_matrix, compute_violation_signatures
from mad_attr_filter.models import ConstraintSpec
from mad_attr_filter.semantic_validator import SemanticValidationError, validate_semantics


class ValidationError(ValueError):
    """Raised when a sample or dataset violates the specification."""


@dataclass(frozen=True)
class DatasetValidationSummary:
    """Compact summary returned after validating a dataset."""

    total_samples: int
    option_closeness_counts: dict[str, int]
    structural_complexity_counts: dict[str, int]
    scenario_counts: dict[str, int]
    gold_position_distribution: dict[str, int]

    def to_dict(self) -> dict[str, object]:
        """Serialize the validation summary."""
        return {
            "total_samples": self.total_samples,
            "option_closeness_counts": dict(self.option_closeness_counts),
            "structural_complexity_counts": dict(self.structural_complexity_counts),
            "scenario_counts": dict(self.scenario_counts),
            "gold_position_distribution": dict(self.gold_position_distribution),
        }


def _constraints_from_sample(sample: Mapping[str, Any]) -> list[ConstraintSpec]:
    constraints: list[ConstraintSpec] = []
    for constraint in sample.get("constraints", []):
        constraints.append(
            ConstraintSpec(
                id=str(constraint["id"]),
                attribute=str(constraint["attribute"]),
                required_value=bool(constraint["required_value"]),
                type=str(constraint["type"]),
                natural_language=str(constraint["natural_language"]),
            )
        )
    return constraints


def _assert_option_closeness_pattern(option_closeness: str, wrong_violation_counts: list[int]) -> None:
    sorted_counts = sorted(wrong_violation_counts)
    if option_closeness == "easy":
        if len(sorted_counts) != 3 or sorted_counts[0] != 2 or sorted_counts[1] != 2:
            raise ValidationError(f"Easy item must have violation counts [2, 2, >=2], got {wrong_violation_counts}")
    elif option_closeness == "medium":
        if sorted_counts != [1, 1, 2]:
            raise ValidationError(f"Medium item must have violation counts [1, 1, 2], got {wrong_violation_counts}")
    elif option_closeness == "hard":
        if sorted_counts != [1, 1, 1]:
            raise ValidationError(f"Hard item must have violation counts [1, 1, 1], got {wrong_violation_counts}")
    else:
        raise ValidationError(f"Unknown option_closeness: {option_closeness}")


def _assert_structural_complexity(structural_complexity: str, num_constraints: int) -> None:
    expected = {3: "low", 4: "medium", 5: "high"}.get(num_constraints)
    if expected is None:
        raise ValidationError(f"Unsupported constraint count: {num_constraints}")
    if structural_complexity != expected:
        raise ValidationError(
            f"structural_complexity must be {expected} for {num_constraints} constraints, got {structural_complexity}"
        )


def validate_sample(sample: Mapping[str, Any]) -> None:
    """Validate one JSON-ready sample independently from generation code."""
    labels = ("A", "B", "C", "D")
    options = sample.get("options")
    entities = sample.get("entities")
    if not isinstance(options, Mapping) or set(options.keys()) != set(labels):
        raise ValidationError("Sample must contain exactly four options A-D")
    if not isinstance(entities, Mapping) or set(entities.keys()) != set(labels):
        raise ValidationError("Sample must contain exactly four entities A-D")

    constraints = _constraints_from_sample(sample)
    if not 3 <= len(constraints) <= 5:
        raise ValidationError("Each sample must contain 3 to 5 constraints")
    option_closeness = str(sample.get("option_closeness", sample.get("difficulty", "")))
    structural_complexity = str(sample.get("structural_complexity", ""))
    _assert_structural_complexity(structural_complexity, len(constraints))
    if sample.get("empirical_difficulty") is not None:
        raise ValidationError("empirical_difficulty must be null before empirical evaluation")

    required_by_attribute: dict[str, bool] = {}
    for constraint in constraints:
        previous = required_by_attribute.get(constraint.attribute)
        if previous is not None and previous != constraint.required_value:
            raise ValidationError(f"Conflicting constraints for attribute {constraint.attribute}")
        required_by_attribute[constraint.attribute] = constraint.required_value

    names = [str(entities[label].get("name")) for label in labels]
    if len(set(names)) != 4:
        raise ValidationError("Candidate names must be unique within a sample")

    candidate_attributes: dict[str, dict[str, bool]] = {}
    expected_signatures: dict[str, list[str]] = {}
    for label in labels:
        entity = entities[label]
        attributes = entity.get("attributes")
        if not isinstance(attributes, Mapping):
            raise ValidationError(f"Entity {label} is missing attributes")
        candidate_attributes[label] = {str(key): bool(value) for key, value in attributes.items()}
        for constraint in constraints:
            if constraint.attribute not in candidate_attributes[label]:
                raise ValidationError(f"Entity {label} is missing constrained attribute {constraint.attribute}")
        expected = entity.get("expected_violation_signature")
        if not isinstance(expected, Sequence) or isinstance(expected, (str, bytes)):
            raise ValidationError(f"Entity {label} has invalid expected violation signature")
        expected_signatures[label] = [str(item) for item in expected]

    recomputed_matrix = compute_constraint_matrix(candidate_attributes, constraints)
    recomputed_signatures = compute_violation_signatures(recomputed_matrix)

    if sample.get("option_constraint_matrix") != recomputed_matrix:
        raise ValidationError("Stored option_constraint_matrix does not match recomputation")
    if sample.get("option_violation_signature") != recomputed_signatures:
        raise ValidationError("Stored option_violation_signature does not match recomputation")

    for label in labels:
        if expected_signatures[label] != recomputed_signatures[label]:
            raise ValidationError(f"Expected violation signature mismatch for option {label}")

    valid_labels = [label for label in labels if not recomputed_signatures[label]]
    if len(valid_labels) != 1:
        raise ValidationError(f"Expected exactly one valid option, got {valid_labels}")
    if sample.get("gold_answer") != valid_labels[0]:
        raise ValidationError("gold_answer does not point to the unique valid option")
    marked_gold_labels = [label for label in labels if entities[label].get("is_gold") is True]
    if marked_gold_labels != valid_labels:
        raise ValidationError(f"Gold marker mismatch: expected {valid_labels}, got {marked_gold_labels}")

    wrong_labels = [label for label in labels if label != valid_labels[0]]
    if any(not recomputed_signatures[label] for label in wrong_labels):
        raise ValidationError("Every wrong option must violate at least one constraint")

    constrained_combinations = {
        tuple((constraint.attribute, candidate_attributes[label][constraint.attribute]) for constraint in constraints)
        for label in labels
    }
    if len(constrained_combinations) != 4:
        raise ValidationError("Constrained attribute combinations must be unique across options")

    for constraint in constraints:
        excluded_count = sum(1 for label in wrong_labels if not recomputed_matrix[label][constraint.id])
        if excluded_count < 1:
            raise ValidationError(f"Constraint {constraint.id} does not exclude any wrong option")

    wrong_violation_counts = [len(recomputed_signatures[label]) for label in wrong_labels]
    _assert_option_closeness_pattern(option_closeness, wrong_violation_counts)
    try:
        validate_semantics(sample)
    except SemanticValidationError as exc:
        raise ValidationError(f"Semantic validation failed: {exc}") from exc
    metadata = sample.get("metadata")
    if isinstance(metadata, Mapping) and metadata.get("semantic_validation_passed") is not True:
        raise ValidationError("metadata.semantic_validation_passed must be true")


def validate_dataset(
    samples: Sequence[Mapping[str, Any]],
    *,
    enforce_pilot_gold_balance: bool = False,
) -> DatasetValidationSummary:
    """Validate a dataset and optionally enforce the pilot gold-position balance."""
    option_closeness_counter: Counter[str] = Counter()
    structural_complexity_counter: Counter[str] = Counter()
    scenario_counter: Counter[str] = Counter()
    gold_counter: Counter[str] = Counter()
    for index, sample in enumerate(samples, start=1):
        try:
            validate_sample(sample)
        except ValidationError as exc:
            item_id = sample.get("item_id", f"#{index}")
            raise ValidationError(f"{item_id}: {exc}") from exc
        option_closeness_counter[str(sample.get("option_closeness", sample.get("difficulty", "")))] += 1
        structural_complexity_counter[str(sample.get("structural_complexity", ""))] += 1
        scenario_counter[str(sample.get("scenario", ""))] += 1
        gold_counter[str(sample["gold_answer"])] += 1

    if enforce_pilot_gold_balance and samples:
        ideal = len(samples) / 4
        for label in ("A", "B", "C", "D"):
            if len(samples) % 4 == 0 and gold_counter[label] != int(ideal):
                raise ValidationError(
                    f"Gold answer distribution is not exactly balanced: {dict(gold_counter)}, ideal={ideal:.2f}"
                )
            if len(samples) % 4 != 0 and abs(gold_counter[label] - ideal) > 5:
                raise ValidationError(
                    f"Gold answer distribution is not balanced: {dict(gold_counter)}, ideal={ideal:.2f}"
                )
        if len(samples) == 100 and all(key in scenario_counter for key in ("expert_recruitment", "project_assignment", "availability_selection")):
            for scenario_key in ("expert_recruitment", "project_assignment", "availability_selection"):
                if scenario_counter[scenario_key] < 25:
                    raise ValidationError(f"Scenario {scenario_key} has fewer than 25 samples: {dict(scenario_counter)}")

    return DatasetValidationSummary(
        total_samples=len(samples),
        option_closeness_counts=dict(sorted(option_closeness_counter.items())),
        structural_complexity_counts=dict(sorted(structural_complexity_counter.items())),
        scenario_counts=dict(sorted(scenario_counter.items())),
        gold_position_distribution={label: gold_counter[label] for label in ("A", "B", "C", "D")},
    )
