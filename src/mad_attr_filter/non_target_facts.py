"""Scenario-relevant candidate facts that are not constraints in the current item."""

from __future__ import annotations

import random
from dataclasses import dataclass

from mad_attr_filter.attributes import (
    AVAILABILITY_SELECTION,
    EXPERT_RECRUITMENT,
    PROJECT_ASSIGNMENT,
)


@dataclass(frozen=True)
class NonTargetFactSpec:
    """A domain-relevant fact outside the current formal attribute pool."""

    key: str
    category: str
    compatible_scenarios: tuple[str, ...]
    templates: tuple[str, ...]


EXPERT_AND_PROJECT = (EXPERT_RECRUITMENT, PROJECT_ASSIGNMENT)
ALL_SCENARIOS = (EXPERT_RECRUITMENT, PROJECT_ASSIGNMENT, AVAILABILITY_SELECTION)

NON_TARGET_FACT_POOL: tuple[NonTargetFactSpec, ...] = (
    NonTargetFactSpec(
        "has_technical_writing_experience",
        "professional_experience",
        EXPERT_AND_PROJECT,
        (
            "{name} has prepared technical reports for previous work",
            "{name} has experience writing technical documentation",
            "{name} has produced formal project reports before",
        ),
    ),
    NonTargetFactSpec(
        "has_peer_review_experience",
        "professional_experience",
        (EXPERT_RECRUITMENT,),
        (
            "{name} has reviewed research work for colleagues",
            "{name} has experience providing peer review feedback",
            "{name} has evaluated draft research reports before",
        ),
    ),
    NonTargetFactSpec(
        "has_grant_proposal_experience",
        "professional_experience",
        (EXPERT_RECRUITMENT,),
        (
            "{name} has contributed to research grant proposals",
            "{name} has helped prepare project funding applications",
            "{name} has experience drafting grant materials",
        ),
    ),
    NonTargetFactSpec(
        "has_mentoring_experience",
        "professional_experience",
        EXPERT_AND_PROJECT,
        (
            "{name} has mentored junior colleagues",
            "{name} has supported less experienced team members",
            "{name} has previously provided professional mentoring",
        ),
    ),
    NonTargetFactSpec(
        "has_stakeholder_reporting_experience",
        "professional_experience",
        EXPERT_AND_PROJECT,
        (
            "{name} has presented progress updates to stakeholders",
            "{name} has experience preparing stakeholder briefings",
            "{name} has reported project progress to external partners",
        ),
    ),
    NonTargetFactSpec(
        "familiar_with_cloud_tools",
        "technical_background",
        EXPERT_AND_PROJECT,
        (
            "{name} is familiar with common cloud collaboration tools",
            "{name} has used cloud-based project tools",
            "{name} has experience working with shared cloud platforms",
        ),
    ),
    NonTargetFactSpec(
        "has_version_control_experience",
        "technical_background",
        (PROJECT_ASSIGNMENT,),
        (
            "{name} has used version control in previous assignments",
            "{name} is familiar with version-controlled project workflows",
            "{name} has maintained shared project files with version control",
        ),
    ),
    NonTargetFactSpec(
        "has_requirements_gathering_experience",
        "professional_experience",
        (PROJECT_ASSIGNMENT,),
        (
            "{name} has gathered requirements for earlier projects",
            "{name} has experience documenting stakeholder requirements",
            "{name} has helped clarify requirements before project work began",
        ),
    ),
    NonTargetFactSpec(
        "keeps_detailed_work_records",
        "work_practice",
        ALL_SCENARIOS,
        (
            "{name} keeps detailed records of completed work",
            "{name} routinely documents task progress",
            "{name} maintains organized records for assignments",
        ),
    ),
    NonTargetFactSpec(
        "prefers_advance_schedule_notice",
        "scheduling_preference",
        (AVAILABILITY_SELECTION,),
        (
            "{name} prefers to receive schedule details several days in advance",
            "{name} generally plans participation after receiving advance notice",
            "{name} prefers advance notice when shifts are assigned",
        ),
    ),
    NonTargetFactSpec(
        "accepts_occasional_overtime",
        "scheduling_preference",
        (AVAILABILITY_SELECTION, PROJECT_ASSIGNMENT),
        (
            "{name} is open to occasional overtime when notified in advance",
            "{name} can sometimes extend a shift with prior notice",
            "{name} accepts occasional overtime arrangements",
        ),
    ),
    NonTargetFactSpec(
        "can_swap_shifts_with_notice",
        "scheduling_practice",
        (AVAILABILITY_SELECTION,),
        (
            "{name} can arrange shift swaps when given notice",
            "{name} is able to exchange assigned shifts in advance",
            "{name} can coordinate an occasional shift swap",
        ),
    ),
    NonTargetFactSpec(
        "can_adjust_break_times",
        "scheduling_practice",
        (AVAILABILITY_SELECTION,),
        (
            "{name} can adjust break times within an assigned shift",
            "{name} is flexible about the timing of scheduled breaks",
            "{name} can move break periods when operations require it",
        ),
    ),
    NonTargetFactSpec(
        "can_attend_optional_check_ins",
        "participation_practice",
        (AVAILABILITY_SELECTION, PROJECT_ASSIGNMENT),
        (
            "{name} can attend optional project check-ins when notified",
            "{name} is generally able to join optional status meetings",
            "{name} can participate in occasional optional check-ins",
        ),
    ),
)

NON_TARGET_FACT_BY_KEY: dict[str, NonTargetFactSpec] = {
    fact.key: fact for fact in NON_TARGET_FACT_POOL
}


def scenario_non_target_facts(scenario_key: str) -> tuple[NonTargetFactSpec, ...]:
    """Return all non-target facts designed for a scenario."""
    return tuple(
        fact for fact in NON_TARGET_FACT_POOL if scenario_key in fact.compatible_scenarios
    )


def sample_non_target_facts(
    name: str,
    scenario_key: str,
    rng: random.Random,
    *,
    count: int = 2,
) -> list[dict[str, str]]:
    """Sample JSON-ready, scenario-compatible non-target facts."""
    available = scenario_non_target_facts(scenario_key)
    if count < 0 or count > len(available):
        raise ValueError(
            f"Scenario {scenario_key} has {len(available)} non-target facts; requested {count}"
        )
    selected = rng.sample(list(available), count)
    return [
        {
            "key": fact.key,
            "category": fact.category,
            "text": rng.choice(fact.templates).format(name=name),
        }
        for fact in selected
    ]


def render_non_target_fact_sentences(facts: list[dict[str, str]]) -> str:
    """Render non-target facts naturally without an explicit irrelevance cue."""
    return " ".join(f"{fact['text']}." for fact in facts)
