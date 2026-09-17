"""Structural, semantic, leakage, and dependency validation."""

from __future__ import annotations

from collections import Counter
from typing import Any

from cbm_attr_v1.oracle import compute_oracle, enumerate_oracle
from mad_drift_pilot.common import AGENTS, LABELS, difficulty_cell
from mad_drift_pilot.prompts import SET_SYSTEM_PROMPT_V2


FORBIDDEN_MODEL_INPUT_TOKENS = ("source_gold", "gold_answer", "option_violation_signature", "difficulty_cell", "oracle")


def validate_frozen_data(items: list[dict[str, Any]], episodes: list[dict[str, Any]], protocol_plan: list[dict[str, Any]], mad_plan: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate all formal invariants and request identities."""
    errors: list[str] = []
    item_by_id = {row["base_item_id"]: row for row in items}
    episode_by_id = {row["base_item_id"]: row for row in episodes}
    if len(items) != 18 or len(item_by_id) != 18:
        errors.append("selection_must_contain_18_unique_items")
    cells = Counter(difficulty_cell(item) for item in items)
    if len(cells) != 18 or set(cells.values()) != {1}:
        errors.append("selection_must_cover_each_cell_once")
    if len(protocol_plan) != 1404 or len({row["request_id"] for row in protocol_plan}) != 1404:
        errors.append("protocol_plan_count_or_identity_error")
    if len(mad_plan) != 10530 or len({row["request_id"] for row in mad_plan}) != 10530:
        errors.append("mad_plan_count_or_identity_error")
    if '["A", "C"]' in SET_SYSTEM_PROMPT_V2 or '["A","C"]' in SET_SYSTEM_PROMPT_V2:
        errors.append("set_prompt_contains_concrete_label_combination")

    plan_ids = {row["request_id"] for row in mad_plan}
    for row in mad_plan:
        if row["agent_id"] not in AGENTS or row["protocol"] not in {"single_choice", "candidate_set"}:
            errors.append(f"invalid_plan_fields:{row['request_id']}")
        for dependency in row["depends_on"]:
            if dependency not in plan_ids:
                errors.append(f"missing_dependency:{row['request_id']}:{dependency}")

    for base, episode in episode_by_id.items():
        item = item_by_id[base]
        for key in ("clean", "noise", "update"):
            for round_data in episode[key]["rounds"]:
                direct = compute_oracle(item["constraints"], round_data["active_target_evidence"])
                enumerated = enumerate_oracle(item["constraints"], round_data["active_target_evidence"])
                if direct != round_data["oracle"] or enumerated != round_data["oracle"]:
                    errors.append(f"oracle_mismatch:{base}:{key}:{round_data['round_id']}")
        clean = {row["round_id"]: row for row in episode["clean"]["rounds"]}
        noise = {row["round_id"]: row for row in episode["noise"]["rounds"]}
        for stage in range(1, 6):
            if clean[stage]["oracle"] != noise[stage]["oracle"]:
                errors.append(f"clean_noise_oracle_mismatch:{base}:s{stage}")
        if clean[3]["oracle"] != [item["gold_answer"]]:
            errors.append(f"clean_final_not_source_gold:{base}")
        update = {row["round_id"]: row for row in episode["update"]["rounds"]}
        target = episode["update"]["target_candidate"]
        expected = sorted((item["gold_answer"], target))
        if update[4]["oracle"] != expected or update[5]["oracle"] != expected:
            errors.append(f"update_oracle_mismatch:{base}")
        if not set(expected).issubset(LABELS):
            errors.append(f"invalid_update_candidates:{base}")

    return {
        "passed": not errors,
        "errors": errors,
        "items": len(items),
        "cells": dict(sorted(cells.items())),
        "protocol_requests": len(protocol_plan),
        "mad_requests": len(mad_plan),
        "scenario_distribution": dict(sorted(Counter(item["scenario"] for item in items).items())),
        "gold_distribution": dict(sorted(Counter(item["gold_answer"] for item in items).items())),
    }

