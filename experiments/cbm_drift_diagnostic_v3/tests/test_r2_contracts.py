"""State, graph, case-reference, evaluator and credential regression tests."""

import copy
import json
import pytest

from cbm_drift_v3.common import sha256_json, read_jsonl, read_json
from cbm_drift_v3.state import replay_evidence, score_answer, EvidenceReplayError
from cbm_drift_v3.validation import validate_dataset
from cbm_drift_v3.controlled_cases import validate_controlled, inspect_message, temporal_from_history
from cbm_drift_v3.judge import render_package, prepare_controlled_judge, credential_gate, validate_prediction
from cbm_drift_v3.evaluation import prf, evaluate_events, evaluate_controlled, match_claims
from cbm_drift_v3.annotation import prepare_deferred_real, flatten_annotation
from cbm_drift_v3.parsing import parse_answer_set
from cbm_drift_v3.runtime import inspect_gpu_csv, GPU_UUID


def test_exact_counts_and_source_preservation(source, sequences, plans):
    plan, views, protocol = plans
    report = validate_dataset(sequences, plan, views, source)
    assert report["status"] == "passed", report
    assert len(protocol) == 108
    assert len({r["message_id"] for r in plan}) == 1188
    assert sum(r["phase"] == "shared_prefix" for r in plan) == 324


@pytest.mark.parametrize("mutation", ["peer", "parent", "barrier", "state", "noise"])
def test_graph_and_state_tampering_rejected(source, sequences, plans, mutation):
    seqs, plan = copy.deepcopy(sequences), copy.deepcopy(plans[0])
    target = next(r for r in plan if r["evidence_stage"] == 4 and r["round"] == 0)
    if mutation == "peer":
        target["visible_peer_message_ids"] = target["barrier_message_ids"]
    elif mutation == "parent":
        target["own_previous_message_id"] = plan[-1]["message_id"]
    elif mutation == "barrier":
        target["barrier_message_ids"] = []
    elif mutation == "state":
        seqs[0]["stage_states"][0]["oracle"] = []
    else:
        combined = next(s for s in seqs if s["branch_type"] == "update_noise")
        combined["stages"][3]["events"] = []
    assert validate_dataset(seqs, plan, plans[1], source)["status"] == "failed"


def test_open_world_update_regression():
    rules = [{"id": "C1", "attribute": "programming", "required_value": True}]
    facts = [{"evidence_id": c, "candidate_id": c, "attribute": "programming", "value": c == "A", "event_type": "observation", "fact_kind": "target"} for c in "ABCD"]
    old = replay_evidence(facts)
    assert score_answer(rules, old["active_evidence"], ["A"])["oracle"] == ["A"]
    updated = replay_evidence(facts + [{**facts[1], "evidence_id": "B_new", "value": True, "event_type": "correction", "supersedes_evidence_id": "B"}])
    score = score_answer(rules, updated["active_evidence"], ["A"])
    assert score["oracle"] == ["A", "B"] and score["omitted"] == ["B"]
    assert score_answer(rules, [], list("ABCD"))["answer_status"] == "correct"
    assert score_answer(rules, [], None)["answer_status"] == "unrecognized"


def test_inactive_restatement_rejected():
    fact = {"evidence_id": "e1", "candidate_id": "A", "attribute": "x", "value": False, "event_type": "observation", "fact_kind": "target"}
    correction = {**fact, "evidence_id": "e2", "value": True, "event_type": "correction", "supersedes_evidence_id": "e1"}
    with pytest.raises(EvidenceReplayError):
        replay_evidence([fact, correction, {**fact, "evidence_id": "e3", "event_type": "restatement", "restates_evidence_id": "e1"}])


def test_controlled72_coverage(controlled):
    cases, refs, report = controlled
    assert report["status"] == "passed" and report["verified"] == 72
    assert report["human_verified"] == 0
    assert all(r["history_source"] == "scripted" for r in refs)
    assert not (set(report["coverage"]["dev"]["families"]) & set(report["coverage"]["holdout"]["families"]))


@pytest.mark.parametrize("stratum", ["known_fact_contradiction", "unsupported_assertion", "rule_change", "inference_error", "quoted_then_rejected", "hypothetical_only", "reasonable_update", "correct_answer_wrong_basis", "correct_answer_stale_basis", "wrong_answer_unresolved", "correct_maintenance", "multi_claim"])
def test_independent_restricted_language_interpretation(controlled, stratum):
    cases, refs, _ = controlled
    by_id = {c["case_id"]: c for c in cases}
    for ref in (r for r in refs if r["primary_stratum"] == stratum):
        result = inspect_message(by_id[ref["case_id"]], by_id[ref["case_id"]]["target_message"])
        assert result["content_labels"] == ref["expected_content_labels"]
        assert result["current_deviation"] == ref["expected_current_deviation"]
        assert temporal_from_history(by_id[ref["case_id"]], ref["temporal_object"]) == ref["expected_temporal_status"]


