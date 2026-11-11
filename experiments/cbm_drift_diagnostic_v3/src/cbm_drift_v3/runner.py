"""Explicit-history MAD DAG execution with immutable inputs and finite attempts."""

from __future__ import annotations

import copy
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

from .common import (AGENTS, freeze_json, read_json, read_jsonl, sha256_file,
                     sha256_json, write_json, write_jsonl)
from .parsing import parse_answer_set
from .prompts import TASK_SYSTEM_PROMPT, MAD_REVISION_PROMPT, peer_block, stage_user_message, snapshot_user_message
from .runtime import RuntimeBlocked, model_files, verify_service


def code_fingerprint() -> dict[str, str]:
    """Pin local implementation rather than relying on an uncommitted base SHA."""
    names = {"common.py", "state.py", "prompts.py", "parsing.py", "prepare.py", "validation.py", "runtime.py", "runner.py"}
    return {p.name: sha256_file(p) for p in sorted(Path(__file__).parent.glob("*.py")) if p.name in names}


def build_messages(request: dict[str, Any], sequence: dict[str, Any], completed: dict[str, Any]) -> list[dict[str, str]]:
    """Consume the explicit parent list; barriers alone never expose peer text."""
    if any(mid not in completed or not completed[mid]["api_success"] for mid in request["depends_on"]):
        raise RuntimeBlocked("missing_or_failed_parent")
    previous = request["own_previous_message_id"]
    messages = copy.deepcopy(completed[previous]["messages"]) + [{"role": "assistant", "content": completed[previous]["raw_response"]}] if previous else [{"role": "system", "content": TASK_SYSTEM_PROMPT}]
    if request["round"] == 0:
        content = stage_user_message(sequence, request["evidence_stage"], include_task=previous is None)
    else:
        peers = [completed[mid] for mid in request["visible_peer_message_ids"]]
        content = MAD_REVISION_PROMPT.format(peer_block=peer_block(peers))
    messages.append({"role": "user", "content": content})
    return messages


class LocalClient:
    """OpenAI-compatible local service with the exact local chat tokenizer."""

    def __init__(self, config: dict[str, Any]):
        verify_service(config)
        from transformers import AutoTokenizer
        self.config = config
        self.tokenizer = AutoTokenizer.from_pretrained(config["model"]["weights_path"], local_files_only=True)

    def count_tokens(self, messages: list[dict[str, str]]) -> int:
        """Count with the non-thinking chat template, including generation prefix."""
        ids = self.tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True,
                                                enable_thinking=False, return_dict=False)
        if not isinstance(ids, list) or any(type(token) is not int for token in ids):
            raise ValueError("Tokenizer must return one flat list of token IDs")
        return len(ids)

    def __call__(self, payload: dict[str, Any]) -> dict[str, Any]:
        verify_service(self.config)
        model = self.config["model"]
        request = urllib.request.Request(model["base_url"].rstrip("/") + "/chat/completions",
                                         json.dumps(payload).encode(),
                                         {"Content-Type": "application/json", "Authorization": "Bearer " + model.get("api_key", "EMPTY")})
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(request, timeout=self.config["generation"]["request_timeout_seconds"]) as response:
            return json.load(response)


def _payload(config: dict[str, Any], request: dict[str, Any], messages: list[dict[str, str]]) -> dict[str, Any]:
    return {"model": config["model"]["model_name"], "messages": messages, "seed": request["seed"],
            **{k: config["generation"][k] for k in ("temperature", "top_p", "max_tokens")},
            **config["model"].get("extra_body", {})}


def _summary(plan: list[dict[str, Any]], completed: dict[str, Any], attempts: list[dict[str, Any]], blocked: list[dict[str, Any]], is_mock: bool) -> dict[str, Any]:
    selected = {p["request_id"] for p in plan}
    records = [r for mid, r in completed.items() if mid in selected]
    succeeded = [r for r in records if r["api_success"]]
    return {"status": "software_test_only" if is_mock else "completed" if len(succeeded) == len(plan) else "blocked" if blocked and not attempts else "partial",
            "planned": len(plan), "attempted": len({a["request_id"] for a in attempts if a["request_id"] in selected}),
            "attempts": sum(a["request_id"] in selected for a in attempts), "api_success": len(succeeded),
            "parsed": sum(r["parsed"]["recognized"] for r in succeeded),
            "failed": sum(not r["api_success"] for r in records), "blocked": len(blocked),
            "truncated": sum(r.get("finish_reason") == "length" for r in succeeded), "is_mock": is_mock}


