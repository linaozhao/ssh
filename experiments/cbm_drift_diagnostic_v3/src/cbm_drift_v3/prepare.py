"""Derive four conditions from frozen v2 designs and an explicit shared-history DAG."""

from __future__ import annotations

import copy
import subprocess
from pathlib import Path
from typing import Any

from .common import (AGENTS, BRANCHES, freeze_json, freeze_jsonl, read_jsonl,
                     sha256_file, sha256_json, stable_seed)
from .state import replay_stages

SOURCE_NAMES = {"clean": "clean_stay", "update": "evidence_update", "noise": "irrelevant_noise"}


def derive_sequences(source: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Combine only non-target noise with current corrected formal events."""
    groups: dict[str, dict[str, Any]] = {}
    for row in source:
        groups.setdefault(row["family_id"], {})[row["variant_type"]] = row
    result = []
    for family, variants in sorted(groups.items()):
        for branch in BRANCHES:
            source_name = SOURCE_NAMES.get(branch, "evidence_update")
            row = copy.deepcopy(variants[source_name])
            row["source_variant_type"] = source_name
            row["source_variant_id"] = row.pop("variant_id")
            row.pop("variant_type", None)
            row["branch_type"] = branch
            row["sequence_id"] = f"{family}::{branch}"
            row["variant_id"] = row["sequence_id"]
            if branch == "update_noise":
                for index in (3, 4):
                    noise = [copy.deepcopy(e) for e in variants["irrelevant_noise"]["stages"][index]["events"] if e["fact_kind"] == "non_target"]
                    row["stages"][index]["events"].extend(noise)
                    row["stages"][index]["stage_kind"] = "formal_events_with_non_target_information"
                row["source_noise_variant_id"] = variants["irrelevant_noise"]["variant_id"]
            row["stage_states"] = replay_stages(row["rules"], row["stages"])
            row["normalized_content_sha256"] = sha256_json({k: row[k] for k in ("candidate_map", "rules", "stages")})
            result.append(row)
    return result


def build_request_plans(config: dict[str, Any], sequences: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Generate canonical messages once, with barriers separate from visible peers."""
    by_key = {(r["family_id"], r["branch_type"]): r for r in sequences}
    families = sorted({r["family_id"] for r in sequences})
    run_id = config["run_id"]
    plan, views, protocol = [], [], []
    for family_index, family in enumerate(families, 1):
        clean = by_key[family, "clean"]
        prefix = f"{run_id}:f{family_index:02d}"
        checkpoint = f"{prefix}:checkpoint_t3"

        def mid(branch: str | None, stage: int, round_id: int, agent: str) -> str:
            part = "p" if stage <= 3 else f"b{BRANCHES.index(branch)}"
            return f"{prefix}:{part}:t{stage}:r{round_id}:{agent}"

        for branch, stages in [(None, (1, 2, 3))] + [(b, (4, 5)) for b in BRANCHES]:
            sequence = by_key[family, branch or "clean"]
            for stage in stages:
                for round_id in range(3):
                    for agent in AGENTS:
                        previous = (mid(branch, stage, round_id - 1, agent) if round_id else
                                    mid(branch, stage - 1, 2, agent) if stage > 1 else None)
                        peers = [mid(branch, stage, round_id - 1, a) for a in AGENTS if a != agent] if round_id else []
                        parents = ([previous] if previous else []) + peers
                        barrier = [mid(None, 3, 2, a) for a in AGENTS] if stage == 4 and round_id == 0 else []
                        rid = mid(branch, stage, round_id, agent)
                        plan.append({"run_id": run_id, "family_id": family, "base_item_id": sequence["base_item_id"],
                                     "repeat_id": 1, "phase": "shared_prefix" if branch is None else "branch_suffix",
                                     "branch_type": branch, "request_id": rid, "message_id": rid,
                                     "own_previous_message_id": previous, "parent_message_ids": parents,
                                     "visible_peer_message_ids": peers, "barrier_message_ids": barrier,
                                     "depends_on": sorted(set(parents + barrier)),
                                     "evidence_stage": stage, "round": round_id, "agent_id": agent,
                                     "seed": stable_seed(config["schedule_seed"], family, stage, round_id, agent),
                                     "checkpoint_id": checkpoint, "shared_prefix_id": prefix,
                                     "sequence_id": sequence["sequence_id"]})
        for branch in BRANCHES:
            views.append({"family_id": family, "base_item_id": clean["base_item_id"], "branch_type": branch,
                          "sequence_id": by_key[family, branch]["sequence_id"],
                          "message_ids": [mid(branch, s, r, a) for s in range(1, 6) for r in range(3) for a in AGENTS]})
        for snapshot, branch, stage in (("early_unknown", "clean", 1), ("clean_t3", "clean", 3), ("update_t4", "update", 4)):
            for run_number, seed in enumerate((11, 22, 33), 1):
                protocol.append({"run_id": run_id, "request_id": f"{prefix}:snapshot:{snapshot}:{run_number}",
                                 "family_id": family, "base_item_id": clean["base_item_id"], "snapshot_name": snapshot,
                                 "sequence_id": by_key[family, branch]["sequence_id"], "evidence_stage": stage,
                                 "seed": seed, "run_number": run_number})
    return plan, views, protocol


def capture_source_manifest(repository_root: Path, source_root: Path) -> dict[str, Any]:
    """Hash tracked legacy designs, code and results before touching new artifacts."""
    relative = source_root.relative_to(repository_root)
    names = subprocess.check_output(["git", "ls-files", "-z", str(relative)], cwd=repository_root).decode().split("\0")
    hashes = {name: sha256_file(repository_root / name) for name in names if name}
    return {"source_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repository_root).decode().strip(),
            "files": hashes, "files_sha256": sha256_json(hashes),
            "untracked_policy": "untouched; excluded from frozen tracked baseline"}


def verify_source_manifest(repository_root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    """Detect any legacy source, selection, code or result byte changes."""
    changes = [name for name, digest in manifest["files"].items()
               if not (repository_root / name).exists() or sha256_file(repository_root / name) != digest]
    return {"status": "passed" if not changes else "failed", "checked_files": len(manifest["files"]), "changed_files": changes}


def prepare_dataset(repository_root: Path, experiment_root: Path, config: dict[str, Any]) -> dict[str, Any]:
    """Create new frozen data; never generate replacement source families."""
    source_root = repository_root / "experiments/cbm_drift_diagnostic_v2"
    data = experiment_root / config.get("data_subdir", "data")
    if not data.resolve().is_relative_to((experiment_root / "data").resolve()):
        raise ValueError("Data version must remain under the new experiment data directory")
    manifest_path = data / "source_manifest.json"
    if not manifest_path.exists():
        freeze_json(manifest_path, capture_source_manifest(repository_root, source_root))
    source = read_jsonl(source_root / "data/evidence_sequences.jsonl")
    sequences = derive_sequences(source)
    plan, views, protocol = build_request_plans(config, sequences)
    freeze_jsonl(data / "selection_manifest.jsonl", read_jsonl(source_root / "data/selection_manifest.jsonl"))
    freeze_jsonl(data / "evidence_sequences.jsonl", sequences)
    freeze_jsonl(data / "mad_request_plan.jsonl", plan)
    freeze_jsonl(data / "branch_views.jsonl", views)
    freeze_jsonl(data / "protocol_request_plan.jsonl", protocol)
    freeze_json(data / "dataset_freeze.json", {"run_id": config["run_id"], "config_sha256": sha256_json(config),
                "sequence_sha256": sha256_json(sequences), "plan_sha256": sha256_json(plan),
                "shared_seed_formula": "sha256(schedule_seed,family_id,stage,round,agent); excludes branch",
                "branch_schedule": list(BRANCHES)})
    return {"sequences": len(sequences), "planned_mad": len(plan), "planned_protocol": len(protocol), "branch_views": len(views)}
