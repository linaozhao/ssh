"""High-risk invariants for synchronized discussion and formal evidence."""

from __future__ import annotations

import json

from mad_drift_pilot.common import AGENTS, read_jsonl, sha256_json
from mad_drift_pilot.prompts import (
    SET_MAD_REVISION,
    SET_SELF_REVISION,
    SET_SYSTEM_PROMPT_V2,
    STATIC_MAD_REVISION,
    STATIC_SELF_REVISION,
    peer_block,
)
from mad_drift_pilot.validation import FORBIDDEN_MODEL_INPUT_TOKENS, validate_frozen_data


def test_no_concrete_set_example() -> None:
    assert '["A", "C"]' not in SET_SYSTEM_PROMPT_V2
    assert "candidates: an array" in SET_SYSTEM_PROMPT_V2


def test_frozen_data_and_plans(experiment_root) -> None:
    data = experiment_root / "data"
    report = validate_frozen_data(
        read_jsonl(data / "source_items.jsonl"), read_jsonl(data / "episodes.jsonl"),
        read_jsonl(data / "protocol_request_plan.jsonl"), read_jsonl(data / "mad_request_plan.jsonl"),
    )
    assert report["passed"], report["errors"]


def test_agents_have_distinct_initial_seeds(experiment_root) -> None:
    rows = read_jsonl(experiment_root / "data/mad_request_plan.jsonl")
    initial = [row for row in rows if row["task_family"] == "static" and row["revision_round"] == 0]
    groups: dict[tuple[str, int], set[int]] = {}
    for row in initial:
        groups.setdefault((row["base_item_id"], row["team_run_id"]), set()).add(row["seed"])
    assert all(len(seeds) == 3 for seeds in groups.values())


def test_peer_block_excludes_self_and_uses_only_supplied_round() -> None:
    records = {
        agent: {"parse": {"recognized": True, "answer": label, "reasoning": f"reason-{agent}"}}
        for agent, label in zip(AGENTS, ("A", "B", "C"), strict=True)
    }
    rendered = peer_block(records, "agent_2", set_protocol=False)
    assert "agent_2" not in rendered
    assert "agent_1" in rendered and "agent_3" in rendered


def test_plan_branches_share_start_but_do_not_cross(experiment_root) -> None:
    rows = read_jsonl(experiment_root / "data/mad_request_plan.jsonl")
    by_id = {row["request_id"]: row for row in rows}
    for row in rows:
        if row["revision_round"] == 1:
            dependency = by_id[row["depends_on"][0]]
            assert dependency["branch"] == "shared"
        if row["revision_round"] == 2:
            dependency = by_id[row["depends_on"][0]]
            assert dependency["branch"] == row["branch"]


def test_clean_noise_and_mad_control_use_paired_seeds(experiment_root) -> None:
    rows = read_jsonl(experiment_root / "data/mad_request_plan.jsonl")
    index = {
        (row["base_item_id"], row["team_run_id"], row["condition"], row["stage"], row["branch"], row["agent_id"], row["revision_round"]): row
        for row in rows
    }
    for key, clean in index.items():
        base, run_id, condition, stage, branch, agent, revision = key
        if condition == "C_clean":
            noise = index[(base, run_id, "E_noise", stage, branch, agent, revision)]
            assert clean["seed"] == noise["seed"]
        if branch == "mad":
            control = index[(base, run_id, condition, stage, "self", agent, revision)]
            assert clean["seed"] == control["seed"]


def test_model_input_leakage_terms_are_internal_only() -> None:
    public_prompts = SET_SYSTEM_PROMPT_V2.lower()
    assert all(token.lower() not in public_prompts for token in FORBIDDEN_MODEL_INPUT_TOKENS)


def test_completed_runtime_is_synchronous_and_branch_safe(experiment_root) -> None:
    paths = [experiment_root / "results/static/raw_outputs.jsonl"] + [
        experiment_root / f"results/cbm/raw_outputs_{condition}.jsonl"
        for condition in ("C_clean", "E_noise", "D_update")
    ]
    expected_counts = (810, 4050, 4050, 1620)
    rows = []
    for path, expected in zip(paths, expected_counts, strict=True):
        values = read_jsonl(path)
        assert len(values) == expected
        rows.extend(values)
    assert len(rows) == 10530
    assert len({row["request_id"] for row in rows}) == 10530
    plan = read_jsonl(experiment_root / "data/mad_request_plan.jsonl")
    assert {row["request_id"] for row in rows} == {row["request_id"] for row in plan}
    by_state = {
        (row["base_item_id"], row["team_run_id"], row["task_family"], row["condition"], row["stage"], row["branch"], row["agent_id"], row["revision_round"]): row
        for row in rows
    }
    for row in rows:
        assert row["messages_sha256"] == sha256_json(row["messages"])
        if row["revision_round"] == 0:
            continue
        previous_branch = "shared" if row["revision_round"] == 1 else row["branch"]
        peers = {
            agent: by_state[(row["base_item_id"], row["team_run_id"], row["task_family"], row["condition"], row["stage"], previous_branch, agent, row["revision_round"] - 1)]
            for agent in AGENTS
        }
        set_protocol = row["protocol"] == "candidate_set"
        if row["branch"] == "mad":
            template = SET_MAD_REVISION if set_protocol else STATIC_MAD_REVISION
            expected_prompt = template.format(peers=peer_block(peers, row["agent_id"], set_protocol=set_protocol))
        else:
            expected_prompt = SET_SELF_REVISION if set_protocol else STATIC_SELF_REVISION
        assert row["messages"][-1]["content"] == expected_prompt


def test_final_analysis_matches_complete_runtime(experiment_root) -> None:
    results = experiment_root / "results"
    integrity = json.loads((results / "runtime_integrity.json").read_text(encoding="utf-8"))
    assert integrity["expected"] == integrity["actual"] == integrity["unique"] == 10530
    assert all(integrity[key] == 0 for key in (
        "missing", "unknown", "duplicates", "api_failures", "blocked", "truncated",
        "message_hash_mismatches", "declared_parent_prefix_mismatches",
        "self_branch_peer_block_leaks", "mad_revision_missing_peer_blocks",
    ))
    assert integrity["recognized"] == integrity["strict_schema"] == 10530
    assert integrity["banned_input_tokens"] == {}

    branch_map = read_jsonl(results / "cbm/update_branch_map.jsonl")
    assert len(branch_map) == 162
    assert all(row["prefix_exact"] for row in branch_map)

    state_stats = json.loads((results / "state_statistics.json").read_text(encoding="utf-8"))
    change_stats = json.loads((results / "diagnostic_change_statistics.json").read_text(encoding="utf-8"))
    assert len(state_stats) == 65
    assert len(change_stats) == 13
    assert sum(row["records"] for row in state_stats) == 10530


def pytest_generate_tests(metafunc):
    if "experiment_root" in metafunc.fixturenames:
        from pathlib import Path

        metafunc.parametrize("experiment_root", [Path(__file__).resolve().parents[1]])
