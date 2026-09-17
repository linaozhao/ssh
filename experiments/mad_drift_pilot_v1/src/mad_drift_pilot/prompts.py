"""Frozen prompts for protocol checking, MAD, and self-revision controls."""

from __future__ import annotations

from typing import Any, Mapping


SET_SYSTEM_PROMPT_V2 = """You are tracking eligibility under accumulating evidence.

The requirements are fixed. At each round, return the candidates who have NOT YET BEEN ELIMINATED by the currently active evidence.

Rules:
- Exclude a candidate only when an observed active fact violates at least one requirement.
- If a required attribute has not been reported for a candidate, it is unknown. Unknown is not false and is not proof that the requirement is satisfied; the candidate remains not yet eliminated.
- A RESTATEMENT repeats an existing fact and does not change it.
- A CORRECTION withdraws the named earlier evidence and replaces it with the corrected fact.
- Use only formal evidence revealed up to the current round.

Return only one valid JSON object with exactly two fields:
- candidates: an array containing every retained candidate label exactly once; each label must be one of A, B, C, or D; array order does not matter.
- reasoning: a short string explaining the current exclusions.

Do not include confidence, Markdown, or any additional fields."""


STATIC_ORIGINAL_PROMPT = """Solve the following multiple-choice problem independently.

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


STATIC_MAD_REVISION = """Reconsider your current answer to the multiple-choice problem.

The following are peer viewpoints, not additional problem facts:

{peers}

Check every original requirement against the candidates. You may keep or revise your answer. Base the decision on the problem facts, not on agreement or majority.

Return only valid JSON with answer, reasoning, and confidence using the same schema as before. Do not use Markdown."""


STATIC_SELF_REVISION = """Review your current answer to the multiple-choice problem once more.

No new problem facts have been provided. Check every original requirement against the candidates. You may keep or revise your answer based on the problem facts.

Return only valid JSON with answer, reasoning, and confidence using the same schema as before. Do not use Markdown."""


SET_MAD_REVISION = """Review your current retained-candidate set using all currently active formal evidence.

The following are peer viewpoints, not formal evidence and cannot add, withdraw, or correct any fact:

{peers}

Check every fixed requirement. You may keep or revise your set. Base the decision on formal evidence, not on agreement or majority.

Return only one valid JSON object using the required candidates and reasoning fields."""


SET_SELF_REVISION = """Review your current retained-candidate set using all currently active formal evidence.

No new formal evidence has been provided. Check every fixed requirement. You may keep or revise your set based only on formal evidence.

Return only one valid JSON object using the required candidates and reasoning fields."""


def response_summary(agent_id: str, record: Mapping[str, Any], *, set_protocol: bool) -> str:
    """Render a peer response without treating it as formal evidence."""
    parsed = record.get("parse", {})
    if set_protocol:
        answer = parsed.get("candidates") if parsed.get("recognized") else "UNRECOGNIZED"
        label = f"Retained candidates: {answer}"
    else:
        answer = parsed.get("answer") if parsed.get("recognized") else "UNRECOGNIZED"
        label = f"Answer: {answer}"
    reasoning = parsed.get("reasoning") or "No parseable reasoning was supplied."
    return f"Peer {agent_id}\n{label}\nReasoning: {reasoning}"


def peer_block(records: Mapping[str, Mapping[str, Any]], own_agent: str, *, set_protocol: bool) -> str:
    """Render only previous-round responses from the other two agents."""
    return "\n\n".join(
        response_summary(agent_id, records[agent_id], set_protocol=set_protocol)
        for agent_id in sorted(records)
        if agent_id != own_agent
    )

