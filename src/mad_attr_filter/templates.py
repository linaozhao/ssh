"""Deterministic English templates for constraints, candidates, and questions."""

from __future__ import annotations

import random
from typing import Any

from mad_attr_filter.attributes import attribute_constraint_templates, attribute_display_templates
from mad_attr_filter.models import ConstraintSpec, ScenarioSpec

QUESTION_ENDINGS: dict[str, tuple[str, ...]] = {
    "expert_recruitment": (
        "Which candidate satisfies all of the requirements?",
        "Which applicant should be selected?",
        "Which researcher meets every listed requirement?",
    ),
    "project_assignment": (
        "Which person is eligible for the assignment?",
        "Which candidate should receive the project role?",
        "Which team member satisfies every assignment requirement?",
    ),
    "availability_selection": (
        "Which candidate meets all of the requirements?",
        "Which participant is eligible based on the stated constraints?",
        "Which candidate matches every scheduling requirement?",
    ),
}

CANDIDATE_TEXT_STYLES: tuple[str, ...] = ("single_sentence", "two_sentences", "reordered")


def render_constraint(attribute_key: str, required_value: bool, rng: random.Random) -> str:
    """Render a single atomic constraint in English."""
    templates = attribute_constraint_templates(attribute_key, required_value)
    if not templates:
        raise ValueError(f"No English constraint templates for {attribute_key}={required_value}")
    return rng.choice(templates)


def _display_order(constraints: list[ConstraintSpec], rng: random.Random) -> list[ConstraintSpec]:
    original = list(constraints)
    shuffled = list(constraints)
    rng.shuffle(shuffled)
    if len(shuffled) > 1 and [item.attribute for item in shuffled] == [item.attribute for item in original]:
        shuffled = shuffled[1:] + shuffled[:1]
    return shuffled


def _join_facts_single_sentence(facts: list[str]) -> str:
    if len(facts) == 1:
        return f"{facts[0]}."
    if len(facts) == 2:
        return f"{facts[0]}, and {facts[1]}."
    return f"{', '.join(facts[:-1])}, and {facts[-1]}."


def render_candidate(
    name: str,
    constraints: list[ConstraintSpec],
    attributes: dict[str, bool],
    rng: random.Random,
) -> tuple[str, list[str], list[dict[str, Any]]]:
    """Render candidate information and return text plus display metadata."""
    ordered_constraints = _display_order(constraints, rng)
    facts: list[dict[str, Any]] = []
    for constraint in ordered_constraints:
        value = attributes[constraint.attribute]
        template = rng.choice(attribute_display_templates(constraint.attribute, value))
        text = template.format(name=name)
        facts.append({"attribute": constraint.attribute, "value": value, "text": text})

    fact_texts = [str(fact["text"]) for fact in facts]
    style = rng.choice(CANDIDATE_TEXT_STYLES)
    if style == "single_sentence":
        text = _join_facts_single_sentence(fact_texts)
    elif style == "two_sentences" and len(fact_texts) >= 3:
        midpoint = max(1, len(fact_texts) // 2)
        first = _join_facts_single_sentence(fact_texts[:midpoint])
        second = _join_facts_single_sentence(fact_texts[midpoint:])
        text = f"{first} In addition, {second}"
    else:
        sentences = [f"{fact}." for fact in fact_texts]
        text = " ".join(sentences)
    return text, [str(fact["attribute"]) for fact in facts], facts


def render_question(
    scenario: ScenarioSpec,
    constraints: list[ConstraintSpec],
    options: dict[str, str],
    rng: random.Random,
) -> str:
    """Render the full multiple-choice question in English."""
    intro = rng.choice(scenario.introduction_templates)
    ending = rng.choice(QUESTION_ENDINGS[scenario.key])
    constraint_lines = "\n".join(
        f"{index}. {constraint.natural_language}" for index, constraint in enumerate(constraints, start=1)
    )
    option_lines = "\n".join(f"{label}. {options[label]}" for label in ("A", "B", "C", "D"))
    return (
        f"{intro}\n"
        "The selected person must satisfy all of the following requirements:\n\n"
        "Requirements:\n"
        f"{constraint_lines}\n\n"
        "Candidates:\n"
        f"{option_lines}\n\n"
        f"{ending}"
    )
