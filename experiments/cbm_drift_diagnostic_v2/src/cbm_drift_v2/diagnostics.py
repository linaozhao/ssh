"""Deterministic state diagnostics and Judge package construction."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import re
from typing import Any

from cbm_drift_v2.common import read_jsonl, sha256_json, write_json, write_jsonl

DIAGNOSTIC_VERSION = "cbm_drift_v2.program_diagnostic.1"


def outcome(row: dict[str, Any]) -> str:
    """Classify response observability separately from correctness."""
    if not row.get("api_success"):
        return "api_failure"
    if not row.get("recognized_answer"):
        return "unrecognized"
    return "valid_correct" if row.get("correct") else "valid_wrong"


def error_objects(row: dict[str, Any]) -> set[str]:
    """Represent answer-set errors as stable candidate-level objects."""
    if not row.get("recognized_answer"):
        return set()
    return {
        *(f"extra:{value}" for value in row.get("extra_candidates") or []),
        *(f"omitted:{value}" for value in row.get("omitted_candidates") or []),
    }


def _effect(previous: dict[str, Any] | None, current: dict[str, Any]) -> str:
    if previous is None or not previous.get("recognized_answer") or not current.get("recognized_answer"):
        return "uncertain" if previous is not None else "none"
    left, right = bool(previous["correct"]), bool(current["correct"])
    return {
        (True, False): "correct_to_wrong", (False, True): "wrong_to_correct",
        (False, False): "wrong_to_wrong", (True, True): "correct_to_correct",
    }[(left, right)]


def _temporal(
    previous: dict[str, Any] | None,
    current: dict[str, Any],
    prior_error_objects: set[str],
    formal_oracle_changed: bool,
) -> str:
    if not current.get("recognized_answer"):
        return "uncertain"
    if previous is None:
        return "correct_maintenance" if current.get("correct") else "initial_error"
    if current.get("correct"):
        if formal_oracle_changed and previous.get("predicted_candidates") != current.get("predicted_candidates"):
            return "reasonable_update"
        return "correct_maintenance" if previous.get("correct") else "corrected"
    current_errors = error_objects(current)
    previous_errors = error_objects(previous)
    if previous.get("correct"):
        return "recurrence" if current_errors & prior_error_objects else "newly_introduced"
    if current_errors & previous_errors:
        return "persistent"
    if current_errors & prior_error_objects:
        return "recurrence"
    return "newly_introduced"


def build_message_diagnostics(sequences: list[dict[str, Any]], outputs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Score every public MAD message against its contemporaneous standard state."""
    by_variant = {row["variant_id"]: row for row in sequences}
    by_agent: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in outputs:
        by_agent[(row["variant_id"], row["agent_id"])].append(row)
    diagnostics: list[dict[str, Any]] = []
    for key in sorted(by_agent):
        prior: dict[str, Any] | None = None
        ever_errors: set[str] = set()
        rows = sorted(by_agent[key], key=lambda value: (int(value["evidence_stage"]), int(value["round"])))
        for row in rows:
            sequence = by_variant[row["variant_id"]]
            state = sequence["stage_states"][int(row["evidence_stage"]) - 1]
            prior_state = None
            if prior is not None:
                prior_state = sequence["stage_states"][int(prior["evidence_stage"]) - 1]
            formal_changed = bool(prior_state and prior_state["oracle"] != state["oracle"])
            errors = error_objects(row)
            violated = {
                candidate: state["exclusions"].get(candidate, [])
                for candidate in (row.get("extra_candidates") or [])
            }
            peer_alignment = []
            if prior is not None and row.get("predicted_candidates") != prior.get("predicted_candidates"):
                for peer_id in row.get("visible_peer_message_ids", []):
                    peer = next((value for value in outputs if value["message_id"] == peer_id), None)
                    if peer and peer.get("predicted_candidates") == row.get("predicted_candidates"):
                        peer_alignment.append(peer_id)
            diagnostics.append({
                "message_id": row["message_id"], "request_id": row["request_id"],
                "base_item_id": row["base_item_id"], "family_id": row["family_id"],
                "variant_id": row["variant_id"], "variant_type": row["variant_type"],
                "trajectory_id": row["trajectory_id"], "evidence_stage": row["evidence_stage"],
                "round": row["round"], "agent_id": row["agent_id"],
                "outcome": outcome(row), "oracle": state["oracle"],
                "prediction": row.get("predicted_candidates"),
                "extra_candidates": row.get("extra_candidates"),
                "omitted_candidates": row.get("omitted_candidates"),
                "extra_candidate_violations": violated,
                "error_objects": sorted(errors),
                "new_error_objects": sorted(errors - error_objects(prior or {})),
                "continued_error_objects": sorted(errors & error_objects(prior or {})),
                "resolved_error_objects": sorted(error_objects(prior or {}) - errors),
                "formal_oracle_changed_since_previous_output": formal_changed,
                "comparison_scope": "within_stage" if prior and prior["evidence_stage"] == row["evidence_stage"] else "across_stage" if prior else "initial",
                "answer_effect": _effect(prior, row),
                "temporal_status": _temporal(prior, row, ever_errors, formal_changed),
                "related_peer_message_ids_by_answer_alignment": sorted(peer_alignment),
                "diagnostic_version": DIAGNOSTIC_VERSION,
            })
            ever_errors.update(errors)
            prior = row
    return sorted(diagnostics, key=lambda row: (row["variant_id"], row["evidence_stage"], row["round"], row["agent_id"]))