def test_ref_labels_not_trusted(controlled):
    cases, refs, _ = controlled
    refs = copy.deepcopy(refs)
    refs[0]["expected_content_labels"] = ["R"]
    refs[0]["reference_sha256"] = sha256_json({k: v for k, v in refs[0].items() if k != "reference_sha256"})
    result = validate_controlled(cases, refs)
    assert any("independent content_labels" in e for e in result["errors"])


def test_missing_history_not_initial(controlled):
    cases, refs, _ = controlled
    by_id = {c["case_id"]: c for c in cases}
    ref = next(r for r in refs if r["expected_temporal_status"] == "newly_introduced")
    case = copy.deepcopy(by_id[ref["case_id"]])
    case["history"] = []
    case["history_scope"]["complete"] = False
    assert temporal_from_history(case, ref["temporal_object"]) == "uncertain"


def test_judge_queue_no_reference_leak(controlled, judge_config, tmp_path):
    cases, _, _ = controlled
    result = prepare_controlled_judge(cases, judge_config, tmp_path)
    queue = read_jsonl(tmp_path / "request_queue.jsonl")
    assert result["formal_unique_requests"] == len({r["request_id"] for r in queue}) == 144
    assert sum(r["preflight"] for r in queue) == 12
    for row in read_jsonl(tmp_path / "input_packages.jsonl"):
        payload = json.dumps(row["messages"])
        assert all(k not in payload for k in ("expected_content_labels", "primary_stratum", '"split"', "mutation_type", '"case_sha256"'))
    direct = render_package(cases[0], "direct")
    structured = render_package(cases[0], "structured")
    assert {k: v for k, v in structured.items() if k != "reference_structure_assistance"} == direct
    assert "temporal_status" not in structured["reference_structure_assistance"]


def test_judge_gate_new_local_only(judge_config, monkeypatch):
    monkeypatch.delenv("JUDGE_API_KEY_V3_NEW", raising=False)
    monkeypatch.setenv("TOKENPLAN_API_KEY", "test-old-not-a-real-credential")
    assert credential_gate(judge_config, enabled=True)["status"] == "not_run_missing_new_credentials"
    monkeypatch.setenv("JUDGE_API_KEY_V3_NEW", "test-new-not-a-real-credential")
    assert credential_gate(judge_config, enabled=False)["status"] == "not_run_not_enabled"
    assert credential_gate(judge_config, enabled=True)["status"] == "blocked_unverified_requested_model"


def test_wrong_object_never_scores_strict_tp():
    ref = {"case_id": "c", "message_id": "m", "agent_id": "a", "evidence_stage": 1, "round": 0,
           "candidate_ids": ["C"], "attribute": "x", "rule_ids": [], "quote": "C is true", "start": 0, "end": 9,
           "conflicting_evidence_ids": ["fact_C"], "evidence_version": "fact_C", "content_labels": ["F"], "stance": "asserted"}
    pred = {**ref, "candidate_ids": ["B"], "conflicting_evidence_ids": ["fact_B"], "evidence_version": "fact_B"}
    metrics = evaluate_events([pred], [ref])
    assert metrics["strict_localization"]["tp"] == 0
    assert metrics["strict_localization"]["fn"] == 1
    assert metrics["classification"]["F"]["f1"] == 0
    assert match_claims([{**ref, "content_labels": ["R"]}], [ref]) == [(0, 0)]


def test_f1_and_failure_denominators(controlled):
    assert prf(0, 0, 3)["f1"] == 0
    assert prf(0, 0, 0)["f1"] is None
    _, refs, _ = controlled
    outputs = [{"case_id": r["case_id"], "protocol": p, "status": "api_failure", "api_success": False} for r in refs for p in ("direct", "structured")]
    result = evaluate_controlled(outputs, refs)
    for split in ("dev", "holdout"):
        score = result["splits"][split]["direct"]
        assert score["current_deviation"]["recall"] == 0
        assert score["negative"]["end_to_end_correct_rejection_rate"] == 0
        assert score["negative"]["false_positive_rate_on_judged"] is None


def test_no_online_scores_without_predictions(controlled):
    assert evaluate_controlled([], controlled[1])["status"] == "not_evaluated"
    mock = [{"is_mock": True}]
    assert evaluate_controlled(mock, controlled[1])["status"] == "not_evaluated"


def test_deferred132_templates(plans, sequences, tmp_path):
    result = prepare_deferred_real(plans[0], sequences, [], tmp_path)
    rows = read_jsonl(tmp_path / "sampling_manifest.jsonl")
    assert result["planned_unique_messages"] == len({r["message_id"] for r in rows}) == 132
    assert result["available_messages"] == 0 and result["online_enabled"] is False
    flat = flatten_annotation(read_jsonl(tmp_path / "annotator_1_template.jsonl"), {r["message_id"] for r in rows})
    assert len(flat) == 132 and all(r["reference_kind"] == "unannotated" for r in flat)
    assert "oracle" not in (tmp_path / "blind_annotation.html").read_text()


