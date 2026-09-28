"""Deterministic 12-family, three-variant CBM diagnostic dataset construction."""

from __future__ import annotations

import copy
import random
from collections import Counter
from pathlib import Path
from typing import Any

from cbm_drift_v2.common import AGENTS, LABELS, VARIANTS, read_jsonl, sha256_json, stable_seed, write_json, write_jsonl
from cbm_drift_v2.state import replay_stages


def _cell(item: dict[str, Any]) -> str:
    factors = item["difficulty_factors"]
    return "__".join((factors["constraint_load"], factors["distractor_similarity"], factors["information_load"]))


def _selection_score(rows: list[dict[str, Any]]) -> tuple[int, int, int, tuple[str, ...]]:
    targets = {
        "scenario": {key: 4 for key in ("expert_recruitment", "project_assignment", "availability_selection")},
        "constraint_load": {key: 4 for key in ("CL1", "CL2", "CL3")},
        "distractor_similarity": {key: 4 for key in ("DS1_far", "DS2_medium", "DS3_near")},
        "information_load": {key: 6 for key in ("IL1_low", "IL2_high")},
        "gold": {key: 3 for key in LABELS},
    }
    counts = {
        "scenario": Counter(row["scenario"] for row in rows),
        "constraint_load": Counter(row["difficulty_factors"]["constraint_load"] for row in rows),
        "distractor_similarity": Counter(row["difficulty_factors"]["distractor_similarity"] for row in rows),
        "information_load": Counter(row["difficulty_factors"]["information_load"] for row in rows),
        "gold": Counter(row["gold_answer"] for row in rows),
    }
    imbalance = sum(abs(counts[group][key] - target) for group, values in targets.items() for key, target in values.items())
    cell_duplicates = len(rows) - len({_cell(row) for row in rows})
    attributes = {constraint["attribute"] for row in rows for constraint in row["constraints"]}
    return imbalance, cell_duplicates, -len(attributes), tuple(sorted(row["base_item_id"] for row in rows))


def select_source_items(
    source: list[dict[str, Any]], *, count: int, seed: int, excluded_base_ids: set[str] | None = None
) -> list[dict[str, Any]]:
    """Select before inference, balancing metadata without reading model outcomes."""
    eligible = [row for row in source if row["base_item_id"] not in (excluded_base_ids or set())]
    if len(eligible) < count:
        raise ValueError(f"Only {len(eligible)} source items remain for a {count}-item selection")
    rng = random.Random(seed)
    best: tuple[tuple[int, int, int, tuple[str, ...]], list[dict[str, Any]]] | None = None
    for _ in range(100_000):
        candidate = rng.sample(eligible, count)
        score = _selection_score(candidate)
        if best is None or score < best[0]:
            best = (score, candidate)
    assert best is not None
    return sorted((copy.deepcopy(row) for row in best[1]), key=lambda row: row["base_item_id"])


def _normalize_event(source: dict[str, Any], *, stage: int) -> dict[str, Any]:
    event = copy.deepcopy(source)
    event["appearance_stage"] = stage
    event["supersedes_evidence_id"] = event.pop("replaces_evidence_id", None)
    event.setdefault("restates_evidence_id", None)
    return event


def _clean_stages(old_episode: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "evidence_stage": int(row["round_id"]),
            "stage_kind": "target_evidence" if int(row["round_id"]) <= 3 else "stay_restatement",
            "events": [_normalize_event(event, stage=int(row["round_id"])) for event in row["events"]],
        }
        for row in old_episode["clean"]["rounds"]
    ]


def _update_stages(old_episode: dict[str, Any]) -> list[dict[str, Any]]:
    stages = _clean_stages(old_episode)[:3]
    for row in old_episode["update"]["rounds"]:
        stage = int(row["round_id"])
        stages.append({
            "evidence_stage": stage,
            "stage_kind": "formal_correction" if stage == 4 else "post_correction_restatement",
            "events": [_normalize_event(event, stage=stage) for event in row["events"]],
        })
    return stages


