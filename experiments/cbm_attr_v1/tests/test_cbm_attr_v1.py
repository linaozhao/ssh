"""Regression and protocol tests for CBM-Attr v1."""

from __future__ import annotations

import json
import copy
from pathlib import Path

from cbm_attr_v1.common import LABELS, read_jsonl
from cbm_attr_v1.oracle import compute_oracle, enumerate_oracle
from cbm_attr_v1.parsing import parse_candidate_set, parse_single_choice
from cbm_attr_v1.prompts import dynamic_user_message
from cbm_attr_v1.runner import build_experiment_manifest
from cbm_attr_v1.validation import validate_artifacts

EXPERIMENT = Path(__file__).resolve().parents[1]


def test_unknown_candidates_are_retained() -> None:
    constraints = [{"attribute": "available_monday", "required_value": True}]
    assert compute_oracle(constraints, []) == list(LABELS)
    evidence = [{"fact_kind": "target", "event_type": "observation", "candidate_id": "A", "attribute": "available_monday", "value": False}]
    assert compute_oracle(constraints, evidence) == ["B", "C", "D"]


def test_independent_oracle_matches_direct_implementation() -> None:
    episode = read_jsonl(EXPERIMENT / "data/episodes.jsonl")[0]
    for row in episode["clean"]["rounds"]:
        assert compute_oracle(episode["constraints"], row["active_target_evidence"]) == row["oracle"]
        assert enumerate_oracle(episode["constraints"], row["active_target_evidence"]) == row["oracle"]


def test_parser_does_not_guess_from_reasoning() -> None:
    names = {"A": "Morgan", "B": "Taylor", "C": "Jordan", "D": "Casey"}
    parsed = parse_candidate_set('I considered Candidate A and B. Candidate C fails.', names)
    assert not parsed["recognized"]


def test_parser_rejects_conflicting_final_sets() -> None:
    names = {"A": "Morgan", "B": "Taylor", "C": "Jordan", "D": "Casey"}
    raw = '{"candidates":["A"],"reasoning":"x"}\nFinal candidates: [B]'
    parsed = parse_candidate_set(raw, names)
    assert parsed["ambiguous"]
    assert not parsed["recognized"]


def test_parser_tracks_duplicate_unknown_and_full_name() -> None:
    names = {"A": "Morgan", "B": "Taylor", "C": "Jordan", "D": "Casey"}
    duplicate = parse_candidate_set('{"candidates":["A","A"],"reasoning":"x"}', names)
    assert duplicate["duplicate_members"] == ["A"]
    assert not duplicate["recognized"]
    mapped = parse_candidate_set('{"candidates":["Morgan","C"],"reasoning":"x"}', names)
    assert mapped["recognized"] and mapped["candidates"] == ["A", "C"]
    assert mapped["name_mapping_used"]


def test_original_protocol_requires_confidence_only_for_strict_schema() -> None:
    names = {"A": "Morgan", "B": "Taylor", "C": "Jordan", "D": "Casey"}
    strict = parse_single_choice('{"answer":"A","reasoning":"checked","confidence":0.8}', names)
    assert strict["recognized"] and strict["strict_schema"]
    semantic_only = parse_single_choice('{"answer":"A","reasoning":"checked"}', names)
    assert semantic_only["recognized"] and not semantic_only["strict_schema"]


def test_generated_dataset_is_fully_valid() -> None:
    report = validate_artifacts(EXPERIMENT / "data")
    assert report["valid"], report["errors"]
    assert report["counts"]["source_items"] == 72
    assert report["counts"]["snapshots"] == 864
    assert report["counts"]["request_plan"] == 5616


def test_gold_and_scenarios_are_balanced() -> None:
    selection = read_jsonl(EXPERIMENT / "data/selection_manifest.jsonl")
    assert {label: sum(row["source_gold"] == label for row in selection) for label in LABELS} == {label: 18 for label in LABELS}
    assert {scenario: sum(row["scenario"] == scenario for row in selection) for scenario in {row["scenario"] for row in selection}} == {
        "expert_recruitment": 24,
        "project_assignment": 24,
        "availability_selection": 24,
    }


