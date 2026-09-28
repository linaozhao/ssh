"""Evidence replay and exact not-yet-eliminated candidate-set solver."""

from __future__ import annotations

import copy
import itertools
from collections.abc import Iterable, Mapping
from typing import Any

from cbm_drift_v2.common import LABELS


class EvidenceReplayError(ValueError):
    """Raised when an evidence log contains an invalid update operation."""


def replay_evidence(events: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Replay observations, restatements, and explicit superseding corrections."""
    active: dict[str, dict[str, Any]] = {}
    seen: dict[str, dict[str, Any]] = {}
    active_target_key: dict[tuple[str, str], str] = {}
    for source in events:
        event = copy.deepcopy(dict(source))
        evidence_id = str(event["evidence_id"])
        if evidence_id in seen:
            raise EvidenceReplayError(f"duplicate evidence_id: {evidence_id}")
        seen[evidence_id] = event
        event_type = event["event_type"]
        if event_type == "restatement":
            target = str(event.get("restates_evidence_id") or "")
            if target not in seen:
                raise EvidenceReplayError(f"restatement references unknown evidence: {target}")
            continue
        if event_type == "correction":
            target = str(event.get("supersedes_evidence_id") or "")
            if target not in active:
                raise EvidenceReplayError(f"correction supersedes inactive evidence: {target}")
            old = active.pop(target)
            if old.get("fact_kind") != "target":
                raise EvidenceReplayError("corrections may only supersede target evidence")
            old_key = (str(old["candidate_id"]), str(old["attribute"]))
            if old_key != (str(event["candidate_id"]), str(event["attribute"])):
                raise EvidenceReplayError("correction must preserve candidate and attribute")
            active_target_key.pop(old_key, None)
        elif event_type != "observation":
            raise EvidenceReplayError(f"unsupported event_type: {event_type}")

        if event.get("fact_kind") == "target":
            key = (str(event["candidate_id"]), str(event["attribute"]))
            prior_id = active_target_key.get(key)
            if prior_id is not None:
                raise EvidenceReplayError(f"target fact {key} already active without correction")
            active_target_key[key] = evidence_id
        active[evidence_id] = event
    return {
        "active_evidence": sorted(active.values(), key=lambda row: str(row["evidence_id"])),
        "superseded_evidence_ids": sorted(set(seen) - set(active) - {row["evidence_id"] for row in seen.values() if row["event_type"] == "restatement"}),
    }


def solve_candidate_set(
    rules: Iterable[Mapping[str, Any]], active_evidence: Iterable[Mapping[str, Any]]
) -> dict[str, Any]:
    """Keep every candidate without an active, known rule violation."""
    target = {
        (str(row["candidate_id"]), str(row["attribute"])): row
        for row in active_evidence
        if row.get("fact_kind") == "target"
    }
    retained: list[str] = []
    exclusions: dict[str, list[dict[str, Any]]] = {}
    for candidate in LABELS:
        violations = []
        for rule in rules:
            fact = target.get((candidate, str(rule["attribute"])))
            if fact is not None and bool(fact["value"]) != bool(rule["required_value"]):
                violations.append({
                    "candidate_id": candidate,
                    "rule_id": str(rule["id"]),
                    "attribute": str(rule["attribute"]),
                    "required_value": bool(rule["required_value"]),
                    "observed_value": bool(fact["value"]),
                    "evidence_id": str(fact["evidence_id"]),
                })
        if violations:
            exclusions[candidate] = violations
        else:
            retained.append(candidate)
    return {"oracle": retained, "exclusions": exclusions}


def enumerate_candidate_set(
    rules: Iterable[Mapping[str, Any]], active_evidence: Iterable[Mapping[str, Any]]
) -> list[str]:
    """Cross-check the open-world oracle by enumerating all unknown completions."""
    rule_rows = list(rules)
    active = {
        (str(row["candidate_id"]), str(row["attribute"])): bool(row["value"])
        for row in active_evidence
        if row.get("fact_kind") == "target"
    }
    retained: list[str] = []
    for candidate in LABELS:
        unknown = [row for row in rule_rows if (candidate, str(row["attribute"])) not in active]
        possible = False
        for values in itertools.product((False, True), repeat=len(unknown)):
            completion = {
                (candidate, str(rule["attribute"])): value
                for rule, value in zip(unknown, values, strict=True)
            }
            if all(
                active.get((candidate, str(rule["attribute"])), completion.get((candidate, str(rule["attribute"]))))
                == bool(rule["required_value"])
                for rule in rule_rows
            ):
                possible = True
                break
        if possible:
            retained.append(candidate)
    return retained


def replay_stages(rules: list[dict[str, Any]], stages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Replay cumulative stage events and independently recompute every standard state."""
    cumulative: list[dict[str, Any]] = []
    output = []
    for stage in stages:
        cumulative.extend(copy.deepcopy(stage["events"]))
        replay = replay_evidence(cumulative)
        solved = solve_candidate_set(rules, replay["active_evidence"])
        output.append({
            "evidence_stage": int(stage["evidence_stage"]),
            "stage_event_ids": [row["evidence_id"] for row in stage["events"]],
            "active_evidence": replay["active_evidence"],
            "superseded_evidence_ids": replay["superseded_evidence_ids"],
            "oracle": solved["oracle"],
            "exclusions": solved["exclusions"],
        })
    return output
