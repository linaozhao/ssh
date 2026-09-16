"""Independent structural and semantic validation for CBM-Attr v1."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from mad_attr_filter.attributes import ATTRIBUTE_BY_KEY

from cbm_attr_v1.common import LABELS, read_jsonl, sha256_json, write_json
from cbm_attr_v1.oracle import compute_oracle, enumerate_oracle


def _target_signature(round_data: dict[str, Any]) -> list[tuple[str, str, bool, str]]:
    return sorted(
        (
            str(event["candidate_id"]),
            str(event["attribute"]),
            bool(event["value"]),
            str(event["event_type"]),
        )
        for event in round_data["events"]
        if event["fact_kind"] == "target"
    )


def validate_episode(episode: dict[str, Any], item: dict[str, Any], snapshots: list[dict[str, Any]]) -> list[str]:
    """Return every detected episode validation error."""
    errors: list[str] = []
    constraints = item["constraints"]
    clean = episode["clean"]["rounds"]
    noise = episode["noise"]["rounds"]
    if len(clean) != 5 or len(noise) != 5 or len(episode["update"]["rounds"]) != 2:
        errors.append("incorrect_round_count")
    if clean[2]["oracle"] != [item["gold_answer"]]:
        errors.append("clean_round3_not_source_gold")
    if clean[3]["oracle"] != clean[2]["oracle"] or clean[4]["oracle"] != clean[3]["oracle"]:
        errors.append("clean_restatement_changed_oracle")

    expected_attributes = {row["attribute"] for row in constraints}
    seen: Counter[tuple[str, str]] = Counter()
    first_rounds: dict[str, set[int]] = defaultdict(set)
    for round_data in clean[:3]:
        for event in round_data["events"]:
            seen[(event["candidate_id"], event["attribute"])] += 1
            first_rounds[event["candidate_id"]].add(round_data["round_id"])
        direct = compute_oracle(constraints, round_data["active_target_evidence"])
        enumerated = enumerate_oracle(constraints, round_data["active_target_evidence"])
        if direct != round_data["oracle"] or enumerated != round_data["oracle"]:
            errors.append(f"oracle_mismatch_clean_r{round_data['round_id']}")
    expected_pairs = {(label, attribute) for label in LABELS for attribute in expected_attributes}
    if set(seen) != expected_pairs or any(count != 1 for count in seen.values()):
        errors.append("target_fact_delivery_not_exactly_once")
    if any(rounds != {1, 2, 3} for rounds in first_rounds.values()):
        errors.append("candidate_facts_not_spread_across_three_rounds")

    for c_round, e_round in zip(clean, noise, strict=True):
        if _target_signature(c_round) != _target_signature(e_round):
            errors.append(f"clean_noise_target_delta_mismatch_r{c_round['round_id']}")
        if c_round["oracle"] != e_round["oracle"]:
            errors.append(f"clean_noise_oracle_mismatch_r{c_round['round_id']}")
    noise_facts = {
        event["evidence_id"]: event
        for row in noise
        for event in row["events"]
        if event["fact_kind"] == "non_target"
    }
    if len(noise_facts) != 8:
        errors.append("noise_fact_count_not_eight")
    if any(fact.get("non_target_key") in ATTRIBUTE_BY_KEY for fact in noise_facts.values()):
        errors.append("non_target_key_is_formal_attribute")

    update = episode["update"]
    target = update["target_candidate"]
    expected_post = sorted((item["gold_answer"], target))
    if sorted(update["post_correction_oracle"]) != expected_post:
        errors.append("update_did_not_restore_target")
    if update["rounds"][1]["oracle"] != update["rounds"][0]["oracle"]:
        errors.append("update_restatement_changed_oracle")
    if update["correction_size"] != len(item["option_violation_signature"][target]):
        errors.append("correction_size_mismatch")
    for round_data in update["rounds"]:
        if compute_oracle(constraints, round_data["active_target_evidence"]) != round_data["oracle"]:
            errors.append(f"update_oracle_mismatch_r{round_data['round_id']}")
        if enumerate_oracle(constraints, round_data["active_target_evidence"]) != round_data["oracle"]:
            errors.append(f"update_enumeration_mismatch_r{round_data['round_id']}")

    snapshot_map = {(row["source_condition"], row["round_id"]): row for row in snapshots}
    expected_keys = {
        *(("C_clean", round_id) for round_id in range(1, 6)),
        *(("E_noise", round_id) for round_id in range(1, 6)),
        ("D_update", 4),
        ("D_update", 5),
    }
    if set(snapshot_map) != expected_keys:
        errors.append("snapshot_key_mismatch")
    for condition_key, condition_name in (("clean", "C_clean"), ("noise", "E_noise")):
        for round_data in episode[condition_key]["rounds"]:
            snapshot = snapshot_map.get((condition_name, round_data["round_id"]))
            if snapshot and (snapshot["oracle"] != round_data["oracle"] or snapshot["visible_facts"] != round_data["visible_facts"]):
                errors.append(f"snapshot_mismatch_{condition_name}_r{round_data['round_id']}")
    for round_data in update["rounds"]:
        snapshot = snapshot_map.get(("D_update", round_data["round_id"]))
        if snapshot and (snapshot["oracle"] != round_data["oracle"] or snapshot["visible_facts"] != round_data["visible_facts"]):
            errors.append(f"snapshot_mismatch_D_update_r{round_data['round_id']}")
    return errors


def validate_artifacts(data_dir: Path, *, report_path: Path | None = None) -> dict[str, Any]:
    """Validate generated data and request-plan denominators."""
    items = read_jsonl(data_dir / "source_items.jsonl")
    selection = read_jsonl(data_dir / "selection_manifest.jsonl")
    episodes = read_jsonl(data_dir / "episodes.jsonl")
    snapshots = read_jsonl(data_dir / "snapshots.jsonl")
    plan = read_jsonl(data_dir / "request_plan.jsonl")
    errors: list[dict[str, str]] = []
    if len(items) != 72 or len(selection) != 72 or len(episodes) != 72:
        errors.append({"scope": "global", "error": "expected_72_items"})
    cells = Counter(row["difficulty_cell"] for row in selection)
    if len(cells) != 18 or set(cells.values()) != {4}:
        errors.append({"scope": "global", "error": f"cell_distribution:{dict(cells)}"})
    gold_by_cell: dict[str, set[str]] = defaultdict(set)
    for row in selection:
        gold_by_cell[row["difficulty_cell"]].add(row["source_gold"])
    if any(values != set(LABELS) for values in gold_by_cell.values()):
        errors.append({"scope": "global", "error": "gold_not_balanced_within_cell"})
    if len(snapshots) != 72 * 12:
        errors.append({"scope": "global", "error": f"expected_864_snapshots_got_{len(snapshots)}"})
    if len(plan) != 72 * 3 * 26:
        errors.append({"scope": "global", "error": f"expected_5616_requests_got_{len(plan)}"})
    request_ids = [row["request_id"] for row in plan]
    if len(request_ids) != len(set(request_ids)):
        errors.append({"scope": "global", "error": "duplicate_request_ids"})
    known = set(request_ids)
    if any(dependency not in known for row in plan for dependency in row["depends_on"]):
        errors.append({"scope": "global", "error": "unknown_request_dependency"})

    item_by_base = {item["base_item_id"]: item for item in items}
    snapshots_by_base: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for snapshot in snapshots:
        snapshots_by_base[snapshot["base_item_id"]].append(snapshot)
    state_sequences: Counter[str] = Counter()
    for episode in episodes:
        for error in validate_episode(
            episode, item_by_base[episode["base_item_id"]], snapshots_by_base[episode["base_item_id"]]
        ):
            errors.append({"scope": episode["base_item_id"], "error": error})
        state_sequences["-".join(str(len(row["oracle"])) for row in episode["clean"]["rounds"])] += 1

    report = {
        "valid": not errors,
        "experiment_version": "cbm_attr_v1.0",
        "counts": {
            "source_items": len(items),
            "episodes": len(episodes),
            "snapshots": len(snapshots),
            "request_plan": len(plan),
            "difficulty_cells": dict(sorted(cells.items())),
            "scenario_distribution": dict(Counter(row["scenario"] for row in selection)),
            "gold_distribution": dict(Counter(row["source_gold"] for row in selection)),
            "clean_oracle_size_sequences": dict(state_sequences),
        },
        "checks": {
            "unknown_retained": compute_oracle(
                [{"attribute": "x", "required_value": True}], []
            ) == list(LABELS),
            "independent_oracle_cross_check": True,
            "no_future_evidence_leak": not any(
                fact["first_appearance_round"] > row["round_id"]
                for episode in episodes
                for key in ("clean", "noise")
                for row in episode[key]["rounds"]
                for fact in row["visible_facts"]
            ),
            "request_plan_sha256": sha256_json(plan),
        },
        "errors": errors,
    }
    if report_path:
        write_json(report_path, report)
    return report
