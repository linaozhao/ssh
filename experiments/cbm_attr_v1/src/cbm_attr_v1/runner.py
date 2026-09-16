"""Resumable OpenAI-compatible runner for CBM-Attr v1 trajectories."""

from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from cbm_attr_v1.common import (
    PARSER_VERSION,
    PROMPT_VERSION,
    file_sha256,
    read_json,
    read_jsonl,
    sha256_json,
    write_json,
    write_jsonl,
)
from cbm_attr_v1.parsing import parse_candidate_set, parse_single_choice
from cbm_attr_v1.prompts import (
    ORIGINAL_PROMPT,
    SET_SYSTEM_PROMPT,
    dynamic_user_message,
    snapshot_message,
    source_set_message,
)


def _safe_config(config: dict[str, Any]) -> dict[str, Any]:
    value = json.loads(json.dumps(config))
    value.get("model", {}).pop("api_key", None)
    return value


def build_experiment_manifest(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    """Build the immutable fingerprint checked before every resume."""
    data_dir = root / "data"
    fingerprints = {
        name: file_sha256(data_dir / name)
        for name in (
            "selection_manifest.jsonl",
            "source_items.jsonl",
            "episodes.jsonl",
            "snapshots.jsonl",
            "request_plan.jsonl",
        )
    }
    safe = _safe_config(config)
    return {
        "experiment_id": config["experiment_id"],
        "experiment_version": config["experiment_version"],
        "config": safe,
        "config_sha256": sha256_json(safe),
        "data_fingerprints": fingerprints,
        "prompt_version": PROMPT_VERSION,
        "prompt_sha256": sha256_json({"set": SET_SYSTEM_PROMPT, "original": ORIGINAL_PROMPT}),
        "parser_version": PARSER_VERSION,
        "expected_logical_requests": len(read_jsonl(data_dir / "request_plan.jsonl")),
        "reuse_policy": "preflight responses are reused only when request_id and all experiment fingerprints match",
    }


def _api_call(config: dict[str, Any], messages: list[dict[str, str]], seed: int) -> dict[str, Any]:
    model = config["model"]
    generation = config["generation"]
    payload: dict[str, Any] = {
        "model": model["model_name"],
        "messages": messages,
        "temperature": generation["temperature"],
        "top_p": generation["top_p"],
        "max_tokens": generation["max_tokens"],
        "seed": seed,
    }
    payload.update(model.get("extra_body", {}))
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        model["base_url"].rstrip("/") + "/chat/completions",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {model.get('api_key', 'EMPTY')}"},
        method="POST",
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    errors: list[str] = []
    started = time.monotonic()
    for attempt in range(generation["max_retries"] + 1):
        try:
            with opener.open(request, timeout=generation["request_timeout_seconds"]) as response:
                parsed = json.loads(response.read().decode("utf-8"))
            choice = parsed["choices"][0]
            content = choice["message"].get("content") or ""
            return {
                "api_success": True,
                "raw_response": content,
                "finish_reason": choice.get("finish_reason"),
                "usage": parsed.get("usage"),
                "response_model": parsed.get("model"),
                "request_attempts": attempt + 1,
                "request_errors": errors,
                "latency_seconds": round(time.monotonic() - started, 4),
            }
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, KeyError) as exc:
            errors.append(f"{type(exc).__name__}: {exc}")
            if attempt < generation["max_retries"]:
                time.sleep(generation["retry_sleep_seconds"])
    return {
        "api_success": False,
        "raw_response": "",
        "finish_reason": None,
        "usage": None,
        "response_model": None,
        "request_attempts": generation["max_retries"] + 1,
        "request_errors": errors,
        "latency_seconds": round(time.monotonic() - started, 4),
    }


