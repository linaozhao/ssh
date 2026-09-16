"""Deterministic construction of CBM-inspired attribute-filtering episodes."""

from __future__ import annotations

import copy
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from mad_attr_filter.attributes import ATTRIBUTE_BY_KEY
from mad_attr_filter.non_target_facts import sample_non_target_facts

from cbm_attr_v1.common import (
    EXPERIMENT_VERSION,
    LABELS,
    difficulty_cell,
    sha256_json,
    stable_seed,
    write_jsonl,
)
from cbm_attr_v1.oracle import compute_oracle


def select_source_items(
    source: list[dict[str, Any]], *, seed: int, per_cell: int = 4
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Select one item per Gold label in each cell while balancing scenarios."""
    if per_cell != 4:
        raise ValueError("CBM-Attr v1 requires four source items per cell")
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in source:
        grouped[difficulty_cell(item)].append(item)
    if len(grouped) != 18:
        raise ValueError(f"Expected 18 difficulty cells, found {len(grouped)}")

    rng = random.Random(seed)
    scenario_counts: Counter[str] = Counter()
    selected: list[dict[str, Any]] = []
    manifest: list[dict[str, Any]] = []
    for cell in sorted(grouped):
        rows = grouped[cell]
        for gold in LABELS:
            candidates = [item for item in rows if item["gold_answer"] == gold]
            if not candidates:
                raise ValueError(f"Cell {cell} has no item with Gold {gold}")
            rng.shuffle(candidates)
            minimum = min(scenario_counts[item["scenario"]] for item in candidates)
            balanced = [item for item in candidates if scenario_counts[item["scenario"]] == minimum]
            chosen = balanced[0]
            selected.append(copy.deepcopy(chosen))
            scenario_counts[chosen["scenario"]] += 1
            manifest.append(
                {
                    "source_item_id": chosen["item_id"],
                    "base_item_id": chosen["base_item_id"],
                    "difficulty_cell": cell,
                    "constraint_load": chosen["difficulty_factors"]["constraint_load"],
                    "distractor_similarity": chosen["difficulty_factors"]["distractor_similarity"],
                    "source_information_load": chosen["difficulty_factors"]["information_load"],
                    "scenario": chosen["scenario"],
                    "source_gold": chosen["gold_answer"],
                    "selection_seed": seed,
                    "selection_method": "one_per_gold_per_cell_then_greedy_scenario_balance",
                    "question_sha256": sha256_json(chosen["question"]),
                    "structured_sha256": sha256_json(
                        {
                            "constraints": chosen["constraints"],
                            "entities": chosen["entities"],
                            "matrix": chosen["option_constraint_matrix"],
                            "violations": chosen["option_violation_signature"],
                        }
                    ),
                }
            )
    return selected, manifest


def _target_facts(item: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    facts: dict[str, list[dict[str, Any]]] = {}
    for label in LABELS:
        rows = []
        for displayed in item["entities"][label]["displayed_facts"]:
            attribute = str(displayed["attribute"])
            rows.append(
                {
                    "evidence_id": f"{item['base_item_id']}:{label}:{attribute}:v1",
                    "candidate_id": label,
                    "candidate_name": item["entities"][label]["name"],
                    "attribute": attribute,
                    "value": bool(displayed["value"]),
                    "text": str(displayed["text"]),
                    "first_appearance_round": None,
                    "fact_kind": "target",
                    "event_type": "observation",
                    "version": 1,
                    "replaces_evidence_id": None,
                    "corrected_by": None,
                }
            )
        facts[label] = rows
    return facts


def _schedule_target_facts(item: dict[str, Any], seed: int) -> list[list[dict[str, Any]]]:
    rounds: list[list[dict[str, Any]]] = [[], [], []]
    facts = _target_facts(item)
    for label_index, label in enumerate(LABELS):
        candidate_facts = facts[label]
        rng = random.Random(stable_seed(seed, item["item_id"], label, "target-schedule"))
        rng.shuffle(candidate_facts)
        offset = label_index % 3
        for index, fact in enumerate(candidate_facts):
            round_index = (index + offset) % 3
            fact["first_appearance_round"] = round_index + 1
            rounds[round_index].append(fact)
    for round_index, events in enumerate(rounds, start=1):
        random.Random(stable_seed(seed, item["item_id"], round_index, "event-order")).shuffle(events)
    return rounds


def _noise_facts(item: dict[str, Any], seed: int) -> list[list[dict[str, Any]]]:
    rounds: list[list[dict[str, Any]]] = [[], [], []]
    for label_index, label in enumerate(LABELS):
        entity = item["entities"][label]
        source = copy.deepcopy(entity.get("non_target_facts", []))
        if len(source) < 2:
            rng = random.Random(stable_seed(seed, item["item_id"], label, "generated-noise"))
            source = sample_non_target_facts(entity["name"], item["scenario"], rng, count=2)
        for fact_index, source_fact in enumerate(source[:2]):
            first_round = 1 + ((label_index + fact_index) % 3)
            rounds[first_round - 1].append(
                {
                    "evidence_id": f"{item['base_item_id']}:{label}:noise:{source_fact['key']}",
                    "candidate_id": label,
                    "candidate_name": entity["name"],
                    "attribute": None,
                    "non_target_key": source_fact["key"],
                    "value": None,
                    "text": source_fact["text"],
                    "first_appearance_round": first_round,
                    "fact_kind": "non_target",
                    "event_type": "observation",
                    "version": 1,
                    "replaces_evidence_id": None,
                    "corrected_by": None,
                }
            )
    for round_index, events in enumerate(rounds, start=1):
        random.Random(stable_seed(seed, item["item_id"], round_index, "noise-order")).shuffle(events)
    return rounds


def _resolved_visible_facts(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    target: dict[tuple[str, str], dict[str, Any]] = {}
    noise: dict[str, dict[str, Any]] = {}
    for event in events:
        if event["event_type"] == "restatement":
            continue
        if event["fact_kind"] == "target":
            target[(event["candidate_id"], event["attribute"])] = event
        else:
            noise[event["evidence_id"]] = event
    return sorted(
        [copy.deepcopy(row) for row in (*target.values(), *noise.values())],
        key=lambda row: (row["candidate_id"], row["fact_kind"], row.get("attribute") or row["evidence_id"]),
    )


def _round_record(
    round_id: int,
    events: list[dict[str, Any]],
    cumulative: list[dict[str, Any]],
    constraints: list[dict[str, Any]],
) -> dict[str, Any]:
    cumulative.extend(copy.deepcopy(events))
    visible = _resolved_visible_facts(cumulative)
    target_visible = [fact for fact in visible if fact["fact_kind"] == "target"]
    oracle = compute_oracle(constraints, target_visible)
    return {
        "round_id": round_id,
        "events": copy.deepcopy(events),
        "active_target_evidence": target_visible,
        "visible_facts": visible,
        "oracle": oracle,
    }


def _restatement(event: dict[str, Any], *, round_id: int, suffix: str) -> dict[str, Any]:
    row = copy.deepcopy(event)
    row.update(
        {
            "evidence_id": f"{event['evidence_id']}:restated:{suffix}",
            "first_appearance_round": round_id,
            "event_type": "restatement",
            "restates_evidence_id": event["evidence_id"],
            "replaces_evidence_id": None,
        }
    )
    return row


def _build_clean_rounds(item: dict[str, Any], seed: int) -> list[dict[str, Any]]:
    scheduled = _schedule_target_facts(item, seed)
    cumulative: list[dict[str, Any]] = []
    rounds = [
        _round_record(index, events, cumulative, item["constraints"])
        for index, events in enumerate(scheduled, start=1)
    ]
    all_targets = [fact for events in scheduled for fact in events]
    satisfying = [
        fact
        for fact in all_targets
        if any(
            constraint["attribute"] == fact["attribute"]
            and constraint["required_value"] == fact["value"]
            for constraint in item["constraints"]
        )
    ]
    rng = random.Random(stable_seed(seed, item["item_id"], "restate"))
    rng.shuffle(satisfying)
    for round_id, fact in zip((4, 5), satisfying[:2], strict=True):
        rounds.append(
            _round_record(
                round_id,
                [_restatement(fact, round_id=round_id, suffix=str(round_id))],
                cumulative,
                item["constraints"],
            )
        )
    return rounds


def _build_noise_rounds(
    item: dict[str, Any], clean_rounds: list[dict[str, Any]], seed: int
) -> list[dict[str, Any]]:
    noise_schedule = _noise_facts(item, seed)
    cumulative: list[dict[str, Any]] = []
    rounds: list[dict[str, Any]] = []
    for index, clean_round in enumerate(clean_rounds, start=1):
        events = copy.deepcopy(clean_round["events"])
        if index <= 3:
            events.extend(copy.deepcopy(noise_schedule[index - 1]))
        rounds.append(_round_record(index, events, cumulative, item["constraints"]))
    return rounds


def _correction_text(item: dict[str, Any], candidate: str, attribute: str, value: bool, seed: int) -> str:
    spec = ATTRIBUTE_BY_KEY[attribute]
    templates = spec.candidate_true_templates if value else spec.candidate_false_templates
    rng = random.Random(stable_seed(seed, item["item_id"], candidate, attribute, "correction-text"))
    return rng.choice(templates).format(name=item["entities"][candidate]["name"])


def _build_update_rounds(
    item: dict[str, Any], clean_rounds: list[dict[str, Any]], seed: int
) -> dict[str, Any]:
    wrong = [label for label in LABELS if label != item["gold_answer"]]
    target = random.Random(stable_seed(seed, item["item_id"], "update-target")).choice(wrong)
    constraint_by_id = {row["id"]: row for row in item["constraints"]}
    violations = item["option_violation_signature"][target]
    corrections: list[dict[str, Any]] = []
    for constraint_id in violations:
        constraint = constraint_by_id[constraint_id]
        attribute = constraint["attribute"]
        old_id = f"{item['base_item_id']}:{target}:{attribute}:v1"
        corrections.append(
            {
                "evidence_id": f"{item['base_item_id']}:{target}:{attribute}:v2",
                "candidate_id": target,
                "candidate_name": item["entities"][target]["name"],
                "attribute": attribute,
                "value": bool(constraint["required_value"]),
                "text": _correction_text(item, target, attribute, bool(constraint["required_value"]), seed),
                "first_appearance_round": 4,
                "fact_kind": "target",
                "event_type": "correction",
                "version": 2,
                "replaces_evidence_id": old_id,
                "corrected_by": None,
            }
        )
    cumulative = [copy.deepcopy(event) for row in clean_rounds[:3] for event in row["events"]]
    round4 = _round_record(4, corrections, cumulative, item["constraints"])
    repeat_source = corrections[0]
    round5 = _round_record(
        5,
        [_restatement(repeat_source, round_id=5, suffix="update5")],
        cumulative,
        item["constraints"],
    )
    return {
        "target_candidate": target,
        "target_candidate_name": item["entities"][target]["name"],
        "violated_constraint_ids": list(violations),
        "correction_size": len(corrections),
        "pre_correction_oracle": clean_rounds[2]["oracle"],
        "post_correction_oracle": round4["oracle"],
        "shared_prefix_rounds": [1, 2, 3],
        "shared_prefix_sha256": sha256_json(clean_rounds[:3]),
        "rounds": [round4, round5],
    }


def build_episode(item: dict[str, Any], *, schedule_seed: int) -> dict[str, Any]:
    """Build clean, noise, and correction trajectories for one source item."""
    clean = _build_clean_rounds(item, schedule_seed)
    noise = _build_noise_rounds(item, clean, schedule_seed)
    update = _build_update_rounds(item, clean, schedule_seed)
    final_first = next(
        row["round_id"] for row in clean if row["oracle"] == [item["gold_answer"]]
    )
    return {
        "episode_id": f"cbm:{item['base_item_id']}",
        "experiment_version": EXPERIMENT_VERSION,
        "source_item_id": item["item_id"],
        "base_item_id": item["base_item_id"],
        "difficulty_cell": difficulty_cell(item),
        "difficulty_factors": copy.deepcopy(item["difficulty_factors"]),
        "source_information_load": item["difficulty_factors"]["information_load"],
        "scenario": item["scenario"],
        "source_gold": item["gold_answer"],
        "schedule_seed": schedule_seed,
        "candidate_names": {label: item["entities"][label]["name"] for label in LABELS},
        "constraints": copy.deepcopy(item["constraints"]),
        "clean": {
            "condition": "C_clean",
            "actual_noise_condition": "no_non_target_information",
            "rounds": clean,
            "first_final_oracle_round": final_first,
        },
        "noise": {
            "condition": "E_noise",
            "actual_noise_condition": "two_non_target_facts_per_candidate",
            "rounds": noise,
        },
        "update": {
            "condition": "D_update",
            "parent_trajectory_condition": "C_clean",
            **update,
        },
    }


def build_snapshots(episode: dict[str, Any]) -> list[dict[str, Any]]:
    """Build 12 independent static snapshots for one episode."""
    rows: list[dict[str, Any]] = []
    for condition_key, condition_name in (("clean", "C_clean"), ("noise", "E_noise")):
        for round_data in episode[condition_key]["rounds"]:
            rows.append(
                {
                    "snapshot_id": f"{episode['base_item_id']}:{condition_name}:r{round_data['round_id']}",
                    "base_item_id": episode["base_item_id"],
                    "source_item_id": episode["source_item_id"],
                    "source_condition": condition_name,
                    "round_id": round_data["round_id"],
                    "visible_facts": copy.deepcopy(round_data["visible_facts"]),
                    "oracle": list(round_data["oracle"]),
                }
            )
    for round_data in episode["update"]["rounds"]:
        rows.append(
            {
                "snapshot_id": f"{episode['base_item_id']}:D_update:r{round_data['round_id']}",
                "base_item_id": episode["base_item_id"],
                "source_item_id": episode["source_item_id"],
                "source_condition": "D_update",
                "round_id": round_data["round_id"],
                "visible_facts": copy.deepcopy(round_data["visible_facts"]),
                "oracle": list(round_data["oracle"]),
            }
        )
    return rows


def build_request_plan(
    items: list[dict[str, Any]], episodes: list[dict[str, Any]], snapshots: list[dict[str, Any]], seeds: list[int]
) -> list[dict[str, Any]]:
    """Enumerate all 26 logical requests per item and repetition."""
    item_by_base = {item["base_item_id"]: item for item in items}
    snapshots_by_base: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for snapshot in snapshots:
        snapshots_by_base[snapshot["base_item_id"]].append(snapshot)
    rows: list[dict[str, Any]] = []
    for episode in episodes:
        base = episode["base_item_id"]
        item = item_by_base[base]
        for run_id, seed in enumerate(seeds, start=1):
            unit = f"{base}:run{run_id}"
            shared = {
                "source_item_id": item["item_id"],
                "base_item_id": base,
                "difficulty_cell": episode["difficulty_cell"],
                "difficulty_factors": episode["difficulty_factors"],
                "scenario": item["scenario"],
                "source_gold": item["gold_answer"],
                "run_id": run_id,
                "seed": seed,
                "unit_id": unit,
            }
            rows.append({**shared, "request_id": f"{unit}:A_original", "condition": "A_original", "round_id": 1, "protocol": "single_choice", "oracle": [item["gold_answer"]], "depends_on": []})
            rows.append({**shared, "request_id": f"{unit}:B_source_set", "condition": "B_source_set", "round_id": 1, "protocol": "candidate_set", "oracle": [item["gold_answer"]], "depends_on": []})
            for condition_key, condition_name in (("clean", "C_clean"), ("noise", "E_noise")):
                previous: str | None = None
                for round_data in episode[condition_key]["rounds"]:
                    request_id = f"{unit}:{condition_name}:r{round_data['round_id']}"
                    rows.append({**shared, "request_id": request_id, "condition": condition_name, "round_id": round_data["round_id"], "protocol": "candidate_set", "oracle": round_data["oracle"], "depends_on": [previous] if previous else []})
                    previous = request_id
            c3 = f"{unit}:C_clean:r3"
            d4 = f"{unit}:D_update:r4"
            rows.append({**shared, "request_id": d4, "condition": "D_update", "round_id": 4, "protocol": "candidate_set", "oracle": episode["update"]["rounds"][0]["oracle"], "depends_on": [c3], "parent_trajectory_id": f"{unit}:C_clean", "shared_prefix_sha256": episode["update"]["shared_prefix_sha256"]})
            rows.append({**shared, "request_id": f"{unit}:D_update:r5", "condition": "D_update", "round_id": 5, "protocol": "candidate_set", "oracle": episode["update"]["rounds"][1]["oracle"], "depends_on": [d4], "parent_trajectory_id": f"{unit}:C_clean", "shared_prefix_sha256": episode["update"]["shared_prefix_sha256"]})
            for snapshot in sorted(snapshots_by_base[base], key=lambda row: (row["source_condition"], row["round_id"])):
                rows.append({**shared, "request_id": f"{unit}:P_snapshot:{snapshot['source_condition']}:r{snapshot['round_id']}", "condition": "P_snapshot", "snapshot_condition": snapshot["source_condition"], "snapshot_id": snapshot["snapshot_id"], "round_id": snapshot["round_id"], "protocol": "candidate_set", "oracle": snapshot["oracle"], "depends_on": []})
    return rows


def prepare_all(
    source_path: Path,
    output_dir: Path,
    *,
    selection_seed: int,
    schedule_seed: int,
    run_seeds: list[int],
) -> dict[str, int]:
    """Generate every deterministic data artifact needed before inference."""
    import json

    source = [json.loads(line) for line in source_path.open(encoding="utf-8") if line.strip()]
    items, manifest = select_source_items(source, seed=selection_seed)
    episodes = [build_episode(item, schedule_seed=schedule_seed) for item in items]
    snapshots = [snapshot for episode in episodes for snapshot in build_snapshots(episode)]
    plan = build_request_plan(items, episodes, snapshots, run_seeds)
    write_jsonl(output_dir / "selection_manifest.jsonl", manifest)
    write_jsonl(output_dir / "source_items.jsonl", items)
    write_jsonl(output_dir / "episodes.jsonl", episodes)
    write_jsonl(output_dir / "snapshots.jsonl", snapshots)
    write_jsonl(output_dir / "request_plan.jsonl", plan)
    return {
        "source_items": len(items),
        "episodes": len(episodes),
        "snapshots": len(snapshots),
        "logical_requests": len(plan),
    }
