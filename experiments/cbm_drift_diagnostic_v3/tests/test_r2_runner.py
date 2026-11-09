"""Mock-only full DAG, restart, checkpoint and visibility checks."""

import copy
import json
from pathlib import Path
import pytest

from cbm_drift_v3.runner import run_requests, run_protocol, build_messages
from cbm_drift_v3.common import read_json, sha256_json
from cbm_drift_v3.runtime import RuntimeBlocked
from cbm_drift_v3.diagnostics import analyze_program


class FakeClient:
    def __init__(self, malformed=False):
        self.calls = []
        self.malformed = malformed

    def count_tokens(self, messages):
        return 100

    def __call__(self, payload):
        self.calls.append(copy.deepcopy(payload))
        raw = "NOT JSON" if self.malformed else json.dumps({"answer_set": list("ABCD"), "explanation": f"synthetic-response-{len(self.calls)}"})
        return {"model": "Qwen3-8B", "choices": [{"message": {"content": raw}, "finish_reason": "stop"}], "usage": {"total_tokens": 120}}


def test_full1188_mock_preflight_and_resume(config, sequences, plans, tmp_path):
    client = FakeClient()
    plan = plans[0]
    first = run_requests(config, plan, sequences, tmp_path, preflight=True, client=client, allow_mock=True)
    assert first["api_success"] == len(client.calls) == 198
    full = run_requests(config, plan, sequences, tmp_path, resume=True, client=client, allow_mock=True)
    assert full["api_success"] == len(client.calls) == 1188
    assert full["complete_branch_views"] == 48 and full["status"] == "software_test_only"
    assert len(list((tmp_path / "checkpoints").glob("*.json"))) == 12
    records = {r["message_id"]: r for r in (read_json(p) for p in (tmp_path / "records").glob("*.json"))}
    lookup = {(r["family_id"], r["branch_type"], r["evidence_stage"], r["round"], r["agent_id"]): r for r in plan}
    for family in sorted({r["family_id"] for r in plan}):
        for agent in ("agent_1", "agent_2", "agent_3"):
            prefix = lookup[family, None, 3, 2, agent]
            parent = records[prefix["message_id"]]
            suffixes = [records[lookup[family, branch, 4, 0, agent]["message_id"]] for branch in ("clean", "update", "noise", "update_noise")]
            assert all(r["messages"][:-1] == parent["messages"] + [{"role": "assistant", "content": parent["raw_response"]}] for r in suffixes)
            assert len({r["seed"] for r in suffixes}) == 1
    run_requests(config, plan, sequences, tmp_path, resume=True, client=client, allow_mock=True)
    assert len(client.calls) == 1188
    assert all(r["is_mock"] for r in records.values())


def test_resume_fingerprint_rejects_changed_config(config, sequences, plans, tmp_path):
    client = FakeClient()
    subset = plans[0][:3]
    run_requests(config, subset, sequences, tmp_path, client=client, allow_mock=True)
    changed = copy.deepcopy(config)
    changed["generation"]["temperature"] = 0.9
    with pytest.raises(ValueError, match="Frozen"):
        run_requests(changed, subset, sequences, tmp_path, resume=True, client=client, allow_mock=True)


def test_malformed_response_not_resampled_and_remains_visible(config, sequences, plans, tmp_path):
    client = FakeClient(malformed=True)
    subset = plans[0][:6]
    result = run_requests(config, subset, sequences, tmp_path, client=client, allow_mock=True)
    assert result["api_success"] == 6 and result["parsed"] == 0
    assert len(client.calls) == 6
    assert any(m["role"] == "assistant" and m["content"] == "NOT JSON" for m in client.calls[-1]["messages"])


def test_failed_parent_blocks_history_not_empty(config, sequences, plans, tmp_path):
    class Broken(FakeClient):
        def __call__(self, payload):
            self.calls.append(payload)
            raise ConnectionError("test transient")
    client = Broken()
    result = run_requests(config, plans[0][:9], sequences, tmp_path, client=client, allow_mock=True)
    assert result["failed"] == 3 and result["blocked"] == 6
    assert len(client.calls) == 9


def test_interrupted_attempt_resume_uses_remaining_budget(config, sequences, plans, tmp_path):
    class Interrupted(FakeClient):
        def __call__(self, payload):
            raise KeyboardInterrupt()
    with pytest.raises(KeyboardInterrupt):
        run_requests(config, plans[0][:3], sequences, tmp_path, client=Interrupted(), allow_mock=True)
    client = FakeClient()
    result = run_requests(config, plans[0][:3], sequences, tmp_path, resume=True, client=client, allow_mock=True)
    assert result["api_success"] == 3 and result["attempts"] == 4


def test_context_excess_not_silently_truncated(config, sequences, plans, tmp_path):
    class Long(FakeClient):
        def count_tokens(self, messages):
            return 16384
    client = Long()
    result = run_requests(config, plans[0][:3], sequences, tmp_path, client=client, allow_mock=True)
    assert result["blocked"] == 3 and len(client.calls) == 0


def test_no_injected_client_without_mock_gate(config, sequences, plans, tmp_path):
    with pytest.raises(ValueError, match="allow_mock"):
        run_requests(config, plans[0], sequences, tmp_path, client=FakeClient())


def test_protocol108_separate_mock(config, sequences, plans, tmp_path):
    client = FakeClient()
    result = run_protocol(config, plans[2], sequences, tmp_path, client=client, allow_mock=True)
    assert result["api_success"] == len(client.calls) == 108
    assert all(len(call["messages"]) == 2 for call in client.calls)


def test_mock_records_cannot_be_real_program_results(config, sequences, plans, tmp_path):
    fake = {**plans[0][0], "api_success": True, "raw_response": '{"answer_set":[],"explanation":"mock"}', "is_mock": True}
    with pytest.raises(ValueError, match="mock"):
        analyze_program(plans[0], sequences, [fake], tmp_path)
