"""Frozen MAD protocol: formal evidence and legally visible peer text only."""

from __future__ import annotations

from typing import Any

PROMPT_VERSION = "shared-history-r2-v1"
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


def render_event(event: dict[str, Any]) -> str:
    """Render evidence operations, not internal classification or standard answers."""
    if event["event_type"] == "restatement":
        return f"- RESTATEMENT of {event['restates_evidence_id']}: {event['text']}."
    if event["event_type"] == "correction":
        return f"- CORRECTION: withdraw {event['supersedes_evidence_id']} and replace it with Evidence {event['evidence_id']}: {event['text']}."
    return f"- Evidence {event['evidence_id']}: {event['text']}."


def stage_user_message(sequence: dict[str, Any], stage: int, *, include_task: bool) -> str:
    """Deliver just the new stage, keeping prior actual conversation intact."""
    prefix = sequence["task_text"] + "\n\n" if include_task else ""
    evidence = "\n".join(render_event(e) for e in sequence["stages"][stage - 1]["events"])
    return f"{prefix}Formal evidence update T{stage}:\n{evidence}\n\nWhich candidates have not yet been eliminated under the currently active evidence?"


def snapshot_user_message(sequence: dict[str, Any], stage: int) -> str:
    """An independent static protocol check, never reused as MAD history."""
    facts = "\n".join(f"- Evidence {r['evidence_id']}: {r['text']}." for r in sequence["stage_states"][stage - 1]["active_evidence"])
    return f"{sequence['task_text']}\n\nCurrent active evidence through T{stage}:\n{facts}\n\nWhich candidates have not yet been eliminated under this evidence?"


def peer_block(peer_rows: list[dict[str, Any]]) -> str:
    """Include actual allowed responses with opaque message IDs."""
    return "\n".join(f"Peer message {r['message_id']} from {r['agent_id']}:\n{r['raw_response']}" for r in sorted(peer_rows, key=lambda r: r["agent_id"]))
