"""English background facts that are deliberately outside the formal task state."""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class IrrelevantFactSpec:
    """A non-evaluative candidate fact used only to increase information load."""

    key: str
    templates: tuple[str, ...]


IRRELEVANT_FACT_POOL: tuple[IrrelevantFactSpec, ...] = (
    IrrelevantFactSpec(
        "enjoys_hiking",
        (
            "{name} enjoys hiking in free time",
            "{name} often goes hiking outside work",
            "hiking is one of {name}'s hobbies",
        ),
    ),
    IrrelevantFactSpec(
        "speaks_french",
        (
            "{name} speaks conversational French",
            "{name} has studied French",
            "{name} can hold a casual conversation in French",
        ),
    ),
    IrrelevantFactSpec(
        "plays_chess",
        (
            "{name} plays chess recreationally",
            "{name} enjoys casual chess games",
            "chess is a hobby of {name}",
        ),
    ),
    IrrelevantFactSpec(
        "likes_gardening",
        (
            "{name} enjoys gardening at home",
            "{name} spends some free time gardening",
            "gardening is among {name}'s hobbies",
        ),
    ),
    IrrelevantFactSpec(
        "reads_history",
        (
            "{name} reads history books for leisure",
            "{name} enjoys reading about history",
            "historical nonfiction interests {name}",
        ),
    ),
    IrrelevantFactSpec(
        "plays_music",
        (
            "{name} plays a musical instrument as a hobby",
            "{name} practices music outside work",
            "making music is one of {name}'s interests",
        ),
    ),
    IrrelevantFactSpec(
        "enjoys_cooking",
        (
            "{name} enjoys cooking at home",
            "{name} tries new recipes for fun",
            "cooking is a personal interest of {name}",
        ),
    ),
    IrrelevantFactSpec(
        "cycles_recreationally",
        (
            "{name} rides a bicycle recreationally",
            "{name} enjoys cycling outside work",
            "recreational cycling is a hobby of {name}",
        ),
    ),
    IrrelevantFactSpec(
        "visits_museums",
        (
            "{name} likes visiting museums",
            "{name} visits museums for leisure",
            "museum visits are one of {name}'s interests",
        ),
    ),
    IrrelevantFactSpec(
        "enjoys_photography",
        (
            "{name} practices photography as a hobby",
            "{name} enjoys taking photographs outside work",
            "photography is a personal interest of {name}",
        ),
    ),
)


def sample_irrelevant_facts(
    name: str,
    rng: random.Random,
    *,
    count: int = 2,
) -> list[dict[str, str]]:
    """Sample JSON-ready facts without adding them to formal candidate attributes."""
    if count < 0 or count > len(IRRELEVANT_FACT_POOL):
        raise ValueError(f"Invalid irrelevant fact count: {count}")
    selected = rng.sample(list(IRRELEVANT_FACT_POOL), count)
    return [
        {
            "key": fact.key,
            "text": rng.choice(fact.templates).format(name=name),
        }
        for fact in selected
    ]


def render_irrelevant_fact_sentence(facts: list[dict[str, str]]) -> str:
    """Render sampled background facts as a clearly non-evaluative sentence."""
    texts = [fact["text"] for fact in facts]
    if not texts:
        return ""
    if len(texts) == 1:
        return f"As background information, {texts[0]}."
    return f"As background information, {', and '.join(texts)}."