def _run(config: dict[str, Any], plan: list[dict[str, Any]], sequences: list[dict[str, Any]], output_dir: Path,
         *, resume: bool, client: Any, allow_mock: bool, static: bool, full_plan: list[dict[str, Any]]) -> dict[str, Any]:
    mock = client is not None
    if mock and not allow_mock:
        raise ValueError("Injected client requires explicit allow_mock; not an online result")
    output_dir.mkdir(parents=True, exist_ok=True)
    seqs = {s["sequence_id"]: s for s in sequences}
    run_fingerprint = {"run_id": config["run_id"], "config": sha256_json(config), "code": code_fingerprint(),
                       "data": sha256_json(sequences), "plan": sha256_json(full_plan),
                       "is_mock": mock, "protocol": "snapshot" if static else "mad"}
    freeze_json(output_dir / "execution_manifest.json", run_fingerprint)
    attempts_path = output_dir / "attempts.jsonl"
    attempts = read_jsonl(attempts_path) if attempts_path.exists() else []
    completed = {}
    for path in (output_dir / "records").glob("*.json"):
        record = read_json(path)
        if not resume:
            raise ValueError("Existing records require explicit --resume")
        if record["run_fingerprint"] != sha256_json(run_fingerprint):
            raise ValueError("Record run/code/config/data fingerprint mismatch")
        if record["request_id"] in completed:
            raise ValueError("Duplicate canonical response")
        if record["request_id"] not in {r["request_id"] for r in full_plan}:
            raise ValueError("Unknown request record")
        completed[record["request_id"]] = record
    try:
        if client is None:
            client = LocalClient(config)
            freeze_json(output_dir / "model_file_fingerprints.json", model_files(config))
    except (RuntimeBlocked, ImportError, OSError, ValueError) as exc:
        blocked = [{"request_id": r["request_id"], "status": "blocked", "reason": str(exc)} for r in plan if r["request_id"] not in completed]
        write_jsonl(output_dir / "blocked.jsonl", blocked)
        summary = _summary(plan, completed, attempts, blocked, mock)
        summary["reason"] = str(exc)
        write_json(output_dir / "status.json", summary)
        return summary
    blocked = []
    for req in plan:
        rid = req["request_id"]
        sequence = seqs[req["sequence_id"]]
        try:
            if not static and req["evidence_stage"] == 4 and req["round"] == 0:
                group = [r for r in full_plan if r["family_id"] == req["family_id"] and r["evidence_stage"] == 3 and r["round"] == 2]
                if len(group) != 3 or not all(r["message_id"] in completed and completed[r["message_id"]]["api_success"] for r in group):
                    raise RuntimeBlocked("checkpoint_barrier_incomplete")
                histories = {r["agent_id"]: {"parent_message_id": r["message_id"],
                             "messages": copy.deepcopy(completed[r["message_id"]]["messages"]) + [{"role": "assistant", "content": completed[r["message_id"]]["raw_response"]}]}
                             for r in group}
                checkpoint_state = sequence["stage_states"][2]
                freeze_json(output_dir / "checkpoints" / (sha256_json(req["checkpoint_id"]) + ".json"),
                            {"checkpoint_id": req["checkpoint_id"], "histories": histories, "histories_sha256": sha256_json(histories),
                             "state": checkpoint_state, "state_sha256": sha256_json(checkpoint_state), "run_fingerprint": sha256_json(run_fingerprint)})
            messages = ([{"role": "system", "content": TASK_SYSTEM_PROMPT}, {"role": "user", "content": snapshot_user_message(sequence, req["evidence_stage"])}]
                        if static else build_messages(req, sequence, completed))
            if not static and req["evidence_stage"] == 4 and req["round"] == 0:
                checkpoint = read_json(output_dir / "checkpoints" / (sha256_json(req["checkpoint_id"]) + ".json"))
                if messages[:-1] != checkpoint["histories"][req["agent_id"]]["messages"]:
                    raise ValueError("Fork does not preserve checkpoint history")
        except RuntimeBlocked as exc:
            blocked.append({"request_id": rid, "status": "blocked", "reason": str(exc)})
            continue
        state = sequence["stage_states"][req["evidence_stage"] - 1]
        payload = _payload(config, req, messages)
        parent_hashes = {mid: sha256_json(completed[mid]["raw_response"]) for mid in req.get("depends_on", [])}
        fingerprint = sha256_json({"payload": payload, "state": state, "parents": parent_hashes, "run": run_fingerprint})
        if rid in completed:
            if completed[rid]["request_sha256"] != fingerprint:
                raise ValueError("History/model/state fingerprint mismatch on resume")
            if completed[rid]["api_success"]:
                continue
        tokens = client.count_tokens(messages)
        if tokens + config["generation"]["max_tokens"] > config["model"]["deployment"]["max_model_len"]:
            blocked.append({"request_id": rid, "status": "blocked", "reason": "context_limit_no_truncation", "input_tokens": tokens})
            continue
        limit = 1 + config["generation"]["max_retries"]
        used = sum(a["request_id"] == rid for a in attempts)
        if used >= limit:
            continue
        while used < limit:
            used += 1
            attempt = {"request_id": rid, "attempt_number": used, "request_sha256": fingerprint,
                       "started_at_unix": time.time(), "status": "started", "is_mock": mock}
            attempts.append(attempt)
            write_jsonl(attempts_path, attempts)
            started = time.monotonic()
            response = None
            error = None
            retryable = False
            try:
                response = client(payload)
                choice = response["choices"][0]
                content = choice["message"].get("content")
                if not isinstance(content, str):
                    content = ""
                if response.get("model", config["model"]["model_name"]) != config["model"]["model_name"]:
                    raise ValueError("response_model_mismatch")
            except urllib.error.HTTPError as exc:
                error, retryable = f"HTTP {exc.code}", exc.code in {408, 429, 500, 502, 503, 504}
            except (TimeoutError, ConnectionError, urllib.error.URLError) as exc:
                error, retryable = type(exc).__name__, True
            except (ValueError, KeyError, IndexError, RuntimeBlocked) as exc:
                error = str(exc)
            success = error is None
            attempt.update(status="api_success" if success else "api_failure", error=error, latency_seconds=time.monotonic() - started)
            write_jsonl(attempts_path, attempts)
            record = {**req, "message_id": req.get("message_id", rid), "run_fingerprint": sha256_json(run_fingerprint),
                      "request_sha256": fingerprint, "messages_sha256": sha256_json(messages), "state_sha256": sha256_json(state),
                      "parent_response_hashes": parent_hashes, "messages": messages, "input_tokens_counted": tokens,
                      "raw_response": content if success else None, "response": response, "api_success": success,
                      "status": "success" if success else "api_failure", "request_error": error,
                      "finish_reason": choice.get("finish_reason") if success else None,
                      "usage": response.get("usage") if success else None,
                      "actual_generation_parameters": {k: v for k, v in payload.items() if k != "messages"},
                      "attempt_count": used, "is_mock": mock}
            record["parsed"] = parse_answer_set(record["raw_response"] or "", {c: v["name"] for c, v in sequence["candidate_map"].items()})
            write_json(output_dir / "records" / (sha256_json(rid) + ".json"), record)
            completed[rid] = record
            if success or not retryable:
                break
            if used < limit:
                time.sleep(0 if mock else config["generation"]["retry_sleep_seconds"])
        if not static and req["evidence_stage"] == 3 and req["round"] == 2:
            group = [r for r in plan if r["family_id"] == req["family_id"] and r["evidence_stage"] == 3 and r["round"] == 2]
            if len(group) == 3 and all(r["message_id"] in completed and completed[r["message_id"]]["api_success"] for r in group):
                histories = {r["agent_id"]: {"parent_message_id": r["message_id"],
                              "messages": copy.deepcopy(completed[r["message_id"]]["messages"]) + [{"role": "assistant", "content": completed[r["message_id"]]["raw_response"]}]}
                             for r in group}
                freeze_json(output_dir / "checkpoints" / (sha256_json(req["checkpoint_id"]) + ".json"),
                            {"checkpoint_id": req["checkpoint_id"], "histories": histories, "histories_sha256": sha256_json(histories),
                             "state": state, "state_sha256": sha256_json(state), "run_fingerprint": sha256_json(run_fingerprint)})
    write_jsonl(output_dir / "blocked.jsonl", blocked)
    summary = _summary(plan, completed, attempts, blocked, mock)
    if not static:
        summary["complete_branch_views"] = sum(all(r["request_id"] in completed and completed[r["request_id"]]["api_success"] for r in plan
                                                   if r["family_id"] == family and r["branch_type"] in {None, branch})
                                             for family in {r["family_id"] for r in plan} for branch in ("clean", "update", "noise", "update_noise"))
    write_json(output_dir / "status.json", summary)
    return summary


def run_requests(config: dict[str, Any], plan: list[dict[str, Any]], sequences: list[dict[str, Any]], output_dir: Path,
                 *, resume: bool = False, preflight: bool = False, client: Any = None, allow_mock: bool = False) -> dict[str, Any]:
    """Run the new graph; two-family preflight is a subset, never duplicated."""
    full_plan = plan
    if preflight:
        selected = sorted({r["family_id"] for r in plan})[:2]
        plan = [r for r in plan if r["family_id"] in selected]
    return _run(config, plan, sequences, output_dir, resume=resume, client=client, allow_mock=allow_mock, static=False, full_plan=full_plan)


def run_protocol(config: dict[str, Any], plan: list[dict[str, Any]], sequences: list[dict[str, Any]], output_dir: Path,
                 *, resume: bool = False, client: Any = None, allow_mock: bool = False) -> dict[str, Any]:
    """Run 108 independent snapshots with the same device and context gates."""
    return _run(config, plan, sequences, output_dir, resume=resume, client=client, allow_mock=allow_mock, static=True, full_plan=plan)
