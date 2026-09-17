"""Resumable, fingerprinted protocol-check and synchronous MAD runners."""

from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from cbm_attr_v1.parsing import parse_candidate_set, parse_single_choice
from cbm_attr_v1.prompts import dynamic_user_message, snapshot_message, source_set_message
from mad_drift_pilot import EXPERIMENT_VERSION, PARSER_VERSION, PROTOCOL_VERSION
from mad_drift_pilot.common import file_sha256, read_json, read_jsonl, sha256_json, write_json
from mad_drift_pilot.prompts import (
    SET_MAD_REVISION,
    SET_SELF_REVISION,
    SET_SYSTEM_PROMPT_V2,
    STATIC_MAD_REVISION,
    STATIC_ORIGINAL_PROMPT,
    STATIC_SELF_REVISION,
    peer_block,
)


def _safe_config(config: dict[str, Any]) -> dict[str, Any]:
    value = json.loads(json.dumps(config))
    value.get("model", {}).pop("api_key", None)
    return value


class ApiClient:
    """OpenAI-compatible client with deterministic endpoint assignment."""

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
        """Estimate exact chat-template input tokens when tokenizer is available."""
        if self.tokenizer is None:
            return None
        value = self.tokenizer.apply_chat_template(
            messages, tokenize=True, add_generation_prompt=True, enable_thinking=False
        )
        if hasattr(value, "keys") and "input_ids" in value:
            value = value["input_ids"]
        if value and isinstance(value[0], list):
            value = value[0]
        return len(value)

    def call(self, request_id: str, messages: list[dict[str, str]], seed: int) -> dict[str, Any]:
        """Call one endpoint, retaining every error and actual request parameter."""
        generation = self.config["generation"]
        model = self.config["model"]
        input_tokens = self.count_tokens(messages)
        max_model_len = int(model["deployment"]["max_model_len"])
        if input_tokens is not None and input_tokens + int(generation["max_tokens"]) > max_model_len:
            return {
                "api_success": False, "blocked": True, "blocked_reason": "context_budget_exceeded",
                "input_tokens_estimate": input_tokens, "endpoint": None, "raw_response": "",
                "finish_reason": None, "usage": None, "request_attempts": 0, "request_errors": [],
                "latency_seconds": 0.0, "response_model": None,
            }
        endpoint_index = int(sha256_json(request_id)[:8], 16) % len(self.urls)
        endpoint = self.urls[endpoint_index]
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
                    parsed = json.loads(response.read().decode("utf-8"))
                choice = parsed["choices"][0]
                return {
                    "api_success": True, "blocked": False, "blocked_reason": None,
                    "input_tokens_estimate": input_tokens, "endpoint": endpoint,
                    "raw_response": choice["message"].get("content") or "",
                    "finish_reason": choice.get("finish_reason"), "usage": parsed.get("usage"),
                    "request_attempts": attempt + 1, "request_errors": errors,
                    "latency_seconds": round(time.monotonic() - started, 4),
                    "response_model": parsed.get("model"),
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


class BaseRunner:
    """Shared manifest, parsing, scoring, append, and resume behavior."""

    def __init__(self, root: Path, config: dict[str, Any], *, kind: str) -> None:
        self.root = root
        self.config = config
        self.kind = kind
        self.data_dir = root / "data"
        self.results_dir = root / "results" / ("protocol_check" if kind == "protocol" else kind)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.output_path = self.results_dir / "raw_outputs.jsonl"
        self.items = {row["base_item_id"]: row for row in read_jsonl(self.data_dir / "source_items.jsonl")}
        self.episodes = {row["base_item_id"]: row for row in read_jsonl(self.data_dir / "episodes.jsonl")}
        self.snapshots = {row["snapshot_id"]: row for row in read_jsonl(self.data_dir / "snapshots.jsonl")}
        plan_name = "protocol_request_plan.jsonl" if kind == "protocol" else "mad_request_plan.jsonl"
        self.plan = read_jsonl(self.data_dir / plan_name)
        self.plan_by_id = {row["request_id"]: row for row in self.plan}
        prompt_payload = {
            "set_system": SET_SYSTEM_PROMPT_V2, "static_original": STATIC_ORIGINAL_PROMPT,
            "static_mad": STATIC_MAD_REVISION, "static_self": STATIC_SELF_REVISION,
            "set_mad": SET_MAD_REVISION, "set_self": SET_SELF_REVISION,
        }
        data_names = ("selection_manifest.jsonl", "source_items.jsonl", "episodes.jsonl", "snapshots.jsonl", plan_name)
        safe = _safe_config(config)
        self.manifest = {
            "experiment_id": config["experiment_id"], "experiment_version": EXPERIMENT_VERSION,
            "runner_kind": kind, "config": safe, "config_sha256": sha256_json(safe),
            "data_fingerprints": {name: file_sha256(self.data_dir / name) for name in data_names},
            "prompt_version": PROTOCOL_VERSION, "prompt_sha256": sha256_json(prompt_payload),
            "parser_version": PARSER_VERSION, "expected_logical_requests": len(self.plan),
        }
        self.manifest_hash = sha256_json(self.manifest)
        self.client = ApiClient(config)
        self.lock = threading.Lock()
        self.completed: dict[str, dict[str, Any]] = {}
        if self.output_path.exists():
            for row in read_jsonl(self.output_path):
                if row.get("experiment_manifest_sha256") != self.manifest_hash:
                    raise RuntimeError(f"Existing {kind} output fingerprint mismatch")
                if row["request_id"] in self.completed:
                    raise RuntimeError(f"Duplicate request id {row['request_id']}")
                self.completed[row["request_id"]] = row

    def initialize(self) -> None:
        """Write or verify the immutable experiment manifest."""
        path = self.results_dir / "experiment_manifest.json"
        if path.exists() and read_json(path) != self.manifest:
            raise RuntimeError(f"Existing {self.kind} manifest differs")
        write_json(path, self.manifest)

    def _append(self, row: dict[str, Any]) -> None:
        with self.lock:
            if row["request_id"] in self.completed:
                return
            with self.output_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
                handle.flush()
            self.completed[row["request_id"]] = row

    def _record(self, plan: dict[str, Any], messages: list[dict[str, str]], api: dict[str, Any], *, reused_from: str | None = None) -> dict[str, Any]:
        item = self.items[plan["base_item_id"]]
        names = {label: item["entities"][label]["name"] for label in ("A", "B", "C", "D")}
        if plan["protocol"] == "single_choice":
            parsed = parse_single_choice(api["raw_response"], names) if api["api_success"] else {"recognized": False, "parse_source": "api_failure"}
            prediction = [parsed["answer"]] if parsed.get("recognized") else None
        else:
            parsed = parse_candidate_set(api["raw_response"], names) if api["api_success"] else {"recognized": False, "parse_source": "api_failure"}
            prediction = parsed.get("candidates") if parsed.get("recognized") else None
        oracle = sorted(plan["oracle"])
        static_violations = []
        if prediction and plan["protocol"] == "single_choice":
            static_violations = item["option_violation_signature"][prediction[0]]
        return {
            **plan, **api, "experiment_id": self.config["experiment_id"],
            "experiment_manifest_sha256": self.manifest_hash, "messages": messages,
            "messages_sha256": sha256_json(messages), "parse": parsed,
            "recognized_answer": bool(parsed.get("recognized")), "predicted_candidates": prediction,
            "correct": prediction is not None and sorted(prediction) == oracle,
            "omitted_candidates": sorted(set(oracle) - set(prediction or [])) if prediction is not None else None,
            "extra_candidates": sorted(set(prediction or []) - set(oracle)) if prediction is not None else None,
            "selected_option_violation_signature": static_violations,
            "reused_from": reused_from,
            "generation_config": self.config["generation"],
        }

    def _blocked(self, plan: dict[str, Any], dependency: str) -> dict[str, Any]:
        api = {"api_success": False, "blocked": True, "blocked_reason": "failed_dependency", "input_tokens_estimate": None, "endpoint": None, "raw_response": "", "finish_reason": None, "usage": None, "request_attempts": 0, "request_errors": [], "latency_seconds": 0.0, "response_model": None}
        return self._record(plan, [], api) | {"blocked_by": dependency}

    def _call(self, plan: dict[str, Any], messages: list[dict[str, str]]) -> dict[str, Any]:
        api = self.client.call(plan["request_id"], messages, int(plan["seed"]))
        return self._record(plan, messages, api)


class ProtocolCheckRunner(BaseRunner):
    """Re-run the old 26-call design with the v2 set protocol."""

    def __init__(self, root: Path, config: dict[str, Any], repository_root: Path) -> None:
        super().__init__(root, config, kind="protocol")
        self.old_outputs = {row["request_id"]: row for row in read_jsonl(repository_root / "experiments/cbm_attr_v1/results/raw_outputs.jsonl")}

    def _round(self, episode: dict[str, Any], condition: str, stage: int) -> dict[str, Any]:
        key = {"C_clean": "clean", "E_noise": "noise", "D_update": "update"}[condition]
        return next(row for row in episode[key]["rounds"] if row["round_id"] == stage)

    def _dynamic_messages(self, plan: dict[str, Any]) -> tuple[list[dict[str, str]] | None, str | None]:
        item, episode = self.items[plan["base_item_id"]], self.episodes[plan["base_item_id"]]
        condition, stage = plan["condition"], int(plan["round_id"])
        messages = [{"role": "system", "content": SET_SYSTEM_PROMPT_V2}]
        history_condition = "C_clean" if condition == "D_update" else condition
        history_stages = range(1, 4 if condition == "D_update" else stage)
        for previous_stage in history_stages:
            row = self._round(episode, history_condition, previous_stage)
            messages.append({"role": "user", "content": dynamic_user_message(item, history_condition, row, first_round=previous_stage == 1)})
            previous_id = f"{plan['unit_id']}:{history_condition}:r{previous_stage}"
            previous = self.completed.get(previous_id)
            if not previous or not previous["api_success"]:
                return None, previous_id
            messages.append({"role": "assistant", "content": previous["raw_response"]})
        if condition == "D_update" and stage == 5:
            d4 = self.completed.get(f"{plan['unit_id']}:D_update:r4")
            if not d4 or not d4["api_success"]:
                return None, f"{plan['unit_id']}:D_update:r4"
            messages.extend((
                {"role": "user", "content": dynamic_user_message(item, condition, self._round(episode, condition, 4), first_round=False)},
                {"role": "assistant", "content": d4["raw_response"]},
            ))
        current = self._round(episode, condition, stage)
        messages.append({"role": "user", "content": dynamic_user_message(item, condition, current, first_round=stage == 1)})
        return messages, None

    def _messages(self, plan: dict[str, Any]) -> tuple[list[dict[str, str]] | None, str | None]:
        item = self.items[plan["base_item_id"]]
        if plan["condition"] == "A_original":
            return [{"role": "user", "content": STATIC_ORIGINAL_PROMPT.format(question=item["question"])}], None
        if plan["condition"] == "B_source_set":
            return [{"role": "system", "content": SET_SYSTEM_PROMPT_V2}, {"role": "user", "content": source_set_message(item)}], None
        if plan["condition"] in {"C_clean", "E_noise", "D_update"}:
            return self._dynamic_messages(plan)
        snapshot = self.snapshots[plan["snapshot_id"]]
        return [{"role": "system", "content": SET_SYSTEM_PROMPT_V2}, {"role": "user", "content": snapshot_message(item, snapshot)}], None

    def _run_unit(self, unit_id: str) -> tuple[int, int, int]:
        order = {"A_original": 0, "B_source_set": 1, "C_clean": 2, "E_noise": 3, "D_update": 4, "P_snapshot": 5}
        plans = sorted((row for row in self.plan if row["unit_id"] == unit_id), key=lambda row: (order[row["condition"]], row.get("snapshot_condition", ""), row["round_id"]))
        called = reused = skipped = 0
        for plan in plans:
            if plan["request_id"] in self.completed:
                skipped += 1
                continue
            messages, dependency = self._messages(plan)
            if messages is None:
                self._append(self._blocked(plan, str(dependency)))
                continue
            if plan["condition"] == "A_original":
                old = self.old_outputs[plan["request_id"]]
                if old["messages"] != messages:
                    raise RuntimeError("A_original reuse fingerprint mismatch")
                api_keys = ("api_success", "blocked", "blocked_by", "raw_response", "finish_reason", "usage", "response_model", "request_attempts", "request_errors", "latency_seconds")
                api = {key: old.get(key) for key in api_keys}
                api.update({"blocked_reason": old.get("blocked_by"), "input_tokens_estimate": None, "endpoint": old.get("generation_config", {}).get("base_url")})
                self._append(self._record(plan, messages, api, reused_from="experiments/cbm_attr_v1/results/raw_outputs.jsonl"))
                reused += 1
            else:
                self._append(self._call(plan, messages))
                called += 1
        return called, reused, skipped

    def run(self, *, limit_units: int | None = None) -> dict[str, int]:
        """Execute independent item-run protocol units."""
        self.initialize()
        units = sorted({row["unit_id"] for row in self.plan})
        if limit_units is not None:
            units = units[:limit_units]
        totals = [0, 0, 0]
        with ThreadPoolExecutor(max_workers=int(self.config["generation"]["max_concurrent_units"])) as pool:
            for result in (future.result() for future in as_completed([pool.submit(self._run_unit, unit) for unit in units])):
                totals = [left + right for left, right in zip(totals, result, strict=True)]
        return {"units": len(units), "new_api_calls": totals[0], "reused_calls": totals[1], "skipped": totals[2], "records": len(self.completed)}


class MadRunner(BaseRunner):
    """Execute static and CBM MAD/control branches with synchronous rounds."""

    def __init__(self, root: Path, config: dict[str, Any]) -> None:
        super().__init__(root, config, kind="static")
        self.cbm_results_dir = root / "results/cbm"
        self.cbm_results_dir.mkdir(parents=True, exist_ok=True)
        for condition in ("C_clean", "E_noise", "D_update"):
            path = self.cbm_results_dir / f"raw_outputs_{condition}.jsonl"
            if not path.exists():
                continue
            for row in read_jsonl(path):
                if row.get("experiment_manifest_sha256") != self.manifest_hash:
                    raise RuntimeError(f"Existing {condition} output fingerprint mismatch")
                if row["request_id"] in self.completed:
                    raise RuntimeError(f"Duplicate request id {row['request_id']}")
                self.completed[row["request_id"]] = row

    def initialize(self) -> None:
        """Initialize shared manifests in both result namespaces."""
        super().initialize()
        write_json(self.cbm_results_dir / "experiment_manifest.json", self.manifest)

    def _append(self, row: dict[str, Any]) -> None:
        if row["task_family"] == "static":
            path = self.output_path
        else:
            path = self.cbm_results_dir / f"raw_outputs_{row['condition']}.jsonl"
        with self.lock:
            if row["request_id"] in self.completed:
                return
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
                handle.flush()
            self.completed[row["request_id"]] = row

    def _prior_messages(self, dependency_id: str) -> tuple[list[dict[str, str]] | None, str | None]:
        previous = self.completed.get(dependency_id)
        if not previous or not previous.get("api_success"):
            return None, dependency_id
        return [*previous["messages"], {"role": "assistant", "content": previous["raw_response"]}], None

    def _messages(self, plan: dict[str, Any], peers: dict[str, dict[str, Any]]) -> tuple[list[dict[str, str]] | None, str | None]:
        item = self.items[plan["base_item_id"]]
        if plan["task_family"] == "static" and plan["revision_round"] == 0:
            return [{"role": "user", "content": STATIC_ORIGINAL_PROMPT.format(question=item["question"])}], None
        if plan["revision_round"] == 0:
            dependency = plan["depends_on"][0] if plan["depends_on"] else None
            if dependency:
                messages, blocked = self._prior_messages(dependency)
                if messages is None:
                    return None, blocked
            else:
                messages = [{"role": "system", "content": SET_SYSTEM_PROMPT_V2}]
            key = {"C_clean": "clean", "E_noise": "noise", "D_update": "update"}[plan["condition"]]
            round_data = next(row for row in self.episodes[plan["base_item_id"]][key]["rounds"] if row["round_id"] == plan["stage"])
            messages.append({"role": "user", "content": dynamic_user_message(item, plan["condition"], round_data, first_round=plan["stage"] == 1)})
            return messages, None
        dependency = plan["depends_on"][0]
        messages, blocked = self._prior_messages(dependency)
        if messages is None:
            return None, blocked
        set_protocol = plan["protocol"] == "candidate_set"
        if plan["branch"] == "mad":
            template = SET_MAD_REVISION if set_protocol else STATIC_MAD_REVISION
            prompt = template.format(peers=peer_block(peers, plan["agent_id"], set_protocol=set_protocol))
        else:
            prompt = SET_SELF_REVISION if set_protocol else STATIC_SELF_REVISION
        messages.append({"role": "user", "content": prompt})
        return messages, None

    def _batch(self, plans: list[dict[str, Any]], peer_records: dict[str, dict[str, Any]] | None = None) -> None:
        peer_records = peer_records or {}
        pending = [plan for plan in plans if plan["request_id"] not in self.completed]
        if not pending:
            return

        def execute(plan: dict[str, Any]) -> dict[str, Any]:
            messages, dependency = self._messages(plan, peer_records)
            return self._blocked(plan, str(dependency)) if messages is None else self._call(plan, messages)

        with ThreadPoolExecutor(max_workers=len(pending)) as pool:
            for result in pool.map(execute, pending):
                self._append(result)

    def _rows(self, base: str, run_id: int, **filters: Any) -> list[dict[str, Any]]:
        rows = [row for row in self.plan if row["base_item_id"] == base and row["team_run_id"] == run_id]
        for key, value in filters.items():
            rows = [row for row in rows if row[key] == value]
        return sorted(rows, key=lambda row: row["agent_id"])

    def _run_stage(self, base: str, run_id: int, *, family: str, condition: str, stage: int | None) -> None:
        base_filter = {"task_family": family, "condition": condition, "stage": stage}
        shared = self._rows(base, run_id, **base_filter, branch="shared", revision_round=0)
        self._batch(shared)
        shared_records = {row["agent_id"]: self.completed[row["request_id"]] for row in shared}
        for branch in ("mad", "self"):
            previous = shared_records
            for revision in (1, 2):
                plans = self._rows(base, run_id, **base_filter, branch=branch, revision_round=revision)
                self._batch(plans, previous if branch == "mad" else {})
                previous = {row["agent_id"]: self.completed[row["request_id"]] for row in plans}

    def _run_unit(self, base: str, run_id: int) -> None:
        self._run_stage(base, run_id, family="static", condition="A_original", stage=None)
        for condition in ("C_clean", "E_noise"):
            for stage in range(1, 6):
                self._run_stage(base, run_id, family="cbm", condition=condition, stage=stage)
        for stage in (4, 5):
            self._run_stage(base, run_id, family="cbm", condition="D_update", stage=stage)

    def run(self, *, limit_units: int | None = None, unit_ids: list[str] | None = None) -> dict[str, int]:
        """Run independent base-item/team units while preserving all barriers."""
        self.initialize()
        units = [(item, run_id) for item in sorted(self.items) for run_id in (1, 2, 3)]
        if unit_ids is not None:
            allowed = set(unit_ids)
            units = [unit for unit in units if f"{unit[0]}:team{unit[1]}" in allowed]
        if limit_units is not None:
            units = units[:limit_units]
        with ThreadPoolExecutor(max_workers=int(self.config["generation"]["max_concurrent_units"])) as pool:
            futures = [pool.submit(self._run_unit, base, run_id) for base, run_id in units]
            for future in as_completed(futures):
                future.result()
        return {"units": len(units), "records": len(self.completed), "expected_total": len(self.plan)}
