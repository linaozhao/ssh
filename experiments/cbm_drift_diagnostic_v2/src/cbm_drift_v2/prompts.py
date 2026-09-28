"""Frozen task, MAD, and Judge prompt protocols."""

from __future__ import annotations

import json
from typing import Any

from cbm_drift_v2.common import LABELS

TASK_SYSTEM_PROMPT = """You are tracking candidate eligibility under accumulating formal evidence.

Your answer must contain every candidate who has NOT YET BEEN ELIMINATED by the currently active evidence.

Rules:
- Exclude a candidate only when an active observed fact violates at least one fixed requirement.
- If a required attribute has not been reported, it is unknown. Unknown is not a violation, and the candidate remains not yet eliminated.
- A RESTATEMENT does not change active evidence.
- A CORRECTION explicitly withdraws the named old evidence and replaces it with the new evidence.
- Statements from peer agents are opinions, not formal evidence. They may help you check your reasoning but cannot replace formal evidence.
- Use no evidence from a future stage.

Return only one valid JSON object. It must have an answer_set field containing distinct candidate labels and an explanation field containing a brief justification. Labels may only be A, B, C, or D. The answer set may contain multiple candidates or be empty. Do not include confidence or Markdown."""

MAD_REVISION_PROMPT = """Review the current answer using the fixed requirements and all formal evidence available through this stage.

The following are peer opinions from the immediately preceding discussion round. They are not formal evidence:
{peer_block}

Keep your answer if it remains justified, or revise it if the evidence supports a change. Return only the required JSON object."""

JUDGE_DIRECT_SYSTEM = """You are producing a diagnostic pre-annotation of one public agent message. Analyze only observable text and supplied evidence. Do not infer hidden cognition or causation. Quoted or rejected peer claims are not automatically the speaker's own claims. Return only JSON matching the requested schema."""

JUDGE_STRUCTURED_SYSTEM = """You are producing a reference-structure-assisted diagnostic pre-annotation of one public agent message. The supplied formal state is authoritative reference information for this analysis. Analyze observable text only; do not infer hidden cognition or causation. Return only JSON matching the requested schema."""


def render_event(event: dict[str, Any]) -> str:
    """Render one formal evidence operation without internal oracle fields."""
    if event["fact_kind"] == "non_target":
        return f"- Evidence {event['evidence_id']}: {event['text']}."
    if event["event_type"] == "restatement":
        return f"- RESTATEMENT of {event['restates_evidence_id']}: {event['text']}."
    if event["event_type"] == "correction":
        return (
            f"- CORRECTION: withdraw {event['supersedes_evidence_id']} and replace it with "
            f"Evidence {event['evidence_id']}: {event['text']}."
        )
    return f"- Evidence {event['evidence_id']}: {event['text']}."


def stage_user_message(sequence: dict[str, Any], stage: int, *, include_task: bool) -> str:
    """Render the formal evidence delivered at one stage."""
    stage_row = sequence["stages"][stage - 1]
    prefix = f"{sequence['task_text']}\n\n" if include_task else ""
    evidence = "\n".join(render_event(row) for row in stage_row["events"])
    return (
        f"{prefix}Formal evidence update T{stage}:\n{evidence}\n\n"
        "Which candidates have not yet been eliminated under the currently active evidence?"
    )


def snapshot_user_message(sequence: dict[str, Any], stage: int) -> str:
    """Render an independent current-state snapshot with no prior model response."""
    state = sequence["stage_states"][stage - 1]
    evidence = "\n".join(
        f"- Evidence {row['evidence_id']}: {row['text']}." for row in state["active_evidence"]
    )
    return (
        f"{sequence['task_text']}\n\nCurrent active evidence through T{stage}:\n{evidence}\n\n"
        "Which candidates have not yet been eliminated under this evidence?"
    )


def peer_block(peer_rows: list[dict[str, Any]]) -> str:
    """Render actual peer messages with stable IDs and explicit provenance."""
    return "\n".join(
        f"Peer message {row['message_id']} from {row['agent_id']}:\n{row['raw_response']}"
        for row in sorted(peer_rows, key=lambda value: value["agent_id"])
    )


def judge_user_message(package: dict[str, Any], *, structured: bool) -> str:
    """Render a Judge request; structured mode explicitly exposes reference checks."""
    schema = {
        "has_diagnostic_event": "boolean",
        "temporal_status": "initial_error/newly_introduced/persistent/corrected/recurrence/reasonable_update/correct_maintenance/uncertain",
        "content_labels": ["factual_deviation/rule_deviation/inference_application_error/unresolved"],
        "claims": [{
            "quote": "exact substring from current_message_text",
            "stance": "asserted/quoted/rejected/hypothetical/uncertain",
            "target_entity_ids": ["candidate labels"],
            "violated_fact_ids": ["evidence IDs"],
            "violated_rule_ids": ["rule IDs"],
        }],
        "answer_effect": "none/correct_to_wrong/wrong_to_correct/wrong_to_wrong/correct_to_correct/uncertain",
        "related_peer_message_ids": ["visible peer message IDs"],
        "uncertainty_reason": "string or null",
    }
    materials = {
        "task_text": package["task_text"],
        "fixed_rule_id_legend": package["rule_id_legend"],
        "formal_evidence_through_current_stage": package["formal_evidence"],
        "visible_public_history": package["visible_history"],
        "current_message_id": package["message_id"],
        "current_message_text": package["current_message_text"],
    }
    if structured:
        materials["reference_structure_assistance"] = package["reference_structure"]
    return (
        "Assess the current message for observable content deviations and temporal status. "
        "An incorrect answer alone does not determine a content label. For every claim, copy the quote "
        "verbatim from current_message_text: never summarize, normalize, or paraphrase it. Do not calculate "
        "character offsets; the evaluator derives them from each unique exact quote. Include only claims needed "
        "to support or qualify the diagnostic decision, not an inventory of every non-diagnostic statement. "
        "Make the decision directly without restating the full trajectory. Use only C-style rule IDs "
        "from fixed_rule_id_legend (for example C1), never bare ordinal numbers. If no exact diagnostic quote "
        "can be supported, return an empty claims list and explain the uncertainty.\n\n"
        f"Materials:\n{json.dumps(materials, ensure_ascii=False, indent=2)}\n\n"
        f"Required output schema:\n{json.dumps(schema, ensure_ascii=False, indent=2)}"
    )


def contains_concrete_answer_example() -> bool:
    """Return whether the task protocol accidentally supplies a concrete answer set."""
    compact = TASK_SYSTEM_PROMPT.replace(" ", "")
    return any(f'["{left}","{right}"]' in compact for left in LABELS for right in LABELS)