def build_program_events(diagnostics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge contiguous same-agent/same-object answer errors into auditable events."""
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in diagnostics:
        grouped[(row["variant_id"], row["agent_id"])].append(row)
    events: list[dict[str, Any]] = []
    team_first: dict[tuple[str, str], str] = {}
    for row in sorted(diagnostics, key=lambda value: (value["variant_id"], value["evidence_stage"], value["round"], value["agent_id"])):
        for object_id in row["error_objects"]:
            team_first.setdefault((row["variant_id"], object_id), row["message_id"])
    for key in sorted(grouped):
        active: dict[str, dict[str, Any]] = {}
        seen: set[str] = set()
        for row in sorted(grouped[key], key=lambda value: (value["evidence_stage"], value["round"])):
            current = set(row["error_objects"])
            for object_id in sorted(set(active) - current):
                events.append(active.pop(object_id))
            for object_id in sorted(current):
                if object_id not in active:
                    event_id = "program:" + sha256_json([row["variant_id"], row["agent_id"], object_id, row["message_id"]])[:20]
                    event = {
                        "event_id": event_id, "base_item_id": row["base_item_id"],
                        "variant_id": row["variant_id"], "trajectory_id": row["trajectory_id"],
                        "agent_id": row["agent_id"], "error_object": object_id,
                        "temporal_status_at_start": "recurrence" if object_id in seen else row["temporal_status"],
                        "first_message_id": row["message_id"], "observations": [],
                        "has_explicit_prior_correct_judgment": row["answer_effect"] == "correct_to_wrong",
                        "team_first_observed_message_id": team_first.setdefault((row["variant_id"], object_id), row["message_id"]),
                        "merge_basis": "deterministic contiguous same-agent and same candidate-level answer error",
                        "label_source": "program_state_comparison",
                    }
                    active[object_id] = event
                    seen.add(object_id)
                active[object_id]["observations"].append({
                    "message_id": row["message_id"], "evidence_stage": row["evidence_stage"],
                    "round": row["round"], "answer_effect": row["answer_effect"],
                })
        events.extend(active.values())
    for event in events:
        event["related_cross_agent_event_ids"] = sorted(
            other["event_id"] for other in events
            if other["event_id"] != event["event_id"]
            and other["variant_id"] == event["variant_id"]
            and other["error_object"] == event["error_object"]
            and other["agent_id"] != event["agent_id"]
        )
    return sorted(events, key=lambda row: row["event_id"])


def build_judge_packages(
    sequences: list[dict[str, Any]], outputs: list[dict[str, Any]], diagnostics: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Package every message, including correct and unchanged outputs, for both Judges."""
    by_variant = {row["variant_id"]: row for row in sequences}
    by_message = {row["message_id"]: row for row in diagnostics}
    packages = []
    for row in sorted(outputs, key=lambda value: value["message_id"]):
        sequence = by_variant[row["variant_id"]]
        state = sequence["stage_states"][int(row["evidence_stage"]) - 1]
        history = [message for message in row["messages"] if message["role"] != "system"]
        peer_ids = set(row.get("visible_peer_message_ids", []))
        for message in row["messages"]:
            peer_ids.update(re.findall(r"Peer message ([^\s]+) from agent_[123]:", message["content"]))
        packages.append({
            "package_id": f"judge:{row['message_id']}", "message_id": row["message_id"],
            "base_item_id": row["base_item_id"], "variant_id": row["variant_id"],
            "trajectory_id": row["trajectory_id"], "evidence_stage": row["evidence_stage"],
            "round": row["round"], "agent_id": row["agent_id"],
            "task_text": sequence["task_text"],
            "rule_id_legend": [
                {"rule_id": rule["id"], "natural_language": rule["natural_language"]}
                for rule in sequence["rules"]
            ],
            "formal_evidence": [
                {"evidence_id": event["evidence_id"], "text": event["text"]}
                for event in state["active_evidence"]
            ],
            "visible_history": history,
            "visible_peer_message_ids": sorted(peer_ids),
            "current_message_text": row["raw_response"],
            "reference_structure": {
                "rules": sequence["rules"], "active_evidence": state["active_evidence"],
                "oracle": state["oracle"], "exclusions": state["exclusions"],
                "program_check": by_message[row["message_id"]],
            },
            "package_sha256": sha256_json({
                "message_id": row["message_id"], "messages": row["messages"],
                "current": row["raw_response"], "state": state,
            }),
        })
    return packages


def analyze_program(root: Path) -> dict[str, Any]:
    """Create all deterministic diagnostics and Judge inputs."""
    sequences = read_jsonl(root / "data/evidence_sequences.jsonl")
    outputs = read_jsonl(root / "results/mad/raw_outputs.jsonl")
    diagnostics = build_message_diagnostics(sequences, outputs)
    events = build_program_events(diagnostics)
    packages = build_judge_packages(sequences, outputs, diagnostics)
    write_jsonl(root / "results/program/message_diagnostics.jsonl", diagnostics)
    write_jsonl(root / "results/program/program_events.jsonl", events)
    write_jsonl(root / "results/judge/judge_input_packages.jsonl", packages)
    summary = {
        "messages": len(diagnostics), "events": len(events),
        "outcomes": dict(sorted(Counter(row["outcome"] for row in diagnostics).items())),
        "temporal_status": dict(sorted(Counter(row["temporal_status"] for row in diagnostics).items())),
        "answer_effect": dict(sorted(Counter(row["answer_effect"] for row in diagnostics).items())),
        "judge_packages": len(packages),
    }
    write_json(root / "results/program/summary.json", summary)
    return summary