def _noise_stages(old_episode: dict[str, Any]) -> list[dict[str, Any]]:
    stages = _clean_stages(old_episode)
    noise = [
        _normalize_event(event, stage=0)
        for row in old_episode["noise"]["rounds"]
        for event in row["events"]
        if event["fact_kind"] == "non_target"
    ]
    noise.sort(key=lambda row: (row["candidate_id"], str(row.get("non_target_key")), row["evidence_id"]))
    midpoint = (len(noise) + 1) // 2
    for stage_number, additions in ((4, noise[:midpoint]), (5, noise[midpoint:])):
        for event in additions:
            event["appearance_stage"] = stage_number
            event["first_appearance_round"] = stage_number
        stages[stage_number - 1]["events"].extend(additions)
        stages[stage_number - 1]["stage_kind"] = "non_target_information"
    return stages


def _task_text(item: dict[str, Any]) -> str:
    requirements = "\n".join(
        f"{index}. {row['natural_language']}" for index, row in enumerate(item["constraints"], start=1)
    )
    candidates = "\n".join(f"{label}. {item['entities'][label]['name']}" for label in LABELS)
    return (
        "A team is tracking which candidates have not yet been eliminated as evidence arrives.\n\n"
        f"Fixed requirements:\n{requirements}\n\nCandidates:\n{candidates}"
    )


def build_variant(
    item: dict[str, Any], old_episode: dict[str, Any], *, family_index: int, variant: str, seed: int
) -> dict[str, Any]:
    """Build one five-stage evidence sequence and recompute all standard states."""
    if variant == "clean_stay":
        stages = _clean_stages(old_episode)
    elif variant == "evidence_update":
        stages = _update_stages(old_episode)
    elif variant == "irrelevant_noise":
        stages = _noise_stages(old_episode)
    else:
        raise ValueError(f"Unknown variant: {variant}")
    states = replay_stages(item["constraints"], stages)
    family_id = f"cbm_v2_family_{family_index:03d}"
    variant_id = f"{family_id}::{variant}"
    candidate_map = {
        label: {"candidate_id": label, "name": item["entities"][label]["name"]}
        for label in LABELS
    }
    record = {
        "base_item_id": item["base_item_id"],
        "family_id": family_id,
        "variant_id": variant_id,
        "variant_type": variant,
        "split": "development",
        "source_data_version": "cbm_attr_v1.0",
        "source_item_id": item["item_id"],
        "generation_seed": seed,
        "scenario": item["scenario"],
        "difficulty_factors": copy.deepcopy(item["difficulty_factors"]),
        "candidate_map": candidate_map,
        "rules": copy.deepcopy(item["constraints"]),
        "task_text": _task_text(item),
        "stages": stages,
        "stage_states": states,
        "source_gold": item["gold_answer"],
        "family_relation": {
            "shared_candidates": True,
            "shared_rules": True,
            "shared_t1_t3_target_evidence": True,
        },
    }
    record["normalized_content_sha256"] = sha256_json({
        "candidate_map": candidate_map,
        "rules": record["rules"],
        "stages": stages,
    })
    return record


def _distribution(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "scenario": dict(sorted(Counter(row["scenario"] for row in rows).items())),
        "constraint_load": dict(sorted(Counter(row["difficulty_factors"]["constraint_load"] for row in rows).items())),
        "distractor_similarity": dict(sorted(Counter(row["difficulty_factors"]["distractor_similarity"] for row in rows).items())),
        "source_information_load": dict(sorted(Counter(row["difficulty_factors"]["information_load"] for row in rows).items())),
        "gold_position": dict(sorted(Counter(row["gold_answer"] for row in rows).items())),
        "difficulty_cells": dict(sorted(Counter(_cell(row) for row in rows).items())),
        "constraint_attributes": dict(sorted(Counter(c["attribute"] for row in rows for c in row["constraints"]).items())),
    }


