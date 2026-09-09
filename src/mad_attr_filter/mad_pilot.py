"""Selection, prompts, and response records for the small baseline MAD pilot."""

from __future__ import annotations

import json
import random
import threading
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from mad_attr_filter.io import read_jsonl
from mad_attr_filter.single_agent import VALID_OPTIONS, model_alias, parse_model_response

ROUND_ZERO_PROMPT = """Solve the following multiple-choice problem independently.

Carefully evaluate every stated requirement and determine which candidate satisfies all of them.

Provide your answer and a concise explanation of your reasoning.

Return only valid JSON:

{{
  "answer": "A",
  "reasoning": "Briefly explain your reasoning.",
  "confidence": 0.85
}}

Rules:
- answer must be exactly A, B, C, or D;
- confidence must be between 0 and 1;
- do not use Markdown;
- solve the problem independently.

Problem:

{question}
"""

DEBATE_PROMPT = """You previously answered the problem as follows:

Your previous answer:
{own_previous_answer}

Your previous reasoning:
{own_previous_reasoning}

The other agents independently gave the following responses:

{peer_responses}

Reconsider the original problem in light of these responses.

You may keep your original answer or revise it.

Evaluate the requirements carefully rather than following another agent merely because it agrees with a majority.

Return only valid JSON:

{{
  "answer": "A",
  "reasoning": "Briefly explain your current reasoning.",
  "confidence": 0.85
}}

Problem:

{question}
"""


def select_mad_pilot_manifest(
    candidates: Sequence[Mapping[str, Any]],
    *,
    stable_control_count: int,
    seed: int,
) -> list[dict[str, Any]]:
    """Select all vulnerable items plus deterministic, stratified stable controls."""
    vulnerable = [
        candidate
        for candidate in candidates
        if candidate.get("screening_category") in {"mixed_correctness", "mildly_vulnerable"}
    ]
    vulnerable.sort(
        key=lambda candidate: (
            0 if candidate.get("mad_priority") == "high" else 1,
            str(candidate["item_id"]),
        )
    )
    stable = [candidate for candidate in candidates if candidate.get("screening_category") == "stable_correct"]
    if len(stable) < stable_control_count:
        raise ValueError(
            f"Requested {stable_control_count} stable controls, but only {len(stable)} are available"
        )

    rng = random.Random(seed)
    shuffled = list(stable)
    rng.shuffle(shuffled)
    selected_stable: list[Mapping[str, Any]] = []
    selected_ids: set[str] = set()
    scenarios = ("expert_recruitment", "project_assignment", "availability_selection")
    complexities = ("low", "medium", "high")
    for scenario in scenarios:
        for complexity in complexities:
            match = next(
                (
                    candidate
                    for candidate in shuffled
                    if str(candidate["item_id"]) not in selected_ids
                    and candidate.get("scenario") == scenario
                    and candidate.get("structural_complexity") == complexity
                ),
                None,
            )
            if match is not None and len(selected_stable) < stable_control_count:
                selected_stable.append(match)
                selected_ids.add(str(match["item_id"]))
    for candidate in shuffled:
        if len(selected_stable) >= stable_control_count:
            break
        item_id = str(candidate["item_id"])
        if item_id not in selected_ids:
            selected_stable.append(candidate)
            selected_ids.add(item_id)

    manifest: list[dict[str, Any]] = []
    for candidate in vulnerable:
        wrong_signatures = dict(candidate.get("observed_wrong_violation_signatures", {}))
        reasons = [str(candidate["screening_category"])]
        if candidate.get("mad_priority") == "high":
            reasons.append("high_mad_priority")
        if any(len(signature) == 1 for signature in wrong_signatures.values()):
            reasons.append("single_constraint_error")
        manifest.append(
            {
                "item_id": candidate["item_id"],
                "pilot_group": "vulnerable",
                "screening_category": candidate["screening_category"],
                "mad_priority": candidate.get("mad_priority"),
                "empirical_accuracy": candidate["empirical_accuracy"],
                "single_agent_wrong_options": list(candidate.get("observed_wrong_options", [])),
                "single_agent_wrong_violation_signatures": wrong_signatures,
                "selection_reason": reasons,
                "scenario": candidate.get("scenario"),
                "structural_complexity": candidate.get("structural_complexity"),
                "option_closeness": candidate.get("option_closeness"),
                "num_constraints": candidate.get("num_constraints"),
            }
        )
    for candidate in selected_stable:
        manifest.append(
            {
                "item_id": candidate["item_id"],
                "pilot_group": "stable_control",
                "screening_category": "stable_correct",
                "mad_priority": "low",
                "empirical_accuracy": candidate["empirical_accuracy"],
                "single_agent_wrong_options": [],
                "single_agent_wrong_violation_signatures": {},
                "selection_reason": ["stable_correct", "stratified_control_selection"],
                "scenario": candidate.get("scenario"),
                "structural_complexity": candidate.get("structural_complexity"),
                "option_closeness": candidate.get("option_closeness"),
                "num_constraints": candidate.get("num_constraints"),
            }
        )
    return manifest


