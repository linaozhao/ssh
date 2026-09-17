"""Deterministic selection and request-plan construction for the pilot."""

from __future__ import annotations

import copy
import difflib
import random
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from mad_drift_pilot.common import AGENTS, LABELS, difficulty_cell, file_sha256, read_jsonl, sha256_json, stable_seed, write_json, write_jsonl
from mad_drift_pilot.prompts import SET_SYSTEM_PROMPT_V2


TEAM_ROOT_SEEDS = (11, 22, 33)
SELECTION_SEED = 20260917


def _balanced_selection(items: list[dict[str, Any]], seed: int) -> list[dict[str, Any]]:
    """Choose one item per cell using a deterministic global balance objective."""
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        grouped[difficulty_cell(item)].append(item)
    if len(grouped) != 18:
        raise ValueError(f"Expected 18 cells, found {len(grouped)}")
    scenarios = ("availability_selection", "expert_recruitment", "project_assignment")
    cells = sorted(grouped)
    choices: list[list[dict[str, Any]]] = []
    for cell in cells:
        rows = sorted(grouped[cell], key=lambda row: row["base_item_id"])
        random.Random(stable_seed(seed, cell)).shuffle(rows)
        choices.append(rows)

    # State is scenario counts + Gold counts. Retain one deterministic path per state.
    states: dict[tuple[int, ...], tuple[int, ...]] = {(0,) * 7: ()}
    for rows in choices:
        next_states: dict[tuple[int, ...], tuple[int, ...]] = {}
        for state, path in states.items():
            for index, item in enumerate(rows):
                values = list(state)
                values[scenarios.index(item["scenario"])] += 1
                values[3 + LABELS.index(item["gold_answer"])] += 1
                key = tuple(values)
                candidate = (*path, index)
                if key not in next_states or candidate < next_states[key]:
                    next_states[key] = candidate
        states = next_states

    def objective(entry: tuple[tuple[int, ...], tuple[int, ...]]) -> tuple[Any, ...]:
        state, path = entry
        scenario_counts, gold_counts = state[:3], state[3:]
        return (
            max(scenario_counts) - min(scenario_counts),
            max(gold_counts) - min(gold_counts),
            sum((value - 6) ** 2 for value in scenario_counts),
            sum((value - target) ** 2 for value, target in zip(gold_counts, (5, 5, 4, 4), strict=True)),
            sha256_json([seed, path]),
        )

    _, path = min(states.items(), key=objective)
    return [copy.deepcopy(choices[index][choice]) for index, choice in enumerate(path)]


def _base_metadata(item: dict[str, Any], run_id: int) -> dict[str, Any]:
    return {
        "base_item_id": item["base_item_id"],
        "source_item_id": item["item_id"],
        "difficulty_cell": difficulty_cell(item),
        "difficulty_factors": item["difficulty_factors"],
        "scenario": item["scenario"],
        "source_gold": item["gold_answer"],
        "team_run_id": run_id,
        "root_seed": TEAM_ROOT_SEEDS[run_id - 1],
    }