def build_request_plans(config: dict[str, Any], variants: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Build the 108 protocol and 1,620 MAD logical request plans."""
    by_family_variant = {(row["family_id"], row["variant_type"]): row for row in variants}
    families = sorted({row["family_id"] for row in variants})
    protocol: list[dict[str, Any]] = []
    for family_id in families:
        selections = (
            ("early_unknown", by_family_variant[(family_id, "clean_stay")], 1),
            ("clean_t3", by_family_variant[(family_id, "clean_stay")], 3),
            ("update_t4", by_family_variant[(family_id, "evidence_update")], 4),
        )
        for snapshot_name, variant, stage in selections:
            for run_id, seed in enumerate(config["protocol_check"]["seeds"], start=1):
                protocol.append({
                    "request_id": f"protocol:{family_id}:{snapshot_name}:run{run_id}",
                    "family_id": family_id,
                    "base_item_id": variant["base_item_id"],
                    "variant_id": variant["variant_id"],
                    "snapshot_name": snapshot_name,
                    "evidence_stage": stage,
                    "run_id": run_id,
                    "seed": seed,
                    "oracle": variant["stage_states"][stage - 1]["oracle"],
                })
    mad: list[dict[str, Any]] = []
    experiment_id = config["experiment_id"]
    for variant in sorted(variants, key=lambda row: row["variant_id"]):
        for stage in config["mad"]["stages"]:
            for round_id in config["mad"]["rounds"]:
                for agent in config["mad"]["agents"]:
                    request_id = f"mad:{variant['variant_id']}:t{stage}:r{round_id}:{agent}"
                    if round_id == 0:
                        dependencies = [] if stage == 1 else [f"mad:{variant['variant_id']}:t{stage - 1}:r2:{agent}"]
                    else:
                        dependencies = [
                            f"mad:{variant['variant_id']}:t{stage}:r{round_id - 1}:{peer}"
                            for peer in config["mad"]["agents"]
                        ]
                    mad.append({
                        "request_id": request_id,
                        "trajectory_id": variant["variant_id"],
                        "variant_id": variant["variant_id"],
                        "family_id": variant["family_id"],
                        "base_item_id": variant["base_item_id"],
                        "variant_type": variant["variant_type"],
                        "evidence_stage": stage,
                        "round": round_id,
                        "agent_id": agent,
                        "seed": stable_seed(experiment_id, variant["variant_id"], stage, round_id, agent),
                        "depends_on": dependencies,
                        "oracle": variant["stage_states"][stage - 1]["oracle"],
                    })
    return protocol, mad


def prepare_dataset(
    repository_root: Path,
    experiment_root: Path,
    config: dict[str, Any],
    *,
    split: str = "development",
    output_dir: Path | None = None,
    excluded_base_ids: set[str] | None = None,
) -> dict[str, Any]:
    """Select source families and materialize data plus request plans."""
    source_items = read_jsonl(repository_root / config["source"]["items"])
    old_episodes = {row["base_item_id"]: row for row in read_jsonl(repository_root / config["source"]["episodes"])}
    count = int(config["source"]["base_item_count"])
    selected = select_source_items(source_items, count=count, seed=int(config["selection_seed"]), excluded_base_ids=excluded_base_ids)
    variants = [
        build_variant(
            item,
            old_episodes[item["base_item_id"]],
            family_index=index,
            variant=variant,
            seed=stable_seed(config["schedule_seed"], item["base_item_id"], variant),
        )
        for index, item in enumerate(selected, start=1)
        for variant in VARIANTS
    ]
    for row in variants:
        row["split"] = split
    protocol, mad = build_request_plans(config, variants)
    target = output_dir or experiment_root / "data"
    manifest = [
        {
            "family_id": f"cbm_v2_family_{index:03d}",
            "base_item_id": item["base_item_id"],
            "source_item_id": item["item_id"],
            "scenario": item["scenario"],
            "difficulty_cell": _cell(item),
            "gold_position": item["gold_answer"],
            "selection_seed": config["selection_seed"],
            "selection_method": "metadata_only_random_search_balance_without_model_outputs",
            "source_content_sha256": sha256_json(item),
        }
        for index, item in enumerate(selected, start=1)
    ]
    write_jsonl(target / "selection_manifest.jsonl", manifest)
    write_jsonl(target / "source_items.jsonl", selected)
    write_jsonl(target / "evidence_sequences.jsonl", variants)
    write_jsonl(target / "protocol_request_plan.jsonl", protocol)
    write_jsonl(target / "mad_request_plan.jsonl", mad)
    summary = {
        "split": split,
        "base_items": len(selected),
        "variants": len(variants),
        "stages_per_variant": 5,
        "protocol_requests": len(protocol),
        "mad_requests": len(mad),
        "selection_score": _selection_score(selected)[:3],
        "distribution": _distribution(selected),
    }
    write_json(target / "dataset_summary.json", summary)
    return summary