def build_round_zero_prompt(question: str) -> str:
    """Build an independent Round 0 prompt containing only the natural-language problem."""
    return ROUND_ZERO_PROMPT.format(question=question)


def _display_answer(response: Mapping[str, Any]) -> str:
    answer = response.get("answer")
    return str(answer) if answer in VALID_OPTIONS else "UNPARSED"


def _display_reasoning(response: Mapping[str, Any]) -> str:
    reasoning = str(response.get("reasoning", "")).strip()
    return reasoning or "No parseable reasoning was returned."


def build_debate_prompt(
    question: str,
    *,
    own_agent_id: str,
    previous_round: Mapping[str, Mapping[str, Any]],
) -> tuple[str, list[dict[str, Any]]]:
    """Build a revision prompt from the previous responses of all three agents."""
    if own_agent_id not in previous_round:
        raise KeyError(f"Missing previous response for {own_agent_id}")
    own = previous_round[own_agent_id]
    peers: list[dict[str, Any]] = []
    peer_blocks: list[str] = []
    for peer_id in sorted(previous_round):
        if peer_id == own_agent_id:
            continue
        peer = previous_round[peer_id]
        peer_answer = _display_answer(peer)
        peer_reasoning = _display_reasoning(peer)
        peers.append({"agent_id": peer_id, "answer": peer.get("answer"), "reasoning": peer.get("reasoning", "")})
        peer_blocks.append(f"Agent {peer_id}:\nAnswer: {peer_answer}\nReasoning: {peer_reasoning}")
    prompt = DEBATE_PROMPT.format(
        own_previous_answer=_display_answer(own),
        own_previous_reasoning=_display_reasoning(own),
        peer_responses="\n\n".join(peer_blocks),
        question=question,
    )
    return prompt, peers


def build_mad_response_record(
    *,
    sample: Mapping[str, Any],
    manifest_record: Mapping[str, Any],
    model_config: Mapping[str, Any],
    agent_id: str,
    round_number: int,
    seed: int,
    prompt: str,
    peer_context: Sequence[Mapping[str, Any]],
    generation_config: Mapping[str, Any],
    raw_response: str,
    api_metadata: Mapping[str, Any],
    request_error: str | None,
) -> dict[str, Any]:
    """Build one agent-round record and attach deterministic violations."""
    if request_error is None:
        parsed = parse_model_response(raw_response)
    else:
        parsed = {
            "answer": None,
            "reasoning": "",
            "confidence": None,
            "parse_success": False,
            "strict_json_success": False,
            "fallback_parse_success": False,
            "parse_error": request_error,
        }
    answer = parsed.get("answer")
    valid_answer = answer if answer in VALID_OPTIONS else None
    gold_answer = str(sample["gold_answer"])
    violations = (
        list(sample["option_violation_signature"][valid_answer]) if valid_answer is not None else []
    )
    return {
        "item_id": sample["item_id"],
        "model_family": model_alias(model_config),
        "model_name": model_config["model_name"],
        "pilot_group": manifest_record["pilot_group"],
        "agent_id": agent_id,
        "round": round_number,
        "seed": seed,
        "answer": valid_answer,
        "gold_answer": gold_answer,
        "correct": valid_answer == gold_answer,
        "reasoning": parsed.get("reasoning", ""),
        "confidence": parsed.get("confidence"),
        "parse_success": parsed.get("parse_success", False),
        "strict_json_success": parsed.get("strict_json_success", False),
        "fallback_parse_success": parsed.get("fallback_parse_success", False),
        "parse_error": parsed.get("parse_error"),
        "raw_response": raw_response,
        "violation_signature": violations,
        "prompt": prompt,
        "peer_context": [dict(peer) for peer in peer_context],
        "generation_config": {
            "temperature": float(generation_config["temperature"]),
            "top_p": float(generation_config["top_p"]),
            "max_tokens": int(generation_config["max_tokens"]),
            "thinking_enabled": bool(model_config.get("thinking_enabled", False)),
            "seed_requested": True,
        },
        "metadata": {
            "request_error": request_error,
            "api_metadata": dict(api_metadata),
            "base_url": model_config.get("base_url"),
        },
    }


def progress_key(record: Mapping[str, Any]) -> tuple[str, str, str, int]:
    """Return the checkpoint identity for one MAD call."""
    return (
        str(record["item_id"]),
        str(record["model_family"]),
        str(record["agent_id"]),
        int(record["round"]),
    )


def load_mad_progress(path: str | Path) -> dict[tuple[str, str, str, int], dict[str, Any]]:
    """Load progress records, retaining the latest record for duplicate keys."""
    progress_path = Path(path)
    if not progress_path.exists():
        return {}
    return {progress_key(record): record for record in read_jsonl(progress_path)}


def append_progress_record(path: str | Path, record: Mapping[str, Any], lock: threading.Lock) -> None:
    """Append and flush one checkpoint under a process-local lock."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(dict(record), ensure_ascii=False, sort_keys=True)
    with lock:
        with output_path.open("a", encoding="utf-8") as file:
            file.write(serialized)
            file.write("\n")
            file.flush()
