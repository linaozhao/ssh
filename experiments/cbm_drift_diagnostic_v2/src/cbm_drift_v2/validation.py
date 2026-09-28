"""Independent structural, semantic, pairing, and request-plan validation."""

from __future__ import annotations

from collections import Counter
from typing import Any

from cbm_drift_v2.common import AGENTS, LABELS, VARIANTS, sha256_json, stable_seed
from cbm_drift_v2.state import EvidenceReplayError, enumerate_candidate_set, replay_stages


def validate_dataset(
    config: dict[str, Any],
    sequences: list[dict[str, Any]],
    protocol_plan: list[dict[str, Any]],
    mad_plan: list[dict[str, Any]],
) -> dict[str, Any]:
    """Recompute every state and return all detected errors."""
    errors: list[str] = []
    if len(sequences) != 36:
        errors.append(f"expected 36 sequences, found {len(sequences)}")
    by_family: dict[str, dict[str, dict[str, Any]]] = {}
    for row in sequences:
        by_family.setdefault(row["family_id"], {})[row["variant_type"]] = row
        if len(row["stages"]) != 5 or len(row["stage_states"]) != 5:
            errors.append(f"{row['variant_id']}: expected five stages and states")
            continue
        if set(row["candidate_map"]) != set(LABELS):
            errors.append(f"{row['variant_id']}: invalid candidate map")
        if not row["rules"] or any(not rule.get("natural_language") for rule in row["rules"]):
            errors.append(f"{row['variant_id']}: missing rule realization")
        try:
            recomputed = replay_stages(row["rules"], row["stages"])
        except EvidenceReplayError as exc:
            errors.append(f"{row['variant_id']}: replay failed: {exc}")
            continue
        if recomputed != row["stage_states"]:
            errors.append(f"{row['variant_id']}: serialized state differs from independent replay")
        for state in recomputed:
            if enumerate_candidate_set(row["rules"], state["active_evidence"]) != state["oracle"]:
                errors.append(f"{row['variant_id']}: direct/enumerated oracle mismatch at T{state['evidence_stage']}")
            if any(int(event.get("appearance_stage", 0)) > state["evidence_stage"] for event in state["active_evidence"]):
                errors.append(f"{row['variant_id']}: future evidence leaked into T{state['evidence_stage']}")
        expected_hash = sha256_json({"candidate_map": row["candidate_map"], "rules": row["rules"], "stages": row["stages"]})
        if row["normalized_content_sha256"] != expected_hash:
            errors.append(f"{row['variant_id']}: normalized content hash mismatch")
        for stage in row["stages"]:
            for event in stage["events"]:
                if not str(event.get("text", "")).strip():
                    errors.append(f"{row['variant_id']}: empty evidence text")
                if event["fact_kind"] == "target" and event["candidate_name"] != row["candidate_map"][event["candidate_id"]]["name"]:
                    errors.append(f"{row['variant_id']}: candidate name mismatch in {event['evidence_id']}")

    if len(by_family) != 12:
        errors.append(f"expected 12 families, found {len(by_family)}")
    for family, variants in by_family.items():
        if set(variants) != set(VARIANTS):
            errors.append(f"{family}: missing variants")
            continue
        clean, update, noise = (variants[key] for key in VARIANTS)
        if clean["candidate_map"] != update["candidate_map"] or clean["candidate_map"] != noise["candidate_map"]:
            errors.append(f"{family}: candidate identity changed across variants")
        if clean["rules"] != update["rules"] or clean["rules"] != noise["rules"]:
            errors.append(f"{family}: rules changed across variants")
        for stage in range(1, 4):
            if clean["stages"][stage - 1]["events"] != update["stages"][stage - 1]["events"]:
                errors.append(f"{family}: update T{stage} differs from clean")
            if clean["stages"][stage - 1]["events"] != noise["stages"][stage - 1]["events"]:
                errors.append(f"{family}: noise T{stage} differs from clean")
        if any(clean["stage_states"][stage]["oracle"] != clean["stage_states"][2]["oracle"] for stage in (3, 4)):
            errors.append(f"{family}: clean T4/T5 changed oracle")
        if update["stage_states"][2]["oracle"] == update["stage_states"][3]["oracle"]:
            errors.append(f"{family}: update T4 did not change oracle")
        if update["stage_states"][3]["oracle"] != update["stage_states"][4]["oracle"]:
            errors.append(f"{family}: update T5 changed oracle")
        for stage in range(5):
            clean_targets = [event for event in clean["stages"][stage]["events"] if event["fact_kind"] == "target"]
            noise_targets = [event for event in noise["stages"][stage]["events"] if event["fact_kind"] == "target"]
            if clean_targets != noise_targets:
                errors.append(f"{family}: noise changed target evidence at T{stage + 1}")
            if clean["stage_states"][stage]["oracle"] != noise["stage_states"][stage]["oracle"]:
                errors.append(f"{family}: noise changed oracle at T{stage + 1}")
        noise_events = [event for stage in noise["stages"][3:] for event in stage["events"] if event["fact_kind"] == "non_target"]
        if not noise_events:
            errors.append(f"{family}: no T4/T5 non-target information")

    if len(protocol_plan) != 108 or len({row["request_id"] for row in protocol_plan}) != len(protocol_plan):
        errors.append("protocol plan must contain 108 unique requests")
    if len(mad_plan) != 1620 or len({row["request_id"] for row in mad_plan}) != len(mad_plan):
        errors.append("MAD plan must contain 1620 unique requests")
    by_variant = {row["variant_id"]: row for row in sequences}
    for row in mad_plan:
        sequence = by_variant.get(row["variant_id"])
        if sequence is None:
            errors.append(f"unknown variant in request plan: {row['variant_id']}")
            continue
        oracle = sequence["stage_states"][row["evidence_stage"] - 1]["oracle"]
        if row["oracle"] != oracle:
            errors.append(f"{row['request_id']}: oracle mismatch")
        expected_seed = stable_seed(
            config["experiment_id"], row["variant_id"], row["evidence_stage"], row["round"], row["agent_id"]
        )
        if row["seed"] != expected_seed:
            errors.append(f"{row['request_id']}: seed mismatch")
    seed_groups: dict[tuple[str, int, int], set[int]] = {}
    for row in mad_plan:
        seed_groups.setdefault((row["variant_id"], row["evidence_stage"], row["round"]), set()).add(row["seed"])
    if any(len(values) != len(AGENTS) for values in seed_groups.values()):
        errors.append("agents share a derived seed within a stage-round")

    content_hashes = Counter(row["normalized_content_sha256"] for row in sequences)
    if any(count > 1 for count in content_hashes.values()):
        errors.append("duplicate normalized evidence sequence detected")
    family_base = {(row["family_id"], row["base_item_id"]) for row in sequences}
    if len(family_base) != 12:
        errors.append("family/base relation is not one-to-one")
    return {
        "passed": not errors,
        "errors": errors,
        "base_items": len(by_family),
        "sequences": len(sequences),
        "protocol_requests": len(protocol_plan),
        "mad_requests": len(mad_plan),
        "variant_distribution": dict(sorted(Counter(row["variant_type"] for row in sequences).items())),
    }