@pytest.mark.parametrize("raw,recognized,strict", [
    ('{"answer_set":["A"],"explanation":"B is invalid"}', True, True),
    ('{"answer_set":["A"]}', True, False),
    ('prefix {"answer_set":["A"],"explanation":"ok"}', True, False),
    ('{"answer_set":["A"]}\nFinal answer: [B]', False, False),
    ('Candidate A is discussed first.', False, False),
    ('{"answer_set":[],"explanation":"none"}', True, True),
    ('{"answer_set":["A","A"]}', False, False)])
def test_conservative_parser(raw, recognized, strict):
    result = parse_answer_set(raw, {})
    assert result["recognized"] == recognized
    assert result["strict_json"] == strict


def test_gpu4_occupied_refuses_and_does_not_fallback(config):
    gpu = f"4,{GPU_UUID},NVIDIA GeForce RTX 4090,0000:88:00.0,24564,2500"
    result = inspect_gpu_csv(config, gpu, f"123,{GPU_UUID},other_python,2450")
    assert result["status"] == "blocked" and result["reason"] == "gpu_occupied"
    assert inspect_gpu_csv(config, gpu.replace("4,", "5,", 1), "")["allowed"] is False


def _example_prediction(controlled):
    cases, refs, _ = controlled
    ref = next(r for r in refs if r["primary_stratum"] == "known_fact_contradiction" and r["expected_temporal_status"] == "newly_introduced")
    case = next(c for c in cases if c["case_id"] == ref["case_id"])
    prediction = {key: ref["expected_" + key] for key in ("current_deviation", "answer_status", "content_labels", "temporal_status", "update_response")}
    prediction["uncertainty_reason"] = None
    prediction["claims"] = copy.deepcopy(ref["claims"])
    for claim in prediction["claims"]:
        claim["cited_evidence_ids"] = []
    return prediction, render_package(case, "direct")


@pytest.mark.parametrize("mutation", ["offset", "evidence", "history_offset", "version", "wrong_candidate"])
def test_prediction_quote_id_version_validation(controlled, mutation):
    prediction, package = _example_prediction(controlled)
    baseline = validate_prediction(prediction, package)
    assert all(baseline[k] for k in ("schema_valid", "quote_valid", "object_valid", "formal_valid"))
    claim = prediction["claims"][0]
    if mutation == "offset":
        claim["start"] += 1
    elif mutation == "evidence":
        claim["conflicting_evidence_ids"] = ["missing_id"]
    elif mutation == "history_offset":
        claim["prior_support"][0]["start"] += 1
    elif mutation == "version":
        claim["evidence_version"] = "not_a_version"
    else:
        claim["candidate_ids"] = [next(c for c in "ABCD" if c != claim["candidate_ids"][0])]
    result = validate_prediction(prediction, package)
    assert not all(result[k] for k in ("quote_valid", "object_valid", "formal_valid"))


def test_malformed_schema_is_recordable(controlled):
    prediction, package = _example_prediction(controlled)
    prediction.update(current_deviation=[], temporal_status={})
    prediction["claims"][0].update(attribute={}, stance=[], temporal_status=[])
    result = validate_prediction(prediction, package)
    assert result["schema_valid"] is False and result["object_valid"] is False


def test_numeric_evidence_version_requires_unique_explicit_reference(controlled):
    prediction, package = _example_prediction(controlled)
    claim = prediction["claims"][0]
    original_id = claim["evidence_version"]
    evidence = next(e for e in package["evidence"] if e["evidence_id"] == original_id)
    claim["evidence_version"] = evidence["version"]
    result = validate_prediction(prediction, package)
    assert result["object_valid"] and result["formal_valid"]
    normalized = result["prediction"]["claims"][0]
    assert normalized["evidence_version"] == original_id
    assert normalized["raw_evidence_version"] == evidence["version"]
    assert claim["evidence_version"] == evidence["version"]
    claim["conflicting_evidence_ids"] = []
    assert not validate_prediction(prediction, package)["object_valid"]


def test_numeric_evidence_version_rejects_ambiguity_and_bool(controlled):
    prediction, package = _example_prediction(controlled)
    claim = prediction["claims"][0]
    claim.update(attribute=None, candidate_ids=[], conflicting_evidence_ids=[], evidence_version=1,
                 cited_evidence_ids=[e["evidence_id"] for e in package["evidence"] if e["version"] == 1])
    assert not validate_prediction(prediction, package)["object_valid"]
    claim["evidence_version"] = True
    assert not validate_prediction(prediction, package)["object_valid"]


def test_same_message_wrong_object_and_missing_message_denominator():
    ref = {"case_id": "c", "message_id": "m", "candidate_ids": ["C"], "attribute": "x", "rule_ids": [], "quote": "claim", "start": 0, "end": 5, "stance": "asserted", "content_labels": ["F"]}
    second = {**ref, "case_id": "c2", "message_id": "m2"}
    result = evaluate_events([ref], [ref, second])
    assert result["strict_localization"]["recall"] == 0.5
