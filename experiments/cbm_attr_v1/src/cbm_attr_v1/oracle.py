"""Turn-level oracle implementations for not-yet-eliminated candidate sets."""

from __future__ import annotations

import itertools
from collections.abc import Iterable, Mapping
from typing import Any

from cbm_attr_v1.common import LABELS


def active_target_facts(evidence: Iterable[Mapping[str, Any]]) -> dict[tuple[str, str], bool]:
    """Resolve active target evidence, applying explicit version replacements."""
    active: dict[tuple[str, str], bool] = {}
    for fact in evidence:
        if fact.get("fact_kind") != "target" or fact.get("event_type") == "restatement":
            continue
        key = (str(fact["candidate_id"]), str(fact["attribute"]))
        active[key] = bool(fact["value"])
    return active


def compute_oracle(
    constraints: Iterable[Mapping[str, Any]], evidence: Iterable[Mapping[str, Any]]
) -> list[str]:
    """Keep candidates unless current active evidence proves a violation."""
    required = {str(row["attribute"]): bool(row["required_value"]) for row in constraints}
    active = active_target_facts(evidence)
    retained: list[str] = []
    for candidate in LABELS:
        violated = any(
            (candidate, attribute) in active and active[(candidate, attribute)] != value
            for attribute, value in required.items()
        )
        if not violated:
            retained.append(candidate)
    return retained


def enumerate_oracle(
    constraints: Iterable[Mapping[str, Any]], evidence: Iterable[Mapping[str, Any]]
) -> list[str]:
    """Cross-check eligibility by enumerating completions of unknown attributes."""
    required = {str(row["attribute"]): bool(row["required_value"]) for row in constraints}
    active = active_target_facts(evidence)
    retained: list[str] = []
    for candidate in LABELS:
        unknown = [attribute for attribute in required if (candidate, attribute) not in active]
        possible = False
        for values in itertools.product((False, True), repeat=len(unknown)):
            completion = dict(zip(unknown, values, strict=True))
            if all(
                active.get((candidate, attribute), completion.get(attribute)) == required_value
                for attribute, required_value in required.items()
            ):
                possible = True
                break
        if possible:
            retained.append(candidate)
    return retained
