"""Open-world Boolean evidence replay and independent candidate-state checks."""

from __future__ import annotations

import copy
import itertools
from collections.abc import Iterable, Mapping
from typing import Any

from .common import LABELS, sha256_json


class EvidenceReplayError(ValueError):
    """An evidence operation references an invalid fact/version."""


def replay_evidence(events: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Apply only named corrections, without treating unknowns as false."""
    active: dict[str, dict[str, Any]] = {}
    seen: dict[str, dict[str, Any]] = {}
    keys: dict[tuple[str, str], str] = {}
    superseded = []
    for source in events:
        event = copy.deepcopy(dict(source))
        eid = event["evidence_id"]
        if eid in seen:
            raise EvidenceReplayError(f"Duplicate evidence: {eid}")
        if event["event_type"] == "restatement":
            previous = active.get(event.get("restates_evidence_id"))
            if previous is None:
                raise EvidenceReplayError("Restatement must reference a currently active earlier fact")
            for key in ("candidate_id", "attribute", "value", "fact_kind"):
                if key in event and event[key] != previous.get(key):
                    raise EvidenceReplayError(f"Restatement changes {key}")
            seen[eid] = event
            continue
        if event["event_type"] == "correction":
            old_id = event.get("supersedes_evidence_id")
            old = active.get(old_id)
            if old is None or old.get("fact_kind") != "target":
                raise EvidenceReplayError("Correction must name active target evidence")
            if event.get("fact_kind") != "target" or any(event[k] != old[k] for k in ("candidate_id", "attribute")):
                raise EvidenceReplayError("Correction changes candidate or attribute")
            del active[old_id]
            del keys[(old["candidate_id"], old["attribute"])]
            superseded.append(old_id)
        elif event["event_type"] != "observation":
            raise EvidenceReplayError("Unsupported evidence event")
        if event.get("fact_kind") == "target":
            if type(event.get("value")) is not bool or event.get("candidate_id") not in LABELS:
                raise EvidenceReplayError("Target must have a Boolean value and valid candidate")
            key = (event["candidate_id"], event["attribute"])
            if key in keys:
                raise EvidenceReplayError("Duplicate active fact without explicit correction")
            keys[key] = eid
        seen[eid] = event
        active[eid] = event
    return {"active_evidence": sorted(active.values(), key=lambda r: r["evidence_id"]),
            "superseded_evidence_ids": sorted(superseded)}


def candidate_rule_states(rules: Iterable[Mapping[str, Any]], active: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Return three-valued state for every candidate-rule object."""
    rules = list(rules)
    facts = {(r["candidate_id"], r["attribute"]): r for r in active if r.get("fact_kind") == "target"}
    output = []
    for candidate in LABELS:
        for rule in rules:
            fact = facts.get((candidate, rule["attribute"]))
            status = "unknown" if fact is None else "known_satisfied" if fact["value"] == rule["required_value"] else "known_violated"
            output.append({"candidate_id": candidate, "rule_id": rule["id"], "attribute": rule["attribute"],
                           "status": status, "required_value": rule["required_value"],
                           "observed_value": fact["value"] if fact else None, "evidence_id": fact["evidence_id"] if fact else None})
    return output


def solve_candidate_set(rules: Iterable[Mapping[str, Any]], active_evidence: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Retain exactly candidates with no known active requirement violation."""
    states = candidate_rule_states(rules, active_evidence)
    exclusions = {}
    for row in states:
        if row["status"] == "known_violated":
            exclusions.setdefault(row["candidate_id"], []).append({k: v for k, v in row.items() if k != "status"})
    return {"oracle": [c for c in LABELS if c not in exclusions], "exclusions": exclusions}


def enumerate_candidate_set(rules: Iterable[Mapping[str, Any]], active_evidence: Iterable[Mapping[str, Any]]) -> list[str]:
    """Independently enumerate unknown completions to verify the solver."""
    rules = list(rules)
    facts = {(r["candidate_id"], r["attribute"]): r["value"] for r in active_evidence if r.get("fact_kind") == "target"}
    retained = []
    for candidate in LABELS:
        missing = [r["attribute"] for r in rules if (candidate, r["attribute"]) not in facts]
        for values in itertools.product((False, True), repeat=len(missing)):
            completion = dict(zip(missing, values))
            if all(facts.get((candidate, r["attribute"]), completion.get(r["attribute"])) == r["required_value"] for r in rules):
                retained.append(candidate)
                break
    return retained


def replay_stages(rules: list[dict[str, Any]], stages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Recompute every prefix; no oracle copied from old experiment outputs."""
    cumulative, states = [], []
    for index, stage in enumerate(stages, 1):
        if stage["evidence_stage"] != index:
            raise EvidenceReplayError("Stages must be consecutive")
        if any(e.get("appearance_stage", index) != index for e in stage["events"]):
            raise EvidenceReplayError("Event stage mismatch")
        cumulative.extend(copy.deepcopy(stage["events"]))
        replay = replay_evidence(cumulative)
        solved = solve_candidate_set(rules, replay["active_evidence"])
        states.append({"evidence_stage": index, "stage_event_ids": [e["evidence_id"] for e in stage["events"]],
                       **replay, **solved,
                       "candidate_rule_states": candidate_rule_states(rules, replay["active_evidence"]),
                       "state_sha256": sha256_json(replay)})
    return states


def score_answer(rules: list[dict[str, Any]], active: list[dict[str, Any]], answer: list[str] | None) -> dict[str, Any]:
    """Keep unreadable output distinct from an empty, valid answer."""
    solved = solve_candidate_set(rules, active)
    valid = isinstance(answer, list) and all(a in LABELS for a in answer) and len(set(answer)) == len(answer)
    return {**solved, "answer_status": "unrecognized" if not valid else "correct" if set(answer) == set(solved["oracle"]) else "incorrect",
            "extra": sorted(set(answer) - set(solved["oracle"])) if valid else None,
            "omitted": sorted(set(solved["oracle"]) - set(answer)) if valid else None}
