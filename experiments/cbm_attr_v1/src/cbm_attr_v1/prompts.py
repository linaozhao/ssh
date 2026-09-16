"""English prompts and losslessly reconstructible message builders."""

from __future__ import annotations

from typing import Any

from cbm_attr_v1.common import LABELS

SET_SYSTEM_PROMPT = """You are tracking eligibility under accumulating evidence.

The requirements are fixed. At each round, return the candidates who have NOT YET BEEN ELIMINATED by the currently active evidence.

Rules:
- Exclude a candidate only when an observed active fact violates at least one requirement.
- If a required attribute has not been reported for a candidate, it is unknown. Unknown is not false and is not proof that the requirement is satisfied; the candidate remains not yet eliminated.
- A RESTATEMENT repeats an existing fact and does not change it.
- A CORRECTION withdraws the named earlier evidence and replaces it with the corrected fact.
- Use only evidence revealed up to the current round.

Return only valid JSON:
{"candidates": ["A", "C"], "reasoning": "Briefly explain the current exclusions."}

The candidates array must contain each retained label exactly once, using only A, B, C, or D. Its order does not matter. Do not include confidence or Markdown."""

ORIGINAL_PROMPT = """Solve the following multiple-choice problem independently.

Carefully evaluate every stated requirement and determine which candidate satisfies all of them.

Provide your answer and a concise explanation of your reasoning.

Return only valid JSON in the following format:

{{
  "answer": "A",
  "reasoning": "Briefly explain how you checked the relevant requirements.",
  "confidence": 0.85
}}

Rules:
- "answer" must be exactly one of A, B, C, or D.
- "confidence" must be a number between 0 and 1.
- Do not use Markdown.
- Do not refer to other agents.
- Solve the problem independently.

Problem:

{question}"""


def requirements_text(item: dict[str, Any]) -> str:
    """Render fixed requirements and candidate label-name mapping."""
    reqs = "\n".join(
        f"{index}. {constraint['natural_language']}"
        for index, constraint in enumerate(item["constraints"], start=1)
    )
    names = "\n".join(f"{label}. {item['entities'][label]['name']}" for label in LABELS)
    return f"Requirements:\n{reqs}\n\nCandidates:\n{names}"


def render_fact(fact: dict[str, Any]) -> str:
    """Render one evidence event without exposing formal attributes or oracle labels."""
    if fact["fact_kind"] == "non_target":
        return f"- {fact['text']}."
    if fact["event_type"] == "restatement":
        return f"- RESTATEMENT of {fact['restates_evidence_id']}: {fact['text']}."
    if fact["event_type"] == "correction":
        return (
            f"- CORRECTION: withdraw {fact['replaces_evidence_id']} and replace it with: "
            f"{fact['text']}."
        )
    return f"- Evidence {fact['evidence_id']}: {fact['text']}."


def dynamic_user_message(
    item: dict[str, Any], condition: str, round_data: dict[str, Any], *, first_round: bool
) -> str:
    """Build one dynamic user turn."""
    evidence = "\n".join(render_fact(fact) for fact in round_data["events"])
    prefix = f"{requirements_text(item)}\n\n" if first_round else ""
    return (
        f"{prefix}Evidence update, round {round_data['round_id']}:\n{evidence}\n\n"
        "Based on all currently active evidence, which candidates have not yet been eliminated?"
    )


def snapshot_message(item: dict[str, Any], snapshot: dict[str, Any]) -> str:
    """Build an independent static snapshot request from active evidence only."""
    facts = "\n".join(f"- {fact['text']}." for fact in snapshot["visible_facts"])
    return (
        f"{requirements_text(item)}\n\nCurrent evidence snapshot:\n{facts}\n\n"
        "Based only on this snapshot, which candidates have not yet been eliminated?"
    )


def source_set_message(item: dict[str, Any]) -> str:
    """Build the one-shot full-source set task."""
    facts: list[str] = []
    for label in LABELS:
        entity = item["entities"][label]
        facts.extend(f"- {fact['text']}." for fact in entity["displayed_facts"])
        facts.extend(f"- {fact['text']}." for fact in entity.get("non_target_facts", []))
    return (
        f"{requirements_text(item)}\n\nAll currently available evidence:\n"
        + "\n".join(facts)
        + "\n\nWhich candidates have not yet been eliminated?"
    )
