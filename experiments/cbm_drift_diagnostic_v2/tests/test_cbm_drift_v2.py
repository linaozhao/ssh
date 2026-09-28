"""Regression tests for CBM drift diagnostic v2."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cbm_drift_v2.common import read_json, read_jsonl, sha256_json
from cbm_drift_v2.diagnostics import build_message_diagnostics, build_program_events
from cbm_drift_v2.evaluation import evaluate_events
from cbm_drift_v2.judge import validate_prediction
from cbm_drift_v2.parsing import parse_answer_set
from cbm_drift_v2.prompts import contains_concrete_answer_example
from cbm_drift_v2.runner import ExperimentRunner
from cbm_drift_v2.state import EvidenceReplayError, replay_evidence, solve_candidate_set
from cbm_drift_v2.tokenplan_judge import (
    TRANSPORT_VERSION,
    TokenPlanJudgeRunner,
    _consume_sse_line,
    _new_stream_accumulator,
    _retryable_record,
    _stream_body,
    build_paired_manifest,
    build_preflight_manifest,
    prepare_tokenplan_experiment,
    scheduler_lock,
)
from cbm_drift_v2.validation import validate_dataset


@pytest.fixture(scope="module")
def sequences() -> list[dict]:
    return read_jsonl(ROOT / "data/evidence_sequences.jsonl")


def test_frozen_dataset_independently_validates(sequences: list[dict]) -> None:
    config = read_json(ROOT / "config/experiment_config.json")
    result = validate_dataset(
        config, sequences,
        read_jsonl(ROOT / "data/protocol_request_plan.jsonl"),
        read_jsonl(ROOT / "data/mad_request_plan.jsonl"),
    )
    assert result["passed"], result["errors"]
    assert result["base_items"] == 12
    assert result["sequences"] == 36


def test_unknown_is_not_a_violation() -> None:
    rules = [{"id": "C1", "attribute": "skill", "required_value": True}]
    solved = solve_candidate_set(rules, [])
    assert solved["oracle"] == ["A", "B", "C", "D"]
    assert solved["exclusions"] == {}


def test_correction_only_supersedes_named_fact() -> None:
    events = [
        {"evidence_id": "E1", "event_type": "observation", "fact_kind": "target", "candidate_id": "A", "attribute": "x", "value": False},
        {"evidence_id": "E2", "event_type": "observation", "fact_kind": "target", "candidate_id": "B", "attribute": "x", "value": False},
        {"evidence_id": "E3", "event_type": "correction", "fact_kind": "target", "candidate_id": "A", "attribute": "x", "value": True, "supersedes_evidence_id": "E1"},
    ]
    replay = replay_evidence(events)
    assert {row["evidence_id"] for row in replay["active_evidence"]} == {"E2", "E3"}
    assert replay["superseded_evidence_ids"] == ["E1"]
    invalid = copy.deepcopy(events)
    invalid[-1]["candidate_id"] = "B"
    with pytest.raises(EvidenceReplayError):
        replay_evidence(invalid)


def test_no_future_evidence_and_clean_noise_oracles_match(sequences: list[dict]) -> None:
    grouped = {}
    for row in sequences:
        grouped.setdefault(row["family_id"], {})[row["variant_type"]] = row
        for state in row["stage_states"]:
            assert all(event["appearance_stage"] <= state["evidence_stage"] for event in state["active_evidence"])
    for variants in grouped.values():
        assert [row["oracle"] for row in variants["clean_stay"]["stage_states"]] == [
            row["oracle"] for row in variants["irrelevant_noise"]["stage_states"]
        ]


def test_parser_does_not_treat_explanation_labels_as_answer() -> None:
    names = {"A": "Alex", "B": "Blair", "C": "Casey", "D": "Drew"}
    parsed = parse_answer_set('{"answer_set":["D"],"explanation":"A and B are excluded."}', names)
    assert parsed["recognized"] and parsed["answer_set"] == ["D"]
    ambiguous = parse_answer_set(
        '{"answer_set":["A"],"explanation":"x"}\n{"answer_set":["B"],"explanation":"y"}', names
    )
    assert not ambiguous["recognized"]
    no_final = parse_answer_set("Candidate A fails, while Candidate B remains possible.", names)
    assert not no_final["recognized"]
    assert parse_answer_set("Final answer set: [Alex, D]", names)["answer_set"] == ["A", "D"]


def test_prompt_has_no_concrete_answer_set_example() -> None:
    assert not contains_concrete_answer_example()


def _output(message: str, stage: int, round_id: int, prediction: list[str], oracle: list[str]) -> dict:
    return {
        "request_id": message, "message_id": message, "variant_id": "v", "trajectory_id": "v",
        "family_id": "f", "base_item_id": "b", "variant_type": "clean_stay", "agent_id": "agent_1",
        "evidence_stage": stage, "round": round_id, "api_success": True, "recognized_answer": True,
        "predicted_candidates": prediction, "correct": prediction == oracle,
        "extra_candidates": sorted(set(prediction) - set(oracle)),
        "omitted_candidates": sorted(set(oracle) - set(prediction)), "visible_peer_message_ids": [],
    }


def test_program_events_new_persistent_corrected_and_recurrence() -> None:
    sequence = {
        "variant_id": "v", "stage_states": [
            {"oracle": ["A"], "exclusions": {"B": [{"evidence_id": "E", "rule_id": "C"}]}},
            {"oracle": ["A"], "exclusions": {"B": [{"evidence_id": "E", "rule_id": "C"}]}},
        ]
    }
    outputs = [
        _output("m1", 1, 0, ["A"], ["A"]),
        _output("m2", 1, 1, ["A", "B"], ["A"]),
        _output("m3", 1, 2, ["A", "B"], ["A"]),
        _output("m4", 2, 0, ["A"], ["A"]),
        _output("m5", 2, 1, ["A", "B"], ["A"]),
    ]
    rows = build_message_diagnostics([sequence], outputs)
    assert [row["temporal_status"] for row in rows] == [
        "correct_maintenance", "newly_introduced", "persistent", "corrected", "recurrence"
    ]
    events = build_program_events(rows)
    assert len(events) == 2
    assert {row["temporal_status_at_start"] for row in events} == {"newly_introduced", "recurrence"}


def test_judge_quote_and_peer_validation() -> None:
    package = {
        "current_message_text": "Casey is eligible.", "visible_peer_message_ids": ["p1"],
        "reference_structure": {
            "active_evidence": [{"evidence_id": "E1"}], "rules": [{"id": "C1"}]
        },
    }
    value = {
        "has_diagnostic_event": True, "temporal_status": "initial_error",
        "content_labels": ["factual_deviation"],
        "claims": [{"quote": "Casey", "start": 0, "end": 5, "stance": "asserted", "target_entity_ids": ["C"], "violated_fact_ids": ["E1"], "violated_rule_ids": ["C1"]}],
        "answer_effect": "none", "related_peer_message_ids": ["p1"], "uncertainty_reason": None,
    }
    assert validate_prediction(value, package)["schema_valid"]
    invalid = copy.deepcopy(value)
    invalid["claims"][0]["start"] = 1
    repaired = validate_prediction(invalid, package)
    assert repaired["schema_valid"]
    assert repaired["normalization_actions"]
    without_offsets = copy.deepcopy(value)
    without_offsets["claims"][0].pop("start")
    without_offsets["claims"][0].pop("end")
    derived = validate_prediction(without_offsets, package)
    assert derived["schema_valid"]
    assert derived["normalized"]["claims"][0]["start"] == 0
    assert derived["normalized"]["claims"][0]["end"] == 5
    invalid["claims"][0]["quote"] = "Casey was eligible."
    assert not validate_prediction(invalid, package)["schema_valid"]


def test_mad_dependencies_enforce_same_round_isolation() -> None:
    rows = read_jsonl(ROOT / "data/mad_request_plan.jsonl")
    for row in rows:
        if row["round"] == 0:
            assert all(f":t{row['evidence_stage']}:r0:" not in dep for dep in row["depends_on"])
        else:
            assert len(row["depends_on"]) == 3
            assert all(f":t{row['evidence_stage']}:r{row['round'] - 1}:" in dep for dep in row["depends_on"])


def test_runner_manifest_is_stable_and_sensitive_to_config(tmp_path: Path) -> None:
    config = read_json(ROOT / "config/experiment_config.json")
    runner = ExperimentRunner(ROOT, config, "protocol")
    first = runner.manifest_hash
    assert first == ExperimentRunner(ROOT, config, "protocol").manifest_hash
    changed = copy.deepcopy(config)
    changed["generation"]["temperature"] = 0.6
    with pytest.raises(RuntimeError, match="fingerprint mismatch"):
        ExperimentRunner(ROOT, changed, "protocol")


def test_no_credentials_embedded_in_config() -> None:
    raw = (ROOT / "config/experiment_config.json").read_text(encoding="utf-8")
    assert "sk-" not in raw
    config = json.loads(raw)
    assert config["judge"]["api_key_env"] == "DEEPSEEK_API_KEY"


def test_event_matching_is_one_to_one_and_category_independent() -> None:
    predictions = [
        {"trajectory_id": "t", "agent_id": "a", "message_id": "m", "content_labels": ["factual_deviation"]},
        {"trajectory_id": "t", "agent_id": "a", "message_id": "m", "content_labels": ["rule_deviation"]},
    ]
    references = [
        {"trajectory_id": "t", "agent_id": "a", "event_start_message_id": "m", "content_labels": ["rule_deviation"]}
    ]
    result = evaluate_events(predictions, references)
    assert result["matched"] == 1
    assert result["unmatched_predictions"] == 1
    assert result["precision"] == 0.5
    assert result["recall"] == 1.0


def test_tokenplan_pairing_is_balanced_and_outcome_independent() -> None:
    packages = read_jsonl(ROOT / "results/judge/judge_input_packages.jsonl")
    paired = build_paired_manifest(packages, 20260928)
    assert len(paired) == 180
    assert len({(row["base_item_id"], row["variant_id"], row["evidence_stage"]) for row in paired}) == 180
    assert {row["round"] for row in paired} == {0, 1, 2}
    assert {sum(row["round"] == value for row in paired) for value in (0, 1, 2)} == {60}
    assert {sum(row["agent_id"] == value for row in paired) for value in ("agent_1", "agent_2", "agent_3")} == {60}
    assert all("outcome" not in row and "correct" not in row for row in paired)


def test_tokenplan_preflight_and_queue_cover_expected_protocols() -> None:
    packages = read_jsonl(ROOT / "results/judge/judge_input_packages.jsonl")
    paired = build_paired_manifest(packages, 20260928)
    preflight = build_preflight_manifest(paired, packages, 20260928)
    assert len(preflight) == 12
    assert {row["variant_id"].split("::")[-1] for row in preflight} == {
        "clean_stay", "evidence_update", "irrelevant_noise"
    }
    assert {row["evidence_stage"] for row in preflight} == {1, 2, 3, 4, 5}
    assert {row["round"] for row in preflight} == {0, 1, 2}
    assert {row["agent_id"] for row in preflight} == {"agent_1", "agent_2", "agent_3"}
    assert {row["context_length_band"] for row in preflight} == {"short", "medium", "long"}

    config = read_json(ROOT / "config/tokenplan_deepseek_v4_pro.json")
    manifest = prepare_tokenplan_experiment(ROOT, config)
    assert manifest["inventory"] == {
        "packages": 1620,
        "paired_messages": 180,
        "preflight_messages": 12,
        "structured_requests": 1620,
        "direct_requests": 180,
        "total_requests": 1800,
    }


def test_tokenplan_config_has_no_secret_and_fixes_judge_protocol() -> None:
    path = ROOT / "config/tokenplan_deepseek_v4_pro.json"
    raw = path.read_text(encoding="utf-8")
    config = json.loads(raw)
    assert "user_" not in raw and "sk-" not in raw
    assert config["api_key_env"] == "TOKENPLAN_API_KEY"
    assert config["model_name"] == "deepseek/deepseek-v4-pro"
    assert config["thinking"] == {"type": "enabled"}
    assert config["reasoning_effort"] == "low"
    assert config["max_tokens"] == 16384
    assert "temperature" not in config and "top_p" not in config


def test_only_infrastructure_failures_are_retryable() -> None:
    assert _retryable_record({
        "api_success": False,
        "terminal_reason": "infrastructure_error",
        "retryable_after_run": True,
        "attempts": [],
    })
    assert not _retryable_record({
        "api_success": True,
        "finish_reason": "length",
        "retryable_after_run": False,
        "attempts": [],
    })
    assert not _retryable_record({
        "api_success": False,
        "terminal_reason": "authentication_or_permission_error",
        "retryable_after_run": False,
        "attempts": [],
    })


def test_tokenplan_transport_does_not_follow_redirects(monkeypatch: pytest.MonkeyPatch) -> None:
    """A gateway redirect must remain an auditable POST failure, never become a GET."""
    monkeypatch.setenv("TOKENPLAN_API_KEY", "test-only-placeholder")
    config = read_json(ROOT / "config/tokenplan_deepseek_v4_pro.json")
    runner = TokenPlanJudgeRunner(ROOT, config)
    try:
        assert runner.client.follow_redirects is False
        assert TRANSPORT_VERSION.endswith("httpx-sse")
    finally:
        runner.client.close()


def test_tokenplan_sse_aggregates_reasoning_final_json_and_usage() -> None:
    accumulator = _new_stream_accumulator()
    lines = [
        'data: {"id":"r1","model":"deepseek/deepseek-v4-pro","choices":[{"delta":{"reasoning":"check "},"finish_reason":null}]}',
        'data: {"id":"r1","model":"deepseek/deepseek-v4-pro","choices":[{"delta":{"content":"{\\"has_diagnostic_event\\":false}"},"finish_reason":"stop"}]}',
        'data: {"id":"r1","model":"deepseek/deepseek-v4-pro","choices":[],"usage":{"prompt_tokens":10,"completion_tokens":5}}',
        "data: [DONE]",
    ]
    for line in lines:
        _consume_sse_line(accumulator, line)
    body = _stream_body(accumulator)
    assert body["choices"][0]["message"]["reasoning_content"] == "check "
    assert body["choices"][0]["message"]["content"] == '{"has_diagnostic_event":false}'
    assert body["choices"][0]["finish_reason"] == "stop"
    assert body["usage"]["prompt_tokens"] == 10
    assert accumulator["done_received"]
    assert accumulator["delta_key_counts"] == {"reasoning": 1, "content": 1}


def test_tokenplan_scheduler_recovers_stale_lock_and_rejects_live_lock(tmp_path: Path) -> None:
    lock = tmp_path / "scheduler.lock"
    lock.write_text('{"pid": 999999999, "started_at": "old"}', encoding="utf-8")
    with scheduler_lock(lock):
        assert lock.exists()
        with pytest.raises(RuntimeError, match="already locked"):
            with scheduler_lock(lock):
                pass
    assert lock.exists()