def build_mad_plan(items: list[dict[str, Any]], episodes: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Build the 10,530-request static and CBM dependency plan."""
    rows: list[dict[str, Any]] = []
    for item in sorted(items, key=lambda row: row["base_item_id"]):
        base = item["base_item_id"]
        episode = episodes[base]
        for run_id, root_seed in enumerate(TEAM_ROOT_SEEDS, start=1):
            meta = _base_metadata(item, run_id)
            for agent in AGENTS:
                request_id = f"static:{base}:team{run_id}:shared:{agent}:r0"
                rows.append({**meta, "request_id": request_id, "task_family": "static", "condition": "A_original", "stage": None, "branch": "shared", "agent_id": agent, "revision_round": 0, "protocol": "single_choice", "oracle": [item["gold_answer"]], "depends_on": [], "seed": stable_seed(root_seed, base, agent, "static", 0)})
            for branch in ("mad", "self"):
                for revision in (1, 2):
                    for agent in AGENTS:
                        parent_branch = "shared" if revision == 1 else branch
                        parent_revision = revision - 1
                        dependency = f"static:{base}:team{run_id}:{parent_branch}:{agent}:r{parent_revision}"
                        rows.append({**meta, "request_id": f"static:{base}:team{run_id}:{branch}:{agent}:r{revision}", "task_family": "static", "condition": "A_original", "stage": None, "branch": branch, "agent_id": agent, "revision_round": revision, "protocol": "single_choice", "oracle": [item["gold_answer"]], "depends_on": [dependency], "seed": stable_seed(root_seed, base, agent, "static", revision)})

            for condition, stages in (("C_clean", range(1, 6)), ("E_noise", range(1, 6)), ("D_update", range(4, 6))):
                episode_key = {"C_clean": "clean", "E_noise": "noise", "D_update": "update"}[condition]
                paired_condition_seed_key = "C_E_paired" if condition in {"C_clean", "E_noise"} else condition
                rounds = {row["round_id"]: row for row in episode[episode_key]["rounds"]}
                for stage in stages:
                    oracle = rounds[stage]["oracle"]
                    for agent in AGENTS:
                        dependencies: list[str] = []
                        if condition == "D_update" and stage == 4:
                            dependencies = [f"cbm:{base}:team{run_id}:C_clean:s3:mad:{agent}:r2"]
                        elif stage > (4 if condition == "D_update" else 1):
                            dependencies = [f"cbm:{base}:team{run_id}:{condition}:s{stage - 1}:mad:{agent}:r2"]
                        rows.append({**meta, "request_id": f"cbm:{base}:team{run_id}:{condition}:s{stage}:shared:{agent}:r0", "task_family": "cbm", "condition": condition, "stage": stage, "branch": "shared", "agent_id": agent, "revision_round": 0, "protocol": "candidate_set", "oracle": oracle, "depends_on": dependencies, "seed": stable_seed(root_seed, base, agent, paired_condition_seed_key, stage, 0), "seed_pairing": "C_clean_E_noise" if condition in {"C_clean", "E_noise"} else None})
                    for branch in ("mad", "self"):
                        for revision in (1, 2):
                            for agent in AGENTS:
                                parent_branch = "shared" if revision == 1 else branch
                                dependency = f"cbm:{base}:team{run_id}:{condition}:s{stage}:{parent_branch}:{agent}:r{revision - 1}"
                                rows.append({**meta, "request_id": f"cbm:{base}:team{run_id}:{condition}:s{stage}:{branch}:{agent}:r{revision}", "task_family": "cbm", "condition": condition, "stage": stage, "branch": branch, "agent_id": agent, "revision_round": revision, "protocol": "candidate_set", "oracle": oracle, "depends_on": [dependency], "seed": stable_seed(root_seed, base, agent, paired_condition_seed_key, stage, revision), "seed_pairing": "C_clean_E_noise" if condition in {"C_clean", "E_noise"} else None})
    return rows


def prepare(root: Path, repository_root: Path) -> dict[str, Any]:
    """Freeze selection, source data, protocol plan, MAD plan, and provenance."""
    cbm_root = repository_root / "experiments/cbm_attr_v1"
    all_items = read_jsonl(cbm_root / "data/source_items.jsonl")
    all_episodes = read_jsonl(cbm_root / "data/episodes.jsonl")
    all_snapshots = read_jsonl(cbm_root / "data/snapshots.jsonl")
    old_protocol_plan = read_jsonl(cbm_root / "data/request_plan.jsonl")
    selected = _balanced_selection(all_items, SELECTION_SEED)
    selected_ids = {item["base_item_id"] for item in selected}
    episodes = [copy.deepcopy(row) for row in all_episodes if row["base_item_id"] in selected_ids]
    snapshots = [copy.deepcopy(row) for row in all_snapshots if row["base_item_id"] in selected_ids]
    episode_by_id = {row["base_item_id"]: row for row in episodes}
    protocol_plan = [copy.deepcopy(row) for row in old_protocol_plan if row["base_item_id"] in selected_ids]
    if len(protocol_plan) != 1404:
        raise ValueError(f"Expected 1,404 protocol-check requests, found {len(protocol_plan)}")
    mad_plan = build_mad_plan(selected, episode_by_id)
    if len(mad_plan) != 10530:
        raise ValueError(f"Expected 10,530 MAD requests, found {len(mad_plan)}")

    source_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repository_root, text=True).strip()
    scenario_counts = Counter(item["scenario"] for item in selected)
    gold_counts = Counter(item["gold_answer"] for item in selected)
    manifest = []
    for item in sorted(selected, key=difficulty_cell):
        manifest.append({
            "source_item_id": item["item_id"], "base_item_id": item["base_item_id"],
            "difficulty_cell": difficulty_cell(item), **item["difficulty_factors"],
            "scenario": item["scenario"], "source_gold": item["gold_answer"],
            "selection_seed": SELECTION_SEED,
            "selection_method": "global_deterministic_balance_one_per_cell_without_model_outcomes",
            "source_commit": source_commit,
            "question_sha256": sha256_json(item["question"]),
            "structured_sha256": sha256_json({"constraints": item["constraints"], "entities": item["entities"], "matrix": item["option_constraint_matrix"], "violations": item["option_violation_signature"]}),
        })

    data = root / "data"
    write_jsonl(data / "selection_manifest.jsonl", manifest)
    write_jsonl(data / "source_items.jsonl", selected)
    write_jsonl(data / "episodes.jsonl", episodes)
    write_jsonl(data / "snapshots.jsonl", snapshots)
    write_jsonl(data / "protocol_request_plan.jsonl", protocol_plan)
    write_jsonl(data / "mad_request_plan.jsonl", mad_plan)

    from cbm_attr_v1.prompts import SET_SYSTEM_PROMPT as old_prompt
    diff = "".join(difflib.unified_diff(old_prompt.splitlines(True), SET_SYSTEM_PROMPT_V2.splitlines(True), fromfile="candidate_set_v1", tofile="candidate_set_v2"))
    (data / "candidate_set_prompt_v1_to_v2.diff").write_text(diff, encoding="utf-8")
    provenance = {
        "source_commit": source_commit,
        "selection_seed": SELECTION_SEED,
        "source_files": {name: file_sha256(cbm_root / "data" / name) for name in ("source_items.jsonl", "episodes.jsonl", "snapshots.jsonl", "request_plan.jsonl")},
        "selected_item_count": len(selected), "scenario_distribution": dict(sorted(scenario_counts.items())), "gold_distribution": dict(sorted(gold_counts.items())),
        "protocol_logical_requests": len(protocol_plan), "mad_logical_requests": len(mad_plan),
    }
    write_json(data / "provenance.json", provenance)
    return provenance