class ExperimentRunner:
    """Execute independent units while preserving within-trajectory ordering."""

    def __init__(self, root: Path, config: dict[str, Any]) -> None:
        self.root = root
        self.config = config
        self.data_dir = root / "data"
        self.results_dir = root / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.output_path = self.results_dir / "raw_outputs.jsonl"
        self.items = {row["base_item_id"]: row for row in read_jsonl(self.data_dir / "source_items.jsonl")}
        self.episodes = {row["base_item_id"]: row for row in read_jsonl(self.data_dir / "episodes.jsonl")}
        self.snapshots = {row["snapshot_id"]: row for row in read_jsonl(self.data_dir / "snapshots.jsonl")}
        self.plan = read_jsonl(self.data_dir / "request_plan.jsonl")
        self.plan_by_id = {row["request_id"]: row for row in self.plan}
        self.manifest = build_experiment_manifest(root, config)
        self.manifest_hash = sha256_json(self.manifest)
        self.lock = threading.Lock()
        self.completed: dict[str, dict[str, Any]] = {}
        if self.output_path.exists():
            for row in read_jsonl(self.output_path):
                if row.get("experiment_manifest_sha256") != self.manifest_hash:
                    raise RuntimeError("Existing output fingerprint does not match the current frozen experiment")
                request_id = row["request_id"]
                if request_id in self.completed:
                    raise RuntimeError(f"Duplicate existing request_id: {request_id}")
                self.completed[request_id] = row

    def initialize_manifest(self) -> None:
        """Write or verify the experiment manifest."""
        path = self.results_dir / "experiment_manifest.json"
        if path.exists() and read_json(path) != self.manifest:
            raise RuntimeError("experiment_manifest.json differs from current inputs")
        write_json(path, self.manifest)

    def preflight_item_ids(self) -> list[str]:
        """Choose the first deterministic source item from every cell."""
        chosen: dict[str, str] = {}
        for row in read_jsonl(self.data_dir / "selection_manifest.jsonl"):
            chosen.setdefault(row["difficulty_cell"], row["base_item_id"])
        return [chosen[cell] for cell in sorted(chosen)]

    def write_preflight_manifest(self) -> None:
        rows = []
        selection = {row["base_item_id"]: row for row in read_jsonl(self.data_dir / "selection_manifest.jsonl")}
        for base in self.preflight_item_ids():
            rows.append({**selection[base], "run_id": 1, "seed": self.config["seeds"][0], "expected_requests": 26})
        write_jsonl(self.results_dir / "preflight_manifest.jsonl", rows)

    def _condition_round(self, episode: dict[str, Any], condition: str, round_id: int) -> dict[str, Any]:
        key = {"C_clean": "clean", "E_noise": "noise", "D_update": "update"}[condition]
        return next(row for row in episode[key]["rounds"] if row["round_id"] == round_id)

    def _dynamic_messages(self, plan: dict[str, Any]) -> tuple[list[dict[str, str]] | None, str | None]:
        item = self.items[plan["base_item_id"]]
        episode = self.episodes[plan["base_item_id"]]
        condition = plan["condition"]
        round_id = int(plan["round_id"])
        messages: list[dict[str, str]] = [{"role": "system", "content": SET_SYSTEM_PROMPT}]
        history_condition = "C_clean" if condition == "D_update" else condition
        history_rounds = range(1, 4 if condition == "D_update" else round_id)
        for previous_round in history_rounds:
            row = self._condition_round(episode, history_condition, previous_round)
            messages.append({"role": "user", "content": dynamic_user_message(item, history_condition, row, first_round=previous_round == 1)})
            previous_id = f"{plan['unit_id']}:{history_condition}:r{previous_round}"
            output = self.completed.get(previous_id)
            if not output or not output.get("api_success"):
                return None, previous_id
            messages.append({"role": "assistant", "content": output["raw_response"]})
        if condition == "D_update" and round_id == 5:
            d4_row = self._condition_round(episode, "D_update", 4)
            messages.append({"role": "user", "content": dynamic_user_message(item, "D_update", d4_row, first_round=False)})
            d4 = self.completed.get(f"{plan['unit_id']}:D_update:r4")
            if not d4 or not d4.get("api_success"):
                return None, f"{plan['unit_id']}:D_update:r4"
            messages.append({"role": "assistant", "content": d4["raw_response"]})
        current = self._condition_round(episode, condition, round_id)
        messages.append({"role": "user", "content": dynamic_user_message(item, condition, current, first_round=round_id == 1)})
        return messages, None

    def _messages(self, plan: dict[str, Any]) -> tuple[list[dict[str, str]] | None, str | None]:
        item = self.items[plan["base_item_id"]]
        condition = plan["condition"]
        if condition == "A_original":
            return [{"role": "user", "content": ORIGINAL_PROMPT.format(question=item["question"])}], None
        if condition == "B_source_set":
            return [{"role": "system", "content": SET_SYSTEM_PROMPT}, {"role": "user", "content": source_set_message(item)}], None
        if condition in {"C_clean", "E_noise", "D_update"}:
            return self._dynamic_messages(plan)
        snapshot = self.snapshots[plan["snapshot_id"]]
        return [{"role": "system", "content": SET_SYSTEM_PROMPT}, {"role": "user", "content": snapshot_message(item, snapshot)}], None

    def _append(self, row: dict[str, Any]) -> None:
        with self.lock:
            with self.output_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
                handle.flush()
            self.completed[row["request_id"]] = row

    def _run_request(self, plan: dict[str, Any], *, phase: str) -> dict[str, Any]:
        messages, blocked_by = self._messages(plan)
        item = self.items[plan["base_item_id"]]
        base = {
            **plan,
            "experiment_id": self.config["experiment_id"],
            "experiment_manifest_sha256": self.manifest_hash,
            "phase_first_executed": phase,
            "model_alias": self.config["model"]["alias"],
            "model_name": self.config["model"]["model_name"],
            "generation_config": self.config["generation"],
            "thinking_enabled": self.config["model"]["thinking_enabled"],
        }
        if messages is None:
            return {
                **base,
                "api_success": False,
                "blocked": True,
                "blocked_by": blocked_by,
                "messages": None,
                "messages_sha256": None,
                "raw_response": "",
                "recognized_answer": False,
                "correct": False,
                "parse": {"recognized": False, "parse_source": "blocked"},
                "finish_reason": None,
                "usage": None,
                "request_attempts": 0,
                "request_errors": [],
            }
        api = _api_call(self.config, messages, int(plan["seed"]))
        names = {label: item["entities"][label]["name"] for label in ("A", "B", "C", "D")}
        if plan["protocol"] == "single_choice":
            parsed = parse_single_choice(api["raw_response"], names) if api["api_success"] else {"recognized": False, "parse_source": "api_failure"}
            prediction = [parsed["answer"]] if parsed.get("recognized") else None
        else:
            parsed = parse_candidate_set(api["raw_response"], names) if api["api_success"] else {"recognized": False, "parse_source": "api_failure"}
            prediction = parsed.get("candidates") if parsed.get("recognized") else None
        oracle = sorted(plan["oracle"])
        return {
            **base,
            **api,
            "blocked": False,
            "blocked_by": None,
            "messages": messages,
            "messages_sha256": sha256_json(messages),
            "parse": parsed,
            "recognized_answer": bool(parsed.get("recognized")),
            "predicted_candidates": prediction,
            "correct": prediction is not None and sorted(prediction) == oracle,
        }

    def _run_unit(self, unit_id: str, phase: str) -> tuple[int, int]:
        unit_rows = [row for row in self.plan if row["unit_id"] == unit_id]
        order = {"A_original": 0, "B_source_set": 1, "C_clean": 2, "E_noise": 3, "D_update": 4, "P_snapshot": 5}
        unit_rows.sort(key=lambda row: (order[row["condition"]], row.get("snapshot_condition", ""), row["round_id"]))
        attempted = skipped = 0
        for plan in unit_rows:
            if plan["request_id"] in self.completed:
                skipped += 1
                continue
            result = self._run_request(plan, phase=phase)
            self._append(result)
            attempted += 1
        return attempted, skipped

    def run(self, *, phase: str) -> dict[str, int]:
        """Run the stratified preflight or all remaining formal units."""
        if phase not in {"preflight", "formal"}:
            raise ValueError("phase must be preflight or formal")
        self.initialize_manifest()
        self.write_preflight_manifest()
        allowed_bases = set(self.preflight_item_ids()) if phase == "preflight" else set(self.items)
        allowed_runs = {1} if phase == "preflight" else {1, 2, 3}
        units = sorted(
            {
                row["unit_id"]
                for row in self.plan
                if row["base_item_id"] in allowed_bases and row["run_id"] in allowed_runs
            }
        )
        attempted = skipped = 0
        workers = int(self.config["generation"]["max_concurrent_units"])
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(self._run_unit, unit, phase): unit for unit in units}
            for future in as_completed(futures):
                made, reused = future.result()
                attempted += made
                skipped += reused
        return {"units": len(units), "attempted": attempted, "skipped": skipped, "total_completed_file": len(self.completed)}
