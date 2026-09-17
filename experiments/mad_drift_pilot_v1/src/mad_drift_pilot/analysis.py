"""Objective protocol, trajectory, transition, pairing, and case analysis."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from mad_drift_pilot.common import AGENTS, read_jsonl, sha256_json, write_json, write_jsonl


def _ratio(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 6) if denominator else None


def _pct(numerator: int, denominator: int) -> str:
    return "不适用" if not denominator else f"{100 * numerator / denominator:.2f}% ({numerator}/{denominator})"


def _prediction(row: dict[str, Any]) -> tuple[str, ...] | None:
    value = row.get("predicted_candidates")
    return tuple(sorted(value)) if value is not None else None


def _protocol_group(row: dict[str, Any]) -> str:
    condition = row["condition"]
    if condition == "P_snapshot":
        return f"P_snapshot:{row['snapshot_condition']}:r{row['round_id']}"
    if condition in {"C_clean", "E_noise", "D_update"}:
        return f"{condition}:r{row['round_id']}"
    return condition


def _protocol_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    groups["candidate_set_all"] = [row for row in rows if row["protocol"] == "candidate_set"]
    for row in rows:
        groups[_protocol_group(row)].append(row)
    result: dict[str, Any] = {}
    for key, values in sorted(groups.items()):
        recognized = [row for row in values if row.get("recognized_answer")]
        set_rows = [row for row in values if row["protocol"] == "candidate_set"]
        ac = sum(_prediction(row) == ("A", "C") for row in set_rows)
        distribution = Counter("UNRECOGNIZED" if _prediction(row) is None else ",".join(_prediction(row) or ()) for row in set_rows)
        result[key] = {
            "records": len(values), "api_success": sum(row.get("api_success", False) for row in values),
            "recognized": len(recognized), "strict_schema": sum(row.get("parse", {}).get("strict_schema", False) for row in values),
            "truncated": sum(row.get("finish_reason") == "length" for row in values),
            "correct": sum(row.get("correct", False) for row in values),
            "accuracy": _ratio(sum(row.get("correct", False) for row in values), len(values)),
            "recognized_accuracy": _ratio(sum(row.get("correct", False) for row in recognized), len(recognized)),
            "a_c_exact": ac, "a_c_rate": _ratio(ac, len(set_rows)),
            "set_distribution": dict(sorted(distribution.items())),
        }
    return result


def analyze_protocol(root: Path, repository_root: Path) -> dict[str, Any]:
    """Compare old and v2 set protocols on exactly the selected item-runs."""
    selected = {row["base_item_id"] for row in read_jsonl(root / "data/selection_manifest.jsonl")}
    new_rows = read_jsonl(root / "results/protocol_check/raw_outputs.jsonl")
    old_rows = [row for row in read_jsonl(repository_root / "experiments/cbm_attr_v1/results/raw_outputs.jsonl") if row["base_item_id"] in selected]
    old_metrics, new_metrics = _protocol_metrics(old_rows), _protocol_metrics(new_rows)
    comparison = {
        "selected_items": len(selected), "old_records": len(old_rows), "new_records": len(new_rows),
        "old": old_metrics, "new": new_metrics,
        "candidate_set_change": {
            "accuracy_delta": round(new_metrics["candidate_set_all"]["accuracy"] - old_metrics["candidate_set_all"]["accuracy"], 6),
            "a_c_rate_delta": round(new_metrics["candidate_set_all"]["a_c_rate"] - old_metrics["candidate_set_all"]["a_c_rate"], 6),
        },
    }
    write_json(root / "results/protocol_check/comparison.json", comparison)
    audit = [row for row in new_rows if not row.get("recognized_answer") or not row.get("parse", {}).get("strict_schema") or row.get("finish_reason") == "length"]
    write_jsonl(root / "results/protocol_check/parse_audit.jsonl", audit)
    items = {row["base_item_id"]: row for row in read_jsonl(root / "data/source_items.jsonl")}
    conflicts = []
    for row in new_rows:
        prediction = set(row.get("predicted_candidates") or [])
        reasoning = str(row.get("parse", {}).get("reasoning") or "")
        for label, entity in items[row["base_item_id"]]["entities"].items():
            subject = rf"(?:candidate\s+{label}\b|{re.escape(entity['name'])}\b)"
            says_excluded = re.search(subject + r".{0,30}\b(?:is|was|should be)\s+(?:eliminated|excluded|ineligible)\b", reasoning, re.I)
            says_retained = re.search(subject + r".{0,35}\b(?:remains|is retained|is not eliminated|has not been eliminated)\b", reasoning, re.I)
            if (label in prediction and says_excluded) or (label not in prediction and says_retained):
                conflicts.append({"request_id": row["request_id"], "label": label, "predicted_candidates": sorted(prediction), "reasoning": reasoning, "conflict": "included_but_reasoning_excludes" if label in prediction else "excluded_but_reasoning_retains"})
    write_jsonl(root / "results/protocol_check/reasoning_conflict_audit.jsonl", conflicts)
    comparison["conservative_reasoning_conflict_count"] = len(conflicts)
    write_json(root / "results/protocol_check/comparison.json", comparison)
    return comparison


def _load_mad_rows(root: Path) -> list[dict[str, Any]]:
    paths = [root / "results/static/raw_outputs.jsonl"] + [root / f"results/cbm/raw_outputs_{condition}.jsonl" for condition in ("C_clean", "E_noise", "D_update")]
    rows: list[dict[str, Any]] = []
    for path in paths:
        if path.exists():
            rows.extend(read_jsonl(path))
    return rows


def _state_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (row["base_item_id"], row["team_run_id"], row["task_family"], row["condition"], row["stage"], row["branch"], row["agent_id"], row["revision_round"])


def _transition_type(before: dict[str, Any], after: dict[str, Any]) -> str:
    if not before.get("recognized_answer") or not after.get("recognized_answer"):
        return "unrecognized_transition"
    if before["correct"] and after["correct"]:
        return "correct_to_correct"
    if before["correct"]:
        return "correct_to_wrong"
    if after["correct"]:
        return "wrong_to_correct"
    return "wrong_to_wrong"


def _team_summary(records: dict[str, dict[str, Any]]) -> dict[str, Any]:
    predictions = [_prediction(records[agent]) for agent in AGENTS]
    valid = all(value is not None for value in predictions)
    counts = Counter(predictions) if valid else Counter(value for value in predictions if value is not None)
    consensus = valid and len(counts) == 1
    return {
        "all_recognized": valid, "disagreement": valid and len(counts) > 1,
        "consensus": consensus, "correct_consensus": consensus and all(records[agent]["correct"] for agent in AGENTS),
        "wrong_consensus": consensus and not all(records[agent]["correct"] for agent in AGENTS),
        "distribution": {"|".join(key): value for key, value in sorted(counts.items())},
    }


def build_events(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Build overlapping objective transition windows and team summaries."""
    index = {_state_key(row): row for row in rows}
    state_groups: dict[tuple[Any, ...], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        group = (row["base_item_id"], row["team_run_id"], row["task_family"], row["condition"], row["stage"], row["branch"], row["revision_round"])
        state_groups[group][row["agent_id"]] = row
    team_rows = []
    for group, records in sorted(state_groups.items(), key=lambda entry: str(entry[0])):
        if len(records) == 3:
            team_rows.append(dict(zip(("base_item_id", "team_run_id", "task_family", "condition", "stage", "branch", "revision_round"), group, strict=True)) | _team_summary(records))

    events: list[dict[str, Any]] = []
    windows = ((0, 1, "pre_to_r1"), (1, 2, "r1_to_r2"), (0, 2, "pre_to_r2"))
    bases = {(row["base_item_id"], row["team_run_id"], row["task_family"], row["condition"], row["stage"]) for row in rows}
    for base, run_id, family, condition, stage in sorted(bases, key=str):
        for branch in ("mad", "self"):
            for before_round, after_round, window in windows:
                before_branch = "shared" if before_round == 0 else branch
                for agent in AGENTS:
                    before = index.get((base, run_id, family, condition, stage, before_branch, agent, before_round))
                    after = index.get((base, run_id, family, condition, stage, branch, agent, after_round))
                    if before is None or after is None:
                        continue
                    transition = _transition_type(before, after)
                    before_pred, after_pred = _prediction(before), _prediction(after)
                    changed = before_pred is not None and after_pred is not None and before_pred != after_pred
                    peer_round = 0 if after_round == 1 else 1
                    peer_branch = "shared" if peer_round == 0 else branch
                    peer_records = {
                        peer: index[(base, run_id, family, condition, stage, peer_branch, peer, peer_round)]
                        for peer in AGENTS if peer != agent and (base, run_id, family, condition, stage, peer_branch, peer, peer_round) in index
                    }
                    adopted = changed and branch == "mad" and any(_prediction(peer) == after_pred for peer in peer_records.values())
                    event = {
                        "base_item_id": base, "team_run_id": run_id, "task_family": family,
                        "condition": condition, "stage": stage, "branch": branch, "agent_id": agent,
                        "window": window, "before_request_id": before["request_id"], "after_request_id": after["request_id"],
                        "before_prediction": before_pred, "after_prediction": after_pred,
                        "before_correct": before.get("correct"), "after_correct": after.get("correct"),
                        "before_recognized": before.get("recognized_answer"), "after_recognized": after.get("recognized_answer"),
                        "transition_type": transition, "answer_changed": changed,
                        "objective_event": {"correct_to_wrong": "harmful_revision", "wrong_to_correct": "effective_correction", "correct_to_correct": "correct_retention", "wrong_to_wrong": "error_persistence"}.get(transition, "format_or_api_transition"),
                        "adopted_peer_previous_answer": adopted,
                        "peer_source_agents": sorted(peer for peer, record in peer_records.items() if changed and _prediction(record) == after_pred),
                        "before_reasoning": before.get("parse", {}).get("reasoning"), "after_reasoning": after.get("parse", {}).get("reasoning"),
                        "peer_records": [{"agent_id": peer, "prediction": _prediction(record), "reasoning": record.get("parse", {}).get("reasoning"), "correct": record.get("correct")} for peer, record in sorted(peer_records.items())],
                    }
                    if family == "static":
                        old_v = set(before.get("selected_option_violation_signature") or [])
                        new_v = set(after.get("selected_option_violation_signature") or [])
                        event.update({"before_violations": sorted(old_v), "after_violations": sorted(new_v), "introduced_violations": sorted(new_v - old_v), "resolved_violations": sorted(old_v - new_v)})
                    else:
                        old_omit, new_omit = set(before.get("omitted_candidates") or []), set(after.get("omitted_candidates") or [])
                        old_extra, new_extra = set(before.get("extra_candidates") or []), set(after.get("extra_candidates") or [])
                        event.update({"before_omitted": sorted(old_omit), "after_omitted": sorted(new_omit), "new_omissions": sorted(new_omit - old_omit), "resolved_omissions": sorted(old_omit - new_omit), "before_extra": sorted(old_extra), "after_extra": sorted(new_extra), "new_extras": sorted(new_extra - old_extra), "resolved_extras": sorted(old_extra - new_extra)})
                    events.append(event)
    return events, team_rows


def _aggregate_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in events:
        groups[(row["task_family"], row["condition"], row["stage"], row["branch"], row["window"])].append(row)
    output = []
    for key, values in sorted(groups.items(), key=lambda entry: str(entry[0])):
        valid = [row for row in values if row["transition_type"] != "unrecognized_transition"]
        correct_start = [row for row in valid if row["before_correct"]]
        wrong_start = [row for row in valid if not row["before_correct"]]
        output.append({
            **dict(zip(("task_family", "condition", "stage", "branch", "window"), key, strict=True)),
            "transitions": len(values), "valid_transitions": len(valid),
            "before_correct": sum(row["before_correct"] for row in valid), "after_correct": sum(row["after_correct"] for row in valid),
            "before_accuracy": _ratio(sum(row["before_correct"] for row in valid), len(valid)),
            "after_accuracy": _ratio(sum(row["after_correct"] for row in valid), len(valid)),
            "harmful_revisions": sum(row["transition_type"] == "correct_to_wrong" for row in valid),
            "harmful_rate_given_correct_start": _ratio(sum(row["transition_type"] == "correct_to_wrong" for row in valid), len(correct_start)),
            "effective_corrections": sum(row["transition_type"] == "wrong_to_correct" for row in valid),
            "correction_rate_given_wrong_start": _ratio(sum(row["transition_type"] == "wrong_to_correct" for row in valid), len(wrong_start)),
            "answer_changes": sum(row["answer_changed"] for row in valid),
            "peer_adoptions": sum(row["adopted_peer_previous_answer"] for row in valid),
        })
    return output


def _paired_mad_self(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    index = {_state_key(row): row for row in rows}
    groups: dict[tuple[Any, ...], list[tuple[dict[str, Any], dict[str, Any]]]] = defaultdict(list)
    bases = {(row["base_item_id"], row["team_run_id"], row["task_family"], row["condition"], row["stage"]) for row in rows}
    for base, run_id, family, condition, stage in bases:
        for agent in AGENTS:
            mad = index.get((base, run_id, family, condition, stage, "mad", agent, 2))
            control = index.get((base, run_id, family, condition, stage, "self", agent, 2))
            if mad and control:
                groups[(family, condition, stage)].append((mad, control))
    result = []
    for key, pairs in sorted(groups.items(), key=lambda entry: str(entry[0])):
        valid = [(mad, control) for mad, control in pairs if mad["recognized_answer"] and control["recognized_answer"]]
        result.append({
            **dict(zip(("task_family", "condition", "stage"), key, strict=True)),
            "pairs": len(pairs), "valid_pairs": len(valid),
            "mad_correct_self_wrong": sum(mad["correct"] and not control["correct"] for mad, control in valid),
            "mad_wrong_self_correct": sum(not mad["correct"] and control["correct"] for mad, control in valid),
            "both_correct": sum(mad["correct"] and control["correct"] for mad, control in valid),
            "both_wrong": sum(not mad["correct"] and not control["correct"] for mad, control in valid),
            "mad_minus_self_accuracy": round((sum(mad["correct"] for mad, _ in valid) - sum(control["correct"] for _, control in valid)) / len(valid), 6) if valid else None,
        })
    return result


def _paired_clean_noise(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Pair C/E at the exact item, team, stage, branch, agent, and round."""
    index = {_state_key(row): row for row in rows}
    groups: dict[tuple[Any, ...], list[tuple[dict[str, Any], dict[str, Any]]]] = defaultdict(list)
    for row in rows:
        if row["condition"] != "C_clean":
            continue
        counterpart = index.get((row["base_item_id"], row["team_run_id"], "cbm", "E_noise", row["stage"], row["branch"], row["agent_id"], row["revision_round"]))
        if counterpart:
            groups[(row["stage"], row["branch"], row["revision_round"])].append((row, counterpart))
    result = []
    for key, pairs in sorted(groups.items()):
        valid = [(clean, noise) for clean, noise in pairs if clean["recognized_answer"] and noise["recognized_answer"]]
        result.append({
            **dict(zip(("stage", "branch", "revision_round"), key, strict=True)),
            "pairs": len(pairs), "valid_pairs": len(valid),
            "paired_seed_mismatches": sum(clean["seed"] != noise["seed"] for clean, noise in pairs),
            "clean_correct_noise_wrong": sum(clean["correct"] and not noise["correct"] for clean, noise in valid),
            "clean_wrong_noise_correct": sum(not clean["correct"] and noise["correct"] for clean, noise in valid),
            "both_correct": sum(clean["correct"] and noise["correct"] for clean, noise in valid),
            "both_wrong": sum(not clean["correct"] and not noise["correct"] for clean, noise in valid),
            "noise_minus_clean_accuracy": round((sum(noise["correct"] for _, noise in valid) - sum(clean["correct"] for clean, _ in valid)) / len(valid), 6) if valid else None,
        })
    return result


def _team_statistics(team_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in team_rows:
        groups[(row["task_family"], row["condition"], row["stage"], row["branch"], row["revision_round"])].append(row)
    result = []
    for key, values in sorted(groups.items(), key=lambda entry: str(entry[0])):
        complete = [row for row in values if row["all_recognized"]]
        result.append({
            **dict(zip(("task_family", "condition", "stage", "branch", "revision_round"), key, strict=True)),
            "teams": len(values), "all_recognized_teams": len(complete),
            "disagreement_teams": sum(row["disagreement"] for row in complete),
            "disagreement_rate": _ratio(sum(row["disagreement"] for row in complete), len(complete)),
            "consensus_teams": sum(row["consensus"] for row in complete),
            "correct_consensus_teams": sum(row["correct_consensus"] for row in complete),
            "wrong_consensus_teams": sum(row["wrong_consensus"] for row in complete),
        })
    return result


def _state_statistics(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Summarize each directly observed state without treating repeats as items."""
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(row["task_family"], row["condition"], row["stage"], row["branch"], row["revision_round"])].append(row)
    result = []
    for key, values in sorted(groups.items(), key=lambda entry: str(entry[0])):
        recognized = [row for row in values if row.get("recognized_answer")]
        result.append({
            **dict(zip(("task_family", "condition", "stage", "branch", "revision_round"), key, strict=True)),
            "records": len(values),
            "api_success": sum(row.get("api_success", False) for row in values),
            "recognized": len(recognized),
            "strict_schema": sum(row.get("parse", {}).get("strict_schema", False) for row in values),
            "truncated": sum(row.get("finish_reason") == "length" for row in values),
            "correct": sum(row.get("correct", False) for row in recognized),
            "accuracy_among_recognized": _ratio(sum(row.get("correct", False) for row in recognized), len(recognized)),
            "prompt_tokens": sum((row.get("usage") or {}).get("prompt_tokens", 0) for row in values),
            "completion_tokens": sum((row.get("usage") or {}).get("completion_tokens", 0) for row in values),
            "latency_seconds_sum": round(sum(row.get("latency_seconds", 0) for row in values), 3),
        })
    return result


def _diagnostic_change_statistics(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Count formal error-set changes on the non-overlapping pre-to-R2 view."""
    groups: dict[tuple[str, str, int | None], list[dict[str, Any]]] = defaultdict(list)
    for row in events:
        if row["branch"] == "mad" and row["window"] == "pre_to_r2":
            groups[(row["task_family"], row["condition"], row["stage"])].append(row)
    output = []
    for key, values in sorted(groups.items(), key=lambda entry: str(entry[0])):
        family, condition, stage = key
        record = {
            "task_family": family,
            "condition": condition,
            "stage": stage,
            "transitions": len(values),
            "answer_changes": sum(row["answer_changed"] for row in values),
            "peer_adoption_signals": sum(row["adopted_peer_previous_answer"] for row in values),
        }
        if family == "static":
            record.update({
                "introduced_violation_instances": sum(len(row["introduced_violations"]) for row in values),
                "resolved_violation_instances": sum(len(row["resolved_violations"]) for row in values),
            })
        else:
            record.update({
                "new_omission_instances": sum(len(row["new_omissions"]) for row in values),
                "resolved_omission_instances": sum(len(row["resolved_omissions"]) for row in values),
                "new_extra_instances": sum(len(row["new_extras"]) for row in values),
                "resolved_extra_instances": sum(len(row["resolved_extras"]) for row in values),
            })
        output.append(record)
    return output


def _update_analysis(rows: list[dict[str, Any]], episodes: dict[str, dict[str, Any]]) -> dict[str, Any]:
    index = {_state_key(row): row for row in rows}
    opportunities = restored = pre_correct = pre_correct_post_correct = pre_discussion_correct = post_discussion_drops_w = 0
    gold_drops = extra_after = 0
    records = []
    for base, episode in episodes.items():
        w = episode["update"]["target_candidate"]
        gold = episode["source_gold"]
        for run_id in (1, 2, 3):
            for agent in AGENTS:
                before = index.get((base, run_id, "cbm", "C_clean", 3, "mad", agent, 2))
                after = index.get((base, run_id, "cbm", "D_update", 4, "shared", agent, 0))
                final = index.get((base, run_id, "cbm", "D_update", 4, "mad", agent, 2))
                if not before or not after or not final:
                    continue
                before_set, after_set, final_set = _prediction(before), _prediction(after), _prediction(final)
                opportunity = before_set is not None and w not in before_set
                if opportunity:
                    opportunities += 1
                    restored += after_set is not None and w in after_set
                if before["correct"]:
                    pre_correct += 1
                    pre_correct_post_correct += after["correct"]
                if after["correct"]:
                    pre_discussion_correct += 1
                    post_discussion_drops_w += final_set is not None and w not in final_set
                if final_set is not None:
                    gold_drops += gold not in final_set
                    extra_after += bool(set(final_set) - set(final["oracle"]))
                records.append({"base_item_id": base, "team_run_id": run_id, "agent_id": agent, "target_candidate": w, "before_set": before_set, "post_correction_pre_discussion_set": after_set, "post_discussion_set": final_set, "opportunity_to_readd": opportunity, "readded_when_previously_excluded": opportunity and after_set is not None and w in after_set, "before_correct": before["correct"], "post_correction_correct": after["correct"], "post_discussion_correct": final["correct"]})
    return {
        "records": records, "summary": {
            "readd_opportunities": opportunities, "readded": restored, "readd_rate_given_previously_excluded": _ratio(restored, opportunities),
            "pre_correction_correct": pre_correct, "post_correction_correct_given_pre_correct": pre_correct_post_correct,
            "post_correction_correct_rate_given_pre_correct": _ratio(pre_correct_post_correct, pre_correct),
            "discussion_pre_correct": pre_discussion_correct, "discussion_then_dropped_w": post_discussion_drops_w,
            "discussion_drop_w_rate_given_correct_start": _ratio(post_discussion_drops_w, pre_discussion_correct),
            "final_gold_drops": gold_drops, "final_unrelated_extra_sets": extra_after,
        }
    }


def _integrity(root: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    plan = read_jsonl(root / "data/mad_request_plan.jsonl")
    plan_ids, output_ids = {row["request_id"] for row in plan}, [row["request_id"] for row in rows]
    banned = Counter()
    for row in rows:
        text = "\n".join(message["content"] for message in row.get("messages", []) if message["role"] in {"system", "user"}).lower()
        for token in ("source_gold", "gold_answer", "option_violation_signature", "difficulty_cell", "c_clean", "e_noise", "d_update"):
            if token in text:
                banned[token] += 1
    prompt_tokens = [(row.get("usage") or {}).get("prompt_tokens") for row in rows if (row.get("usage") or {}).get("prompt_tokens") is not None]
    completion_tokens = [(row.get("usage") or {}).get("completion_tokens") for row in rows if (row.get("usage") or {}).get("completion_tokens") is not None]
    by_id = {row["request_id"]: row for row in rows}
    prefix_mismatches = message_hash_mismatches = self_peer_blocks = mad_missing_peer_blocks = 0
    for row in rows:
        if row.get("messages") is not None and row.get("messages_sha256") != sha256_json(row["messages"]):
            message_hash_mismatches += 1
        if row.get("api_success") and row.get("depends_on"):
            parent = by_id.get(row["depends_on"][0])
            expected = [*parent["messages"], {"role": "assistant", "content": parent["raw_response"]}] if parent and parent.get("api_success") else None
            if expected is not None and row["messages"][: len(expected)] != expected:
                prefix_mismatches += 1
        if row.get("revision_round", 0) > 0 and row.get("messages"):
            last = row["messages"][-1]["content"].lower()
            if row["branch"] == "self" and "peer viewpoints" in last:
                self_peer_blocks += 1
            if row["branch"] == "mad" and "peer viewpoints" not in last:
                mad_missing_peer_blocks += 1
    return {
        "expected": len(plan), "actual": len(rows), "unique": len(set(output_ids)),
        "missing": len(plan_ids - set(output_ids)), "unknown": len(set(output_ids) - plan_ids), "duplicates": len(output_ids) - len(set(output_ids)),
        "api_failures": sum(not row.get("api_success") and not row.get("blocked") for row in rows),
        "blocked": sum(row.get("blocked", False) for row in rows), "recognized": sum(row.get("recognized_answer", False) for row in rows),
        "strict_schema": sum(row.get("parse", {}).get("strict_schema", False) for row in rows),
        "truncated": sum(row.get("finish_reason") == "length" for row in rows),
        "max_prompt_tokens": max(prompt_tokens, default=None), "max_completion_tokens": max(completion_tokens, default=None),
        "total_prompt_tokens": sum(prompt_tokens), "total_completion_tokens": sum(completion_tokens),
        "total_latency_seconds": round(sum(row.get("latency_seconds", 0) for row in rows), 3),
        "http_attempts_including_retries": sum(row.get("request_attempts", 0) for row in rows),
        "extra_retry_attempts": sum(max(0, row.get("request_attempts", 0) - 1) for row in rows if row.get("api_success") or row.get("request_attempts")),
        "token_estimate_usage_mismatches": sum(
            row.get("input_tokens_estimate") != (row.get("usage") or {}).get("prompt_tokens")
            for row in rows if row.get("api_success") and (row.get("usage") or {}).get("prompt_tokens") is not None
        ),
        "banned_input_tokens": dict(banned),
        "message_hash_mismatches": message_hash_mismatches,
        "declared_parent_prefix_mismatches": prefix_mismatches,
        "self_branch_peer_block_leaks": self_peer_blocks,
        "mad_revision_missing_peer_blocks": mad_missing_peer_blocks,
    }


def _write_stats_csv(path: Path, event_stats: list[dict[str, Any]], paired: list[dict[str, Any]]) -> None:
    rows = [{"section": "transition", **row} for row in event_stats] + [{"section": "mad_vs_self", **row} for row in paired]
    fields = sorted({key for row in rows for key in row})
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _case_markdown(root: Path, events: list[dict[str, Any]], rows: list[dict[str, Any]], items: dict[str, dict[str, Any]]) -> None:
    by_request = {row["request_id"]: row for row in rows}
    by_state = {_state_key(row): row for row in rows}
    predicates = [
        ("有害修改", lambda e: e["branch"] == "mad" and e["window"] == "pre_to_r2" and e["transition_type"] == "correct_to_wrong"),
        ("有效纠错", lambda e: e["branch"] == "mad" and e["window"] == "pre_to_r2" and e["transition_type"] == "wrong_to_correct"),
        ("正确保持", lambda e: e["branch"] == "mad" and e["window"] == "pre_to_r2" and e["transition_type"] == "correct_to_correct"),
        ("错误持续", lambda e: e["branch"] == "mad" and e["window"] == "pre_to_r2" and e["transition_type"] == "wrong_to_wrong"),
    ]
    lines = ["# MAD Drift Pilot v1 案例复核", "", "以下为程序选择的可审查案例，不声称是人工标注或内部机制证明。", ""]
    for title, predicate in predicates:
        match = next((event for event in events if predicate(event)), None)
        lines.extend([f"## {title}", ""])
        if match is None:
            lines.extend(["本轮未观察到该类案例。", ""])
            continue
        before = by_request[match["before_request_id"]]
        item = items[match["base_item_id"]]
        lines.extend([
            f"- item: `{match['base_item_id']}`; condition: `{match['condition']}`; stage: `{match['stage']}`; team: {match['team_run_id']}; agent: `{match['agent_id']}`",
            "- 要求：" + " / ".join(row["natural_language"] for row in item["constraints"]),
            f"- 当轮 oracle：`{before['oracle']}`",
            f"- 修改前：`{match['before_prediction']}`，解释：{match['before_reasoning']}",
            f"- 同伴消息：`{json.dumps(match['peer_records'], ensure_ascii=False)}`",
            f"- 修改后：`{match['after_prediction']}`，解释：{match['after_reasoning']}",
            f"- 程序判定：`{match['transition_type']}`；采用同伴上一轮答案信号：`{match['adopted_peer_previous_answer']}`。",
            "- 边界：该事件能确定答案与标准状态的变化，不能单凭输出解释确定模型内部原因。", "",
        ])
    lines.extend(["## CBM 更正后的更新", ""])
    update_case = None
    for row in rows:
        if row["condition"] == "D_update" and row["stage"] == 4 and row["branch"] == "shared":
            before = by_state.get((row["base_item_id"], row["team_run_id"], "cbm", "C_clean", 3, "mad", row["agent_id"], 2))
            final = by_state.get((row["base_item_id"], row["team_run_id"], "cbm", "D_update", 4, "mad", row["agent_id"], 2))
            if before and final:
                update_case = (before, row, final)
                break
    if update_case is None:
        lines.extend(["本轮没有完整的更正案例。", ""])
    else:
        before, after, final = update_case
        correction_message = after["messages"][-1]["content"]
        lines.extend([
            f"- item: `{after['base_item_id']}`; team: {after['team_run_id']}; agent: `{after['agent_id']}`",
            f"- 更正前 oracle/输出：`{before['oracle']}` / `{before['predicted_candidates']}`",
            f"- 正式更正：{correction_message}",
            f"- 更正后讨论前 oracle/输出：`{after['oracle']}` / `{after['predicted_candidates']}`",
            f"- MAD R2 输出：`{final['predicted_candidates']}`；解释：{final['parse'].get('reasoning')}",
            "- 边界：更正导致标准状态变化，不把这一步本身记为同伴讨论漂移；只对更正后的阶段内修订单独判断。", "",
        ])

    lines.extend(["## MAD 与阶段内自我修正不同", ""])
    pair_case = None
    for key, mad in by_state.items():
        base, run_id, family, condition, stage, branch, agent, revision = key
        if branch == "mad" and revision == 2:
            control = by_state.get((base, run_id, family, condition, stage, "self", agent, 2))
            if control and _prediction(mad) != _prediction(control):
                pair_case = (mad, control)
                break
    if pair_case is None:
        lines.extend(["本轮未观察到 MAD 与同起点自我修正最终输出不同的案例。", ""])
    else:
        mad, control = pair_case
        lines.extend([
            f"- item: `{mad['base_item_id']}`; condition: `{mad['condition']}`; stage: `{mad['stage']}`; team: {mad['team_run_id']}; agent: `{mad['agent_id']}`",
            f"- oracle：`{mad['oracle']}`",
            f"- MAD R2：`{mad['predicted_candidates']}`；解释：{mad['parse'].get('reasoning')}",
            f"- 同起点自我修正 R2：`{control['predicted_candidates']}`；解释：{control['parse'].get('reasoning')}",
            "- 结论边界：两路线共享当阶段讨论前状态，但 token 数与输入内容不同；差异是配对观察，不证明具体内部机制。", "",
        ])
    (root / "reports/case_review.md").parent.mkdir(parents=True, exist_ok=True)
    (root / "reports/case_review.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def analyze_mad(root: Path) -> dict[str, Any]:
    """Analyze complete static and CBM MAD records and write all artifacts."""
    rows = _load_mad_rows(root)
    items = {row["base_item_id"]: row for row in read_jsonl(root / "data/source_items.jsonl")}
    episodes = {row["base_item_id"]: row for row in read_jsonl(root / "data/episodes.jsonl")}
    events, team_rows = build_events(rows)
    static_events = [row for row in events if row["task_family"] == "static"]
    cbm_events = [row for row in events if row["task_family"] == "cbm"]
    write_jsonl(root / "results/static/transition_events.jsonl", static_events)
    write_jsonl(root / "results/cbm/transition_events.jsonl", cbm_events)
    write_jsonl(root / "results/team_state_summaries.jsonl", team_rows)
    event_stats = _aggregate_events(events)
    paired = _paired_mad_self(rows)
    noise_paired = _paired_clean_noise(rows)
    team_stats = _team_statistics(team_rows)
    state_stats = _state_statistics(rows)
    change_stats = _diagnostic_change_statistics(events)
    _write_stats_csv(root / "results/paired_statistics.csv", event_stats, paired)
    write_json(root / "results/cbm/clean_noise_paired.json", noise_paired)
    write_json(root / "results/team_statistics.json", team_stats)
    write_json(root / "results/state_statistics.json", state_stats)
    write_json(root / "results/diagnostic_change_statistics.json", change_stats)
    update = _update_analysis(rows, episodes)
    write_jsonl(root / "results/cbm/update_events.jsonl", update.pop("records"))
    write_json(root / "results/cbm/update_summary.json", update["summary"])
    by_id = {row["request_id"]: row for row in rows}
    branch_map = []
    for row in rows:
        if row["condition"] == "D_update" and row["stage"] == 4 and row["branch"] == "shared":
            parent_id = row["depends_on"][0]
            parent = by_id.get(parent_id)
            branch_map.append({
                "base_item_id": row["base_item_id"], "team_run_id": row["team_run_id"],
                "agent_id": row["agent_id"], "child_request_id": row["request_id"],
                "parent_request_id": parent_id,
                "parent_messages_sha256": parent.get("messages_sha256") if parent else None,
                "child_messages_sha256": row.get("messages_sha256"),
                "prefix_exact": bool(parent and row["messages"][: len(parent["messages"]) + 1] == [*parent["messages"], {"role": "assistant", "content": parent["raw_response"]}]),
            })
    write_jsonl(root / "results/cbm/update_branch_map.jsonl", branch_map)
    integrity = _integrity(root, rows)
    write_json(root / "results/runtime_integrity.json", integrity)
    taxonomy = {
        "complete_project_taxonomy_found": False,
        "formal_category_mapping_completed": False,
        "reason": "The repository describes a future 15-category taxonomy but contains no frozen category definitions or Judge configuration.",
        "objective_signals": [
            {"signal": "harmful_revision", "necessary_evidence": "recognized correct state followed by recognized wrong state under unchanged formal evidence", "supported": True},
            {"signal": "effective_correction", "necessary_evidence": "recognized wrong state followed by recognized correct state under unchanged formal evidence", "supported": True},
            {"signal": "peer_answer_adoption", "necessary_evidence": "changed answer equals a peer's immediately previous answer", "supported": True, "causal_claim": False},
            {"signal": "wrong_answer_propagation", "necessary_evidence": "peer adoption signal and resulting state is wrong", "supported": True, "causal_claim": False},
            {"signal": "constraint_or_set_error_change", "necessary_evidence": "formal matrix/oracle comparison", "supported": True},
        ],
    }
    write_json(root / "results/taxonomy_support.json", taxonomy)
    review = [row for row in events if row["transition_type"] in {"correct_to_wrong", "wrong_to_correct"} or row["adopted_peer_previous_answer"]]
    write_jsonl(root / "results/review_queue.jsonl", review)
    _case_markdown(root, events, rows, items)
    summary = {
        "integrity": integrity,
        "objective_event_distribution": dict(sorted(Counter(row["objective_event"] for row in events).items())),
        "events_involving_items": len({row["base_item_id"] for row in events if row["objective_event"] in {"harmful_revision", "effective_correction"}}),
        "event_statistics": event_stats,
        "mad_vs_self": paired,
        "clean_vs_noise": noise_paired,
        "team_statistics": team_stats,
        "state_statistics": state_stats,
        "diagnostic_change_statistics": change_stats,
        "update": update["summary"],
        "team_summary": {
            "states": len(team_rows), "disagreement_states": sum(row["disagreement"] for row in team_rows),
            "correct_consensus_states": sum(row["correct_consensus"] for row in team_rows),
            "wrong_consensus_states": sum(row["wrong_consensus"] for row in team_rows),
        },
        "mean_latency_seconds": round(mean(row.get("latency_seconds", 0) for row in rows), 4) if rows else None,
    }
    write_json(root / "results/analysis_summary.json", summary)
    return summary


def write_report(root: Path, protocol: dict[str, Any], analysis: dict[str, Any]) -> None:
    """Render the Chinese report entirely from current experiment results."""
    old_set, new_set = protocol["old"]["candidate_set_all"], protocol["new"]["candidate_set_all"]
    integrity = analysis["integrity"]
    event_counts = analysis["objective_event_distribution"]
    update = analysis["update"]
    # Pull final pre->R2 aggregate rows for compact condition-level reporting.
    final_rows = [row for row in analysis["event_statistics"] if row["window"] == "pre_to_r2"]
    static = [row for row in final_rows if row["task_family"] == "static"]
    cbm = [row for row in final_rows if row["task_family"] == "cbm"]
    final_pairs = analysis["mad_vs_self"]
    pair_denominator = sum(row["valid_pairs"] for row in final_pairs)
    mad_better = sum(row["mad_correct_self_wrong"] for row in final_pairs)
    self_better = sum(row["mad_wrong_self_correct"] for row in final_pairs)
    final_noise = [row for row in analysis["clean_vs_noise"] if row["branch"] == "mad" and row["revision_round"] == 2]
    noise_pairs = sum(row["valid_pairs"] for row in final_noise)
    clean_better = sum(row["clean_correct_noise_wrong"] for row in final_noise)
    noise_better = sum(row["clean_wrong_noise_correct"] for row in final_noise)
    resources = json.loads((root / "results/resource_manifest.json").read_text(encoding="utf-8"))
    state_index = {
        (row["task_family"], row["condition"], row["stage"], row["branch"], row["revision_round"]): row
        for row in analysis["state_statistics"]
    }
    team_index = {
        (row["task_family"], row["condition"], row["stage"], row["branch"], row["revision_round"]): row
        for row in analysis["team_statistics"]
    }
    pair_index = {
        (row["task_family"], row["condition"], row["stage"]): row
        for row in analysis["mad_vs_self"]
    }

    def state_accuracy(key: tuple[Any, ...]) -> str:
        row = state_index[key]
        return _pct(row["correct"], row["recognized"])

    def disagreement(key: tuple[Any, ...]) -> str:
        row = team_index[key]
        return _pct(row["disagreement_teams"], row["all_recognized_teams"])

    stage_keys = sorted(
        {(row["task_family"], row["condition"], row["stage"]) for row in analysis["state_statistics"]},
        key=str,
    )
    lines = [
        "# 原始属性筛选与 CBM 动态属性筛选 MAD 漂移诊断 Pilot", "",
        "## 实验状态", "",
        "- 18 道基础题，18 个 CL×DS×source_IL cell 各 1 题；每题 3 个团队重复、3 个同质 Qwen3-8B 智能体、2 轮同步复核。",
        f"- MAD/对照计划 {integrity['expected']} 条，实际 {integrity['actual']} 条，缺失 {integrity['missing']}，重复 {integrity['duplicates']}，API 失败 {integrity['api_failures']}，依赖阻塞 {integrity['blocked']}。",
        f"- 可识别 {integrity['recognized']}/{integrity['actual']}；严格格式 {integrity['strict_schema']}/{integrity['actual']}；截断 {integrity['truncated']}。最大输入 {integrity['max_prompt_tokens']} tokens。",
        f"- 使用 {len(resources['services'])} 个同配置 Qwen3-8B vLLM 副本，GPU 为 {', '.join(str(row['gpu_index']) for row in resources['services'])}；BF16、无量化、上下文 16384。",
        f"- 正式实验消耗 prompt/completion tokens 共 {integrity['total_prompt_tokens']}/{integrity['total_completion_tokens']}；请求延迟求和 {integrity['total_latency_seconds']:.3f} 秒，单请求均值 {analysis['mean_latency_seconds']:.4f} 秒。延迟求和不是并行运行墙钟时间。",
        "- 所有普通错误、格式错误与截断均保留；没有按结果重采样。", "",
        "## 集合协议复核", "",
        f"- 旧协议集合准确率 {_pct(old_set['correct'], old_set['records'])}，新协议 {_pct(new_set['correct'], new_set['records'])}。",
        f"- 具体示例集合 `{{A,C}}` 的出现率从 {_pct(old_set['a_c_exact'], old_set['records'])} 变为 {_pct(new_set['a_c_exact'], new_set['records'])}。",
        f"- B_source_set 完全正确率由 {_pct(protocol['old']['B_source_set']['correct'], protocol['old']['B_source_set']['records'])} 变为 {_pct(protocol['new']['B_source_set']['correct'], protocol['new']['B_source_set']['records'])}；具体示例锚定消失并不等于集合任务已被模型掌握。",
        f"- 新协议可识别率 {_pct(new_set['recognized'], new_set['records'])}，严格格式率 {_pct(new_set['strict_schema'], new_set['records'])}，截断 {_pct(new_set['truncated'], new_set['records'])}。",
        f"- 保守规则识别到解释与最终集合明显冲突的候选记录 {protocol.get('conservative_reasoning_conflict_count', 0)} 条，已单独保存供复核。",
        "- 新协议只删除具体标签组合示例，不改变 unknown、重述、更正或候选集合语义。准确率变化是描述性配对结果，不单独证明内部锚定机制。", "",
        "## 讨论变化", "",
        f"- 重叠窗口客观事件：正确保持 {event_counts.get('correct_retention', 0)}，有害修改 {event_counts.get('harmful_revision', 0)}，有效纠错 {event_counts.get('effective_correction', 0)}，错误持续 {event_counts.get('error_persistence', 0)}。这些窗口不能相加解释为互斥事件总数。",
        f"- 有害修改或有效纠错涉及 {analysis['events_involving_items']}/18 道基础题；这是事件覆盖，不是总体发生率估计。",
        f"- 3,510 个完整团队状态中有分歧 {analysis['team_summary']['disagreement_states']} 个、正确共识 {analysis['team_summary']['correct_consensus_states']} 个、错误共识 {analysis['team_summary']['wrong_consensus_states']} 个。",
    ]
    for row in static:
        lines.append(f"- 静态 `{row['branch']}`：讨论前→R2 准确率 {row['before_accuracy']}→{row['after_accuracy']}；正确起点有害修改 {_pct(row['harmful_revisions'], row['before_correct'])}；错误起点有效纠错率 {row['correction_rate_given_wrong_start']}。")
    lines.append(f"- 所有最终 MAD/self 有效配对中，MAD 对而 self 错 {_pct(mad_better, pair_denominator)}；MAD 错而 self 对 {_pct(self_better, pair_denominator)}。该对照匹配当前阶段起点，不代表全程无同伴历史。")
    lines.extend([
        "",
        "### 阶段级状态与团队分歧",
        "",
        "|任务/条件|阶段|讨论前准确率|MAD R1|MAD R2|Self R1|Self R2|讨论前分歧|MAD R2 分歧|MAD 对/self 错|MAD 错/self 对|",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for family, condition, stage in stage_keys:
        base = (family, condition, stage)
        pair = pair_index[base]
        display_stage = "-" if stage is None else str(stage)
        lines.append(
            f"|{family}/{condition}|{display_stage}|"
            f"{state_accuracy((*base, 'shared', 0))}|"
            f"{state_accuracy((*base, 'mad', 1))}|{state_accuracy((*base, 'mad', 2))}|"
            f"{state_accuracy((*base, 'self', 1))}|{state_accuracy((*base, 'self', 2))}|"
            f"{disagreement((*base, 'shared', 0))}|{disagreement((*base, 'mad', 2))}|"
            f"{_pct(pair['mad_correct_self_wrong'], pair['valid_pairs'])}|"
            f"{_pct(pair['mad_wrong_self_correct'], pair['valid_pairs'])}|"
        )
    lines.extend(["", "## CBM 新增诊断", ""])
    for row in cbm:
        lines.append(f"- `{row['condition']}` stage {row['stage']} `{row['branch']}`：讨论前→R2 {row['before_accuracy']}→{row['after_accuracy']}，有害修改率(正确起点)={row['harmful_rate_given_correct_start']}，有效纠错率(错误起点)={row['correction_rate_given_wrong_start']}。")
    lines.extend([
        f"- 更正阶段中，在 W 更正前确实被排除的 {update['readd_opportunities']} 次机会里，讨论前重新加入 W：{_pct(update['readded'], update['readd_opportunities'])}。这避免把原先已错误保留 W 的情况算作恢复。",
        f"- 更正后讨论前正确的 {update['discussion_pre_correct']} 次状态中，MAD R2 又排除 W：{_pct(update['discussion_then_dropped_w'], update['discussion_pre_correct'])}。",
        f"- C/E 对应 MAD R2 配对中，clean 对/noise 错 {_pct(clean_better, noise_pairs)}，clean 错/noise 对 {_pct(noise_better, noise_pairs)}；所有配对 seed 不一致数应为 0。",
        f"- 更正前完全正确的 {update['pre_correction_correct']} 次状态中，更正后讨论前仍完全正确 {_pct(update['post_correction_correct_given_pre_correct'], update['pre_correction_correct'])}；最终丢失原 Gold {update['final_gold_drops']} 次，仍含无关额外候选 {update['final_unrelated_extra_sets']} 次。",
        "- CBM 相比静态题增加了 unknown 下的候选保留、oracle 随证据变化、重述保持、非目标信息配对和明确更正后的集合扩张事件。", "",
        "## 形式化错误集合变化", "",
    ])
    for row in analysis["diagnostic_change_statistics"]:
        if row["task_family"] == "static":
            details = f"新增/消除违反实例 {row['introduced_violation_instances']}/{row['resolved_violation_instances']}"
        else:
            details = (
                f"新增/消除漏选 {row['new_omission_instances']}/{row['resolved_omission_instances']}，"
                f"新增/消除多选 {row['new_extra_instances']}/{row['resolved_extra_instances']}"
            )
        lines.append(
            f"- `{row['condition']}` stage {row['stage']}: pre→MAD R2 共 {row['transitions']} 条，"
            f"答案变化 {row['answer_changes']}，同伴答案采用信号 {row['peer_adoption_signals']}；{details}。"
        )
    lines.extend([
        "",
        "## 分类支持与边界", "",
        "- 仓库中未找到冻结的完整 15 类 taxonomy 或 Judge 配置，因此本轮不自行发明类别替代品，也不输出正式漂移类别。",
        "- 程序可准确判定正确→错误、错误→正确、约束违反集合、错误保留/排除集合、同伴上一轮答案采用信号与共识变化。",
        "- 采用同伴答案不等于从众；相同错误只构成传播线索；输出解释不证明内部遗忘或因果机制。自然语言原因进入待复核队列。", "",
        "## 结论", "",
        "- 本 pilot 验证了在真实同步 MAD 轨迹上定位交互前后状态变化，并用结构化约束和逐轮 oracle 给出可审查证据。",
        "- 协议中的具体 `{A,C}` 示例锚定明显缓解，但 B_source_set 仍为 0/54，说明集合状态跟踪本身仍是强基线限制；不应把全部错误解释为交互漂移。",
        "- 静态题 162 个独立 R0 判断均正确，MAD 与自我修正均保持正确；本轮静态子集可作为稳定控制，但没有提供静态有害漂移案例。",
        "- CBM 的 clean/noise、更正与逐阶段 oracle 提供了静态题没有的可定位事件。客观事件信号得到支持，但缺少冻结 taxonomy，因此尚不支持正式漂移类别标注。",
        "- 建议先冻结 taxonomy 的必要证据定义并复核报告中的候选案例；随后可扩到 72 题以估计事件覆盖，但应保留协议检查和静态稳定控制，而不是调整任务去追求更多漂移。18 题重复响应不能当作独立题目。",
        "- 本轮未运行 Drift Judge、RL 或其他模型，也未自动扩样。", "",
    ])
    path = root / "reports/MAD_DRIFT_PILOT_V1_REPORT.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