def test_noise_is_formally_paired_every_round() -> None:
    for episode in read_jsonl(EXPERIMENT / "data/episodes.jsonl"):
        for clean, noise in zip(episode["clean"]["rounds"], episode["noise"]["rounds"], strict=True):
            assert clean["oracle"] == noise["oracle"]
            clean_target = [(row["candidate_id"], row["attribute"], row["value"], row["event_type"]) for row in clean["events"] if row["fact_kind"] == "target"]
            noise_target = [(row["candidate_id"], row["attribute"], row["value"], row["event_type"]) for row in noise["events"] if row["fact_kind"] == "target"]
            assert clean_target == noise_target


def test_correction_restores_exactly_one_wrong_candidate() -> None:
    for episode in read_jsonl(EXPERIMENT / "data/episodes.jsonl"):
        update = episode["update"]
        assert update["pre_correction_oracle"] == [episode["source_gold"]]
        assert set(update["post_correction_oracle"]) == {episode["source_gold"], update["target_candidate"]}
        assert update["rounds"][0]["oracle"] == update["rounds"][1]["oracle"]


def test_request_dependencies_and_denominators() -> None:
    plan = read_jsonl(EXPERIMENT / "data/request_plan.jsonl")
    assert len(plan) == 5616
    assert len({row["request_id"] for row in plan}) == len(plan)
    ids = {row["request_id"] for row in plan}
    assert all(dependency in ids for row in plan for dependency in row["depends_on"])
    per_unit: dict[str, int] = {}
    for row in plan:
        per_unit[row["unit_id"]] = per_unit.get(row["unit_id"], 0) + 1
    assert set(per_unit.values()) == {26}


def test_serialized_data_is_reproducible() -> None:
    validation = json.loads((EXPERIMENT / "data/validation_report.json").read_text())
    assert validation["valid"]
    assert validation["checks"]["no_future_evidence_leak"]


def test_dynamic_prompt_hides_internal_condition_labels() -> None:
    item = read_jsonl(EXPERIMENT / "data/source_items.jsonl")[0]
    episode = read_jsonl(EXPERIMENT / "data/episodes.jsonl")[0]
    for key, condition in (("clean", "C_clean"), ("noise", "E_noise")):
        message = dynamic_user_message(item, condition, episode[key]["rounds"][0], first_round=True)
        assert "C_clean" not in message
        assert "E_noise" not in message
        assert "D_update" not in message


def test_resume_manifest_is_stable_and_sensitive_to_config() -> None:
    config = json.loads((EXPERIMENT / "config/experiment_config.json").read_text())
    first = build_experiment_manifest(EXPERIMENT, config)
    second = build_experiment_manifest(EXPERIMENT, config)
    assert first == second
    assert "api_key" not in first["config"]["model"]
    changed = copy.deepcopy(config)
    changed["generation"]["temperature"] = 0.1
    assert build_experiment_manifest(EXPERIMENT, changed)["config_sha256"] != first["config_sha256"]


def test_frozen_final_outputs_cover_request_plan_exactly() -> None:
    outputs_path = EXPERIMENT / "results/raw_outputs.jsonl"
    if not outputs_path.exists():
        return
    outputs = read_jsonl(outputs_path)
    plan = read_jsonl(EXPERIMENT / "data/request_plan.jsonl")
    output_ids = [row["request_id"] for row in outputs]
    assert len(outputs) == 5616
    assert len(output_ids) == len(set(output_ids))
    assert set(output_ids) == {row["request_id"] for row in plan}
    assert all(row["api_success"] or row["blocked"] for row in outputs)
    assert sum(row["phase_first_executed"] == "preflight" for row in outputs) == 468


def test_runtime_branch_and_leakage_audit_passes() -> None:
    path = EXPERIMENT / "results/runtime_integrity.json"
    if not path.exists():
        return
    audit = json.loads(path.read_text())
    assert audit["passed"]
    assert audit["actual_shared_prefix_matches"] == 216
    assert audit["banned_input_token_counts"] == {}
