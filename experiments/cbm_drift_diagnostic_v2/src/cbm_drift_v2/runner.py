"""Fingerprint-safe protocol-check and synchronous MAD runners."""

from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from cbm_drift_v2.common import read_json, read_jsonl, sha256_file, sha256_json, write_json
from cbm_drift_v2.parsing import parse_answer_set
from cbm_drift_v2.prompts import (
    MAD_REVISION_PROMPT,
    TASK_SYSTEM_PROMPT,
    peer_block,
    snapshot_user_message,
    stage_user_message,
)

RUNNER_VERSION = "cbm_drift_v2.runner.1"


def _safe_config(config: dict[str, Any]) -> dict[str, Any]:
    """Return a manifest-safe copy with credential values removed."""
    value = json.loads(json.dumps(config))
    value.get("model", {}).pop("api_key", None)
    return value


class OpenAIClient:
    """Small OpenAI-compatible client with deterministic endpoint routing."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.urls = list(config["model"]["base_urls"])
        if not self.urls:
            raise ValueError("At least one model endpoint is required")
        self.tokenizer = None
        try:
            from transformers import AutoTokenizer

            self.tokenizer = AutoTokenizer.from_pretrained(
                config["model"]["deployment"]["weights_path"], local_files_only=True
            )
        except (ImportError, OSError, ValueError):
            self.tokenizer = None

    def count_tokens(self, messages: list[dict[str, str]]) -> int | None:
        """Count input tokens with the deployed tokenizer when available."""
        if self.tokenizer is None:
            return None
        tokens = self.tokenizer.apply_chat_template(
            messages, tokenize=True, add_generation_prompt=True, enable_thinking=False
        )
        if hasattr(tokens, "keys") and "input_ids" in tokens:
            tokens = tokens["input_ids"]
        if tokens and isinstance(tokens[0], list):
            tokens = tokens[0]
        return len(tokens)

    def call(
        self, request_id: str, messages: list[dict[str, str]], seed: int, *, endpoint_index: int | None = None
    ) -> dict[str, Any]:
        """Issue one logical request; retries cover infrastructure failures only."""
        generation, model = self.config["generation"], self.config["model"]
        input_tokens = self.count_tokens(messages)
        max_context = int(model["deployment"]["max_model_len"])
        if input_tokens is not None and input_tokens + int(generation["max_tokens"]) > max_context:
            return {
                "api_success": False, "blocked": True, "blocked_reason": "context_budget_exceeded",
                "input_tokens_estimate": input_tokens, "endpoint": None, "raw_response": "",
                "finish_reason": None, "usage": None, "request_attempts": 0, "request_errors": [],
                "latency_seconds": 0.0, "response_model": None,
            }
        index = endpoint_index
        if index is None:
            index = int(sha256_json(request_id)[:8], 16) % len(self.urls)
        endpoint = self.urls[index % len(self.urls)]
        payload: dict[str, Any] = {
            "model": model["model_name"], "messages": messages,
            "temperature": generation["temperature"], "top_p": generation["top_p"],
            "max_tokens": generation["max_tokens"], "seed": seed,
        }
        payload.update(model.get("extra_body", {}))
        request = urllib.request.Request(
            endpoint.rstrip("/") + "/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {model.get('api_key', 'EMPTY')}"},
            method="POST",
        )
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        errors: list[str] = []
        started = time.monotonic()
        for attempt in range(int(generation["max_retries"]) + 1):
            try:
                with opener.open(request, timeout=int(generation["request_timeout_seconds"])) as response:
                    body = json.loads(response.read().decode("utf-8"))
                choice = body["choices"][0]
                return {
                    "api_success": True, "blocked": False, "blocked_reason": None,
                    "input_tokens_estimate": input_tokens, "endpoint": endpoint,
                    "raw_response": choice["message"].get("content") or "",
                    "finish_reason": choice.get("finish_reason"), "usage": body.get("usage"),
                    "request_attempts": attempt + 1, "request_errors": errors,
                    "latency_seconds": round(time.monotonic() - started, 4),
                    "response_model": body.get("model"),
                }
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, KeyError) as exc:
                errors.append(f"{type(exc).__name__}: {exc}")
                if attempt < int(generation["max_retries"]):
                    time.sleep(float(generation["retry_sleep_seconds"]))
        return {
            "api_success": False, "blocked": False, "blocked_reason": None,
            "input_tokens_estimate": input_tokens, "endpoint": endpoint, "raw_response": "",
            "finish_reason": None, "usage": None,
            "request_attempts": int(generation["max_retries"]) + 1, "request_errors": errors,
            "latency_seconds": round(time.monotonic() - started, 4), "response_model": None,
        }


class ExperimentRunner:
    """Execute protocol or MAD requests with strict resume and dependency checks."""

    def __init__(self, root: Path, config: dict[str, Any], kind: str) -> None:
        if kind not in {"protocol", "mad"}:
            raise ValueError(f"Unsupported run kind: {kind}")
        self.root, self.config, self.kind = root, config, kind
        self.data_dir = root / "data"
        self.results_dir = root / "results" / kind
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.output_path = self.results_dir / "raw_outputs.jsonl"
        self.sequences = {row["variant_id"]: row for row in read_jsonl(self.data_dir / "evidence_sequences.jsonl")}
        plan_name = "protocol_request_plan.jsonl" if kind == "protocol" else "mad_request_plan.jsonl"
        self.plan = read_jsonl(self.data_dir / plan_name)
        safe_config = _safe_config(config)
        prompt_payload = {
            "task": TASK_SYSTEM_PROMPT,
            "revision": MAD_REVISION_PROMPT,
            "protocol": "snapshot or synchronous three-agent evidence tracking",
        }
        data_names = ["selection_manifest.jsonl", "source_items.jsonl", "evidence_sequences.jsonl", plan_name]
        self.manifest = {
            "experiment_id": config["experiment_id"], "experiment_version": config["experiment_version"],
            "run_kind": kind, "runner_version": RUNNER_VERSION,
            "config": safe_config, "config_sha256": sha256_json(safe_config),
            "data_fingerprints": {name: sha256_file(self.data_dir / name) for name in data_names},
            "prompt_sha256": sha256_json(prompt_payload), "parser_sha256": sha256_file(Path(__file__).with_name("parsing.py")),
            "expected_logical_requests": len(self.plan),
        }
        self.manifest_hash = sha256_json(self.manifest)
        self.client = OpenAIClient(config)
        self.lock = threading.Lock()
        self.completed: dict[str, dict[str, Any]] = {}
        if self.output_path.exists():
            for row in read_jsonl(self.output_path):
                request_id = row["request_id"]
                if row.get("experiment_manifest_sha256") != self.manifest_hash:
                    raise RuntimeError(f"Existing {kind} record fingerprint mismatch: {request_id}")
                if request_id in self.completed:
                    raise RuntimeError(f"Duplicate request_id: {request_id}")
                self.completed[request_id] = row

    def initialize(self) -> None:
        """Write or verify the frozen experiment manifest."""
        path = self.results_dir / "experiment_manifest.json"
        if path.exists() and read_json(path) != self.manifest:
            raise RuntimeError(f"Existing {self.kind} manifest differs from frozen inputs")
        write_json(path, self.manifest)

    def _append(self, row: dict[str, Any]) -> None:
        with self.lock:
            if row["request_id"] in self.completed:
                return
            with self.output_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
                handle.flush()
            self.completed[row["request_id"]] = row

    def _record(
        self, plan: dict[str, Any], messages: list[dict[str, str]], api: dict[str, Any], visible_peer_ids: list[str]
    ) -> dict[str, Any]:
        sequence = self.sequences[plan["variant_id"]]
        names = {key: value["name"] for key, value in sequence["candidate_map"].items()}
        parsed = parse_answer_set(api["raw_response"], names) if api["api_success"] else {
            "recognized": False, "answer_set": None, "strict_json": False,
            "parse_source": "api_failure", "ambiguity_reason": "API request failed",
            "explanation": None, "raw_answer": None,
        }
        prediction = parsed.get("answer_set") if parsed.get("recognized") else None
        oracle = sorted(plan["oracle"])
        return {
            **plan, **api, "experiment_id": self.config["experiment_id"],
            "experiment_manifest_sha256": self.manifest_hash,
            "message_id": plan["request_id"], "messages": messages, "messages_sha256": sha256_json(messages),
            "visible_peer_message_ids": sorted(visible_peer_ids), "parse": parsed,
            "recognized_answer": bool(parsed.get("recognized")), "predicted_candidates": prediction,
            "correct": prediction is not None and sorted(prediction) == oracle,
            "omitted_candidates": sorted(set(oracle) - set(prediction or [])) if prediction is not None else None,
            "extra_candidates": sorted(set(prediction or []) - set(oracle)) if prediction is not None else None,
            "generation_config": self.config["generation"],
        }

    def _blocked(self, plan: dict[str, Any], dependency: str) -> dict[str, Any]:
        api = {
            "api_success": False, "blocked": True, "blocked_reason": "failed_dependency",
            "input_tokens_estimate": None, "endpoint": None, "raw_response": "", "finish_reason": None,
            "usage": None, "request_attempts": 0, "request_errors": [], "latency_seconds": 0.0,
            "response_model": None,
        }
        return self._record(plan, [], api, []) | {"blocked_by": dependency}

    def _call(
        self, plan: dict[str, Any], messages: list[dict[str, str]], visible_peer_ids: list[str], endpoint_index: int
    ) -> dict[str, Any]:
        api = self.client.call(plan["request_id"], messages, int(plan["seed"]), endpoint_index=endpoint_index)
        return self._record(plan, messages, api, visible_peer_ids)

    def _protocol_messages(self, plan: dict[str, Any]) -> list[dict[str, str]]:
        sequence = self.sequences[plan["variant_id"]]
        return [
            {"role": "system", "content": TASK_SYSTEM_PROMPT},
            {"role": "user", "content": snapshot_user_message(sequence, int(plan["evidence_stage"]))},
        ]

    def run_protocol(self) -> dict[str, int]:
        """Run all independent protocol snapshots."""
        if self.kind != "protocol":
            raise RuntimeError("Runner was not initialized for protocol")
        self.initialize()
        pending = [row for row in self.plan if row["request_id"] not in self.completed]
        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = [
                pool.submit(self._call, row, self._protocol_messages(row), [], index % len(self.client.urls))
                for index, row in enumerate(pending)
            ]
            for future in as_completed(futures):
                self._append(future.result())
        return {"expected": len(self.plan), "completed": len(self.completed), "new_calls": len(pending)}

    def _history(self, dependency_id: str) -> tuple[list[dict[str, str]] | None, str | None]:
        previous = self.completed.get(dependency_id)
        if previous is None or not previous.get("api_success"):
            return None, dependency_id
        return [*previous["messages"], {"role": "assistant", "content": previous["raw_response"]}], None

    def _mad_messages(
        self, plan: dict[str, Any], preceding_round: dict[str, dict[str, Any]]
    ) -> tuple[list[dict[str, str]] | None, list[str], str | None]:
        sequence = self.sequences[plan["variant_id"]]
        stage, round_id = int(plan["evidence_stage"]), int(plan["round"])
        if round_id == 0:
            if stage == 1:
                messages = [{"role": "system", "content": TASK_SYSTEM_PROMPT}]
            else:
                dependency = f"mad:{plan['variant_id']}:t{stage - 1}:r2:{plan['agent_id']}"
                messages, blocked = self._history(dependency)
                if messages is None:
                    return None, [], blocked
            messages.append({"role": "user", "content": stage_user_message(sequence, stage, include_task=stage == 1)})
            return messages, [], None
        own_dependency = f"mad:{plan['variant_id']}:t{stage}:r{round_id - 1}:{plan['agent_id']}"
        messages, blocked = self._history(own_dependency)
        if messages is None:
            return None, [], blocked
        peers = [preceding_round[agent] for agent in sorted(preceding_round) if agent != plan["agent_id"]]
        visible = [row["message_id"] for row in peers]
        messages.append({"role": "user", "content": MAD_REVISION_PROMPT.format(peer_block=peer_block(peers))})
        return messages, visible, None

    def _run_trajectory(self, variant_id: str, endpoint_index: int) -> None:
        rows = [row for row in self.plan if row["variant_id"] == variant_id]
        by_key = {(int(row["evidence_stage"]), int(row["round"]), row["agent_id"]): row for row in rows}
        agents = list(self.config["mad"]["agents"])
        for stage in self.config["mad"]["stages"]:
            prior: dict[str, dict[str, Any]] = {}
            for round_id in self.config["mad"]["rounds"]:
                plans = [by_key[(int(stage), int(round_id), agent)] for agent in agents]
                pending = [row for row in plans if row["request_id"] not in self.completed]
                def execute(row: dict[str, Any]) -> dict[str, Any]:
                    messages, visible, dependency = self._mad_messages(row, prior)
                    if messages is None:
                        return self._blocked(row, str(dependency))
                    return self._call(row, messages, visible, endpoint_index)
                if pending:
                    with ThreadPoolExecutor(max_workers=len(pending)) as pool:
                        for result in pool.map(execute, pending):
                            self._append(result)
                prior = {row["agent_id"]: self.completed[row["request_id"]] for row in plans}

    def run_mad(self, *, preflight_only: bool = False) -> dict[str, int]:
        """Run trajectories with stage/round barriers and deterministic endpoint affinity."""
        if self.kind != "mad":
            raise RuntimeError("Runner was not initialized for MAD")
        self.initialize()
        variants = sorted(self.sequences)
        if preflight_only:
            families = sorted({self.sequences[value]["family_id"] for value in variants})[: int(self.config["mad"]["preflight_base_items"])]
            variants = [value for value in variants if self.sequences[value]["family_id"] in families]
        before = len(self.completed)
        workers = min(int(self.config["generation"]["max_concurrent_trajectories"]), len(self.client.urls), len(variants))
        with ThreadPoolExecutor(max_workers=max(workers, 1)) as pool:
            futures = [pool.submit(self._run_trajectory, variant, index % len(self.client.urls)) for index, variant in enumerate(variants)]
            for future in as_completed(futures):
                future.result()
        return {
            "trajectories_selected": len(variants), "expected_total": len(self.plan),
            "completed_total": len(self.completed), "new_records": len(self.completed) - before,
        }


def audit_outputs(root: Path, kind: str) -> dict[str, Any]:
    """Audit output inventory independently of the execution loop."""
    plan_name = "protocol_request_plan.jsonl" if kind == "protocol" else "mad_request_plan.jsonl"
    plan = read_jsonl(root / "data" / plan_name)
    output_path = root / "results" / kind / "raw_outputs.jsonl"
    outputs = read_jsonl(output_path) if output_path.exists() else []
    expected, seen = {row["request_id"] for row in plan}, [row["request_id"] for row in outputs]
    duplicates = sorted({value for value in seen if seen.count(value) > 1})
    return {
        "kind": kind, "expected": len(expected), "records": len(outputs),
        "missing": sorted(expected - set(seen)), "unknown": sorted(set(seen) - expected),
        "duplicates": duplicates,
        "api_failures": sum(not row.get("api_success", False) for row in outputs),
        "recognized": sum(bool(row.get("recognized_answer")) for row in outputs),
        "strict_json": sum(bool(row.get("parse", {}).get("strict_json")) for row in outputs),
        "truncated": sum(row.get("finish_reason") == "length" for row in outputs),
    }
