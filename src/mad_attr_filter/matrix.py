"""Constraint satisfaction matrix and violation signature helpers."""

from __future__ import annotations

from collections.abc import Mapping

from mad_attr_filter.models import ConstraintSpec


def compute_constraint_matrix(
    candidate_attributes_by_label: Mapping[str, Mapping[str, bool]],
    constraints: list[ConstraintSpec],
) -> dict[str, dict[str, bool]]:
    """Compute whether each option satisfies each constraint."""
    matrix: dict[str, dict[str, bool]] = {}
    for label, attributes in candidate_attributes_by_label.items():
        matrix[label] = {}
        for constraint in constraints:
            if constraint.attribute not in attributes:
                raise KeyError(f"Candidate {label} is missing attribute {constraint.attribute}")
            matrix[label][constraint.id] = attributes[constraint.attribute] == constraint.required_value
    return matrix


def compute_violation_signatures(matrix: Mapping[str, Mapping[str, bool]]) -> dict[str, list[str]]:
    """Convert a satisfaction matrix to ordered violation signatures."""
    signatures: dict[str, list[str]] = {}
    for label, row in matrix.items():
        signatures[label] = [constraint_id for constraint_id, is_satisfied in row.items() if not is_satisfied]
    return signatures

