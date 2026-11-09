"""Independent source, state, graph and visibility validation."""

from __future__ import annotations

from collections import Counter
from typing import Any

from .common import AGENTS, BRANCHES
from .state import enumerate_candidate_set, replay_stages


def validate_dataset(sequences: list[dict[str, Any]], plan: list[dict[str, Any]], views: list[dict[str, Any]], source: list[dict[str, Any]]) -> dict[str, Any]:
    """Reject wrong counts, stale evidence, cross-branch parents and hidden leakage."""
    errors = []
    def check(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)
    check(len(sequences) == 48, "expected 48 sequences")
    families = {r["family_id"] for r in sequences}
    check(len(families) == 12, "expected original 12 families")
    by_key = {(r["family_id"], r["branch_type"]): r for r in sequences}
    old = {(r["family_id"], r["variant_type"]): r for r in source}
    check(len(by_key) == len(sequences), "duplicate sequence")
    for row in sequences:
        try:
            recomputed = replay_stages(row["rules"], row["stages"])
            check(recomputed == row["stage_states"], f"stale states {row['sequence_id']}")
            for state in recomputed:
                check(state["oracle"] == enumerate_candidate_set(row["rules"], state["active_evidence"]), "solver/enumerator disagreement")
            original = old[row["family_id"], row["source_variant_type"]]
            check(row["rules"] == original["rules"] and row["candidate_map"] == original["candidate_map"], "task modified")
            if row["branch_type"] != "update_noise":
                check(row["stages"] == original["stages"], "old design events modified")
        except (ValueError, KeyError) as exc:
            errors.append(f"state failure: {exc}")
    for family in families:
        if any((family, b) not in by_key for b in BRANCHES):
            errors.append("missing family branch")
            continue
        rows = {b: by_key[family, b] for b in BRANCHES}
        check(all(r["stages"][:3] == rows["clean"]["stages"][:3] for r in rows.values()), "prefix evidence mismatch")
        for stage in range(5):
            for left, right in (("clean", "noise"), ("update", "update_noise")):
                a, b = rows[left]["stage_states"][stage], rows[right]["stage_states"][stage]
                target = lambda s: [e for e in s["active_evidence"] if e["fact_kind"] == "target"]
                check(target(a) == target(b) and a["oracle"] == b["oracle"], "non-target noise changed formal state")
            noise = lambda b: [e for e in rows[b]["stages"][stage]["events"] if e["fact_kind"] == "non_target"]
            check(noise("noise") == noise("update_noise"), "noise composition mismatch")
    by_id = {r["message_id"]: r for r in plan}
    check(len(plan) == len(by_id) == 1188, "expected 1188 unique canonical requests")
    check(Counter(r["phase"] for r in plan) == {"shared_prefix": 324, "branch_suffix": 864}, "phase count mismatch")
    visited = set()
    lookup = {(r["family_id"], r["branch_type"], r["evidence_stage"], r["round"], r["agent_id"]): r for r in plan}
    for row in plan:
        try:
            stage, round_id, branch = row["evidence_stage"], row["round"], row["branch_type"]
            expected_own = None
            if stage > 1 or round_id:
                s, r = (stage, round_id - 1) if round_id else (stage - 1, 2)
                b = None if s <= 3 else branch
                expected_own = lookup[row["family_id"], b, s, r, row["agent_id"]]["message_id"]
            expected_peers = sorted(lookup[row["family_id"], branch, stage, round_id - 1, a]["message_id"] for a in AGENTS if a != row["agent_id"]) if round_id else []
            check(row["own_previous_message_id"] == expected_own, "wrong own history")
            check(sorted(row["visible_peer_message_ids"]) == expected_peers, "wrong visible peers")
            expected_parents = ([expected_own] if expected_own else []) + expected_peers
            check(sorted(row["parent_message_ids"]) == sorted(expected_parents), "parent/visibility mismatch")
            barriers = [lookup[row["family_id"], None, 3, 2, a]["message_id"] for a in AGENTS] if stage == 4 and round_id == 0 else []
            check(set(row["barrier_message_ids"]) == set(barriers), "missing T3 checkpoint barrier")
            check(set(row["depends_on"]) == set(expected_parents + barriers), "dependency mismatch")
            check(set(row["depends_on"]) <= visited, "future/missing dependency or non-topological plan")
            check(row["sequence_id"] == by_key[row["family_id"], branch or "clean"]["sequence_id"], "wrong sequence for branch")
            check("oracle" not in row, "oracle leaked into execution plan")
            visited.add(row["message_id"])
        except KeyError as exc:
            errors.append(f"missing graph node: {exc}")
    check(len(views) == 48 and sum(len(v["message_ids"]) for v in views) == 2160, "expected 2160 view references")
    ref_counts = Counter(mid for v in views for mid in v["message_ids"])
    for mid, row in by_id.items():
        check(ref_counts[mid] == (4 if row["phase"] == "shared_prefix" else 1), "shared prefix reference count mismatch")
    return {"status": "passed" if not errors else "failed", "errors": errors, "sequence_count": len(sequences),
            "unique_mad_requests": len(by_id), "shared_prefix_requests": 324, "branch_suffix_requests": 864,
            "branch_views": len(views), "view_references": sum(map(lambda v: len(v["message_ids"]), views)),
            "semantics": "not-yet-eliminated; unknown is not a violation"}
