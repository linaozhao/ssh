"""English scenario definitions for attribute-filtering tasks."""

from __future__ import annotations

from mad_attr_filter.attributes import AVAILABILITY_SELECTION, EXPERT_RECRUITMENT, PROJECT_ASSIGNMENT
from mad_attr_filter.models import ScenarioSpec


SCENARIOS: tuple[ScenarioSpec, ...] = (
    ScenarioSpec(
        key=EXPERT_RECRUITMENT,
        title="Expert recruitment",
        introduction_templates=(
            "A research lab is selecting one researcher for a new project.",
            "A research team needs to recruit one member who satisfies all of the listed requirements.",
            "A project leader must choose one qualified researcher from four applicants.",
        ),
        allowed_attribute_categories=("ability", "qualification", "availability", "restriction", "preference"),
        allowed_attribute_keys=None,
    ),
    ScenarioSpec(
        key=PROJECT_ASSIGNMENT,
        title="Project assignment",
        introduction_templates=(
            "A project team needs to assign one member to a specialized task.",
            "The project manager must select one person who satisfies every requirement for the assignment.",
            "Four team members are being considered for a project role.",
        ),
        allowed_attribute_categories=("ability", "qualification", "availability", "restriction", "preference"),
        allowed_attribute_keys=None,
    ),
    ScenarioSpec(
        key=AVAILABILITY_SELECTION,
        title="Availability selection",
        introduction_templates=(
            "A team is selecting one participant whose availability matches all project requirements.",
            "Four candidates are being considered based on their availability and participation constraints.",
            "The coordinator must identify the only candidate who meets all scheduling requirements.",
        ),
        allowed_attribute_categories=("ability", "availability", "restriction", "preference"),
        allowed_attribute_keys=(
            "available_monday",
            "available_tuesday",
            "available_morning",
            "available_afternoon",
            "available_weekend",
            "available_next_month",
            "has_schedule_conflict",
            "requires_extra_equipment",
            "can_work_remote",
            "can_work_onsite",
            "accepts_flexible_hours",
        ),
    ),
)

SCENARIO_BY_KEY: dict[str, ScenarioSpec] = {scenario.key: scenario for scenario in SCENARIOS}


def is_allowed_by_scenario(attribute_key: str, category: str, scenario_key: str) -> bool:
    """Return whether a scenario allows an attribute by category and optional key allowlist."""
    scenario = SCENARIO_BY_KEY[scenario_key]
    if category not in scenario.allowed_attribute_categories:
        return False
    if scenario.allowed_attribute_keys is not None and attribute_key not in scenario.allowed_attribute_keys:
        return False
    return True


def serialized_scenarios() -> list[dict[str, object]]:
    """Return all scenario specs as JSON-ready dictionaries."""
    return [scenario.to_dict() for scenario in SCENARIOS]

