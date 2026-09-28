"""Resumable TokenPlan/Command Code Judge scheduling and analysis support."""

from __future__ import annotations

import contextlib
import copy
import datetime as dt
import fcntl
import json
import os
import random
import re
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterator

import httpx

from cbm_drift_v2.common import (
    read_json,
    read_jsonl,
    sha256_file,
    sha256_json,
    write_json,
    write_jsonl,
)
from cbm_drift_v2.judge import _extract_json, validate_prediction
from cbm_drift_v2.prompts import JUDGE_DIRECT_SYSTEM, JUDGE_STRUCTURED_SYSTEM, judge_user_message

RUNNER_VERSION = "cbm_drift_v2.tokenplan_judge.1"
TRANSPORT_VERSION = "cbm_drift_v2.tokenplan_transport.4-httpx-sse"
RESULTS_RELATIVE = Path("results/judge_deepseek_v4_pro_v3")
INFRASTRUCTURE_ERROR_CODES = {301, 302, 303, 307, 308, 408, 425, 429, 500, 502, 503, 504}
AUTHORIZATION_ERROR_CODES = {401, 403}


def utc_now() -> str:
    """Return a stable UTC timestamp."""
    return dt.datetime.now(dt.timezone.utc).isoformat()


def atomic_write_json(path: Path, value: Any) -> None:
    """Atomically replace one JSON document in the destination directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _safe_filename(request_id: str) -> str:
    return sha256_json(request_id)[:32] + ".json"


def load_atomic_records(
    results: Path, queue: list[dict[str, Any]], fingerprint: str
) -> dict[str, dict[str, Any]]:
    """Load and verify per-request atomic records without requiring API credentials."""
    queue_ids = {row["judge_request_id"] for row in queue}
    completed: dict[str, dict[str, Any]] = {}
    for path in (results / "records").glob("*.json"):
        row = read_json(path)
        if row.get("experiment_fingerprint") != fingerprint:
            raise RuntimeError(f"Record fingerprint mismatch: {path}")
        request_id = row["judge_request_id"]
        if request_id not in queue_ids:
            raise RuntimeError(f"Unknown request record: {request_id}")
        if request_id in completed:
            raise RuntimeError(f"Duplicate request record: {request_id}")
        completed[request_id] = row
    return completed


def materialize_atomic_records(results: Path) -> dict[str, Any]:
    """Materialize deterministic JSONL and summary from crash-safe request files."""
    manifest = read_json(results / "experiment_manifest.json")
    queue = read_jsonl(results / "request_queue.jsonl")
    completed = load_atomic_records(results, queue, manifest["experiment_fingerprint"])
    ordered = [completed[row["judge_request_id"]] for row in queue if row["judge_request_id"] in completed]
    write_jsonl(results / "judge_outputs.jsonl", ordered)
    summary = {
        "expected_requests": len(queue),
        "completed_records": len(ordered),
        "remaining_requests": len(queue) - len(ordered),
        "api_success": sum(row["api_success"] for row in ordered),
        "parse_success": sum(row["parse_success"] for row in ordered),
        "schema_valid": sum(row["schema_valid"] for row in ordered),
        "truncated": sum(row.get("finish_reason") == "length" for row in ordered),
        "terminal_reasons": dict(sorted(Counter(
            row.get("terminal_reason") or "success" for row in ordered
        ).items())),
        "by_protocol": {
            protocol: sum(row["judge_protocol"] == protocol for row in ordered)
            for protocol in ("direct", "structured_assistance")
        },
        "preflight": {
            "expected": 24,
            "completed": sum(row["is_preflight"] for row in ordered),
        },
        "updated_at": utc_now(),
    }
    atomic_write_json(results / "progress_summary.json", summary)
    return summary


def _message_order(message_id: str) -> tuple[int, int, int]:
    match = re.search(r":t(\d+):r(\d+):agent_(\d+)$", message_id)
    if not match:
        raise ValueError(f"Unexpected MAD message ID: {message_id}")
    return tuple(int(value) for value in match.groups())


def build_paired_manifest(packages: list[dict[str, Any]], seed: int) -> list[dict[str, Any]]:
    """Select one message per base item, variant, and evidence stage without outcome filtering."""
    groups: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for package in packages:
        groups[(package["base_item_id"], package["variant_id"], int(package["evidence_stage"]))].append(package)
    if len(groups) != 180:
        raise ValueError(f"Expected 180 base-variant-stage groups, found {len(groups)}")

    base_ids = sorted({key[0] for key in groups})
    base_index = {value: index for index, value in enumerate(base_ids)}
    variant_type_index = {
        "clean_stay": 0,
        "evidence_update": 1,
        "irrelevant_noise": 2,
    }
    rows: list[dict[str, Any]] = []
    for key in sorted(groups):
        base_id, variant_id, stage = key
        candidates = sorted(groups[key], key=lambda row: _message_order(row["message_id"])[1:])
        if len(candidates) != 9:
            raise ValueError(f"{key} has {len(candidates)} messages instead of 9")
        variant_offset = variant_type_index[variant_id.split("::")[-1]]
        agent_index = (base_index[base_id] + variant_offset + stage + seed) % 3
        round_index = (base_index[base_id] + 2 * variant_offset + 2 * stage + seed) % 3
        selected = next(
            row for row in candidates
            if int(row["round"]) == round_index and row["agent_id"] == f"agent_{agent_index + 1}"
        )
        rows.append({
            "pair_sample_id": f"pair:{base_id}:{variant_id.split('::')[-1]}:t{stage}",
            "message_id": selected["message_id"],
            "package_id": selected["package_id"],
            "package_sha256": selected["package_sha256"],
            "base_item_id": base_id,
            "variant_id": variant_id,
            "trajectory_id": selected["trajectory_id"],
            "evidence_stage": stage,
            "round": selected["round"],
            "agent_id": selected["agent_id"],
            "selection_seed": seed,
            "selection_basis": "balanced deterministic Latin schedule; independent of model outcome and Judge label",
        })
    return rows


def build_preflight_manifest(
    paired: list[dict[str, Any]], packages: list[dict[str, Any]], seed: int
) -> list[dict[str, Any]]:
    """Select 12 paired messages spanning variants, stages, rounds, agents, and prompt lengths."""
    package_by_message = {row["message_id"]: row for row in packages}
    rng = random.Random(seed)
    candidates = copy.deepcopy(paired)
    rng.shuffle(candidates)
    lengths = {
        row["message_id"]: len(judge_user_message(package_by_message[row["message_id"]], structured=True))
        for row in candidates
    }
    chosen: list[dict[str, Any]] = []
    needed_variants = Counter({"clean_stay": 4, "evidence_update": 4, "irrelevant_noise": 4})
    needed_stages = Counter({1: 2, 2: 2, 3: 2, 4: 3, 5: 3})
    needed_rounds = Counter({0: 4, 1: 4, 2: 4})
    needed_agents = Counter({"agent_1": 4, "agent_2": 4, "agent_3": 4})

    def variant_type(row: dict[str, Any]) -> str:
        return row["variant_id"].split("::")[-1]

    while len(chosen) < 12:
        best: tuple[float, dict[str, Any]] | None = None
        for row in candidates:
            if row in chosen:
                continue
            score = (
                20 * max(needed_variants[variant_type(row)], 0)
                + 12 * max(needed_stages[int(row["evidence_stage"])], 0)
                + 8 * max(needed_rounds[int(row["round"])], 0)
                + 8 * max(needed_agents[row["agent_id"]], 0)
                + lengths[row["message_id"]] / 10000
            )
            tie = int(sha256_json([seed, row["message_id"]])[:8], 16) / 16**8
            candidate = (score + tie, row)
            if best is None or candidate[0] > best[0]:
                best = candidate
        if best is None:
            raise RuntimeError("Could not construct preflight manifest")
        row = best[1]
        chosen.append(row)
        needed_variants[variant_type(row)] -= 1
        needed_stages[int(row["evidence_stage"])] -= 1
        needed_rounds[int(row["round"])] -= 1
        needed_agents[row["agent_id"]] -= 1

    result = []
    ordered_lengths = sorted(lengths.values())
    for index, row in enumerate(sorted(chosen, key=lambda value: value["message_id"]), start=1):
        value = dict(row)
        length = lengths[row["message_id"]]
        value.update({
            "preflight_id": f"preflight_{index:02d}",
            "structured_prompt_characters": length,
            "context_length_band": (
                "short" if length <= ordered_lengths[len(ordered_lengths) // 3]
                else "long" if length >= ordered_lengths[2 * len(ordered_lengths) // 3]
                else "medium"
            ),
            "preflight_selection_seed": seed,
        })
        result.append(value)
    return result


def _protocol_messages(package: dict[str, Any], protocol: str) -> list[dict[str, str]]:
    structured = protocol == "structured_assistance"
    if protocol not in {"direct", "structured_assistance"}:
        raise ValueError(f"Unknown Judge protocol: {protocol}")
    return [
        {"role": "system", "content": JUDGE_STRUCTURED_SYSTEM if structured else JUDGE_DIRECT_SYSTEM},
        {"role": "user", "content": judge_user_message(package, structured=structured)},
    ]


def prepare_tokenplan_experiment(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    """Freeze paired/preflight manifests, request queue, and experiment fingerprint."""
    results = root / RESULTS_RELATIVE
    results.mkdir(parents=True, exist_ok=True)
    packages_path = root / "results/judge/judge_input_packages.jsonl"
    packages = read_jsonl(packages_path)
    if len(packages) != 1620 or len({row["message_id"] for row in packages}) != 1620:
        raise ValueError("Judge packages must contain 1620 unique messages")
    paired = build_paired_manifest(packages, int(config["paired_selection_seed"]))
    preflight = build_preflight_manifest(paired, packages, int(config["preflight_selection_seed"]))
    paired_ids = {row["message_id"] for row in paired}
    preflight_ids = {row["message_id"] for row in preflight}
    package_by_message = {row["message_id"]: row for row in packages}

    queue = []
    for package in packages:
        protocols = ["structured_assistance"] + (["direct"] if package["message_id"] in paired_ids else [])
        for protocol in protocols:
            messages = _protocol_messages(package, protocol)
            request_id = f"{protocol}:{package['message_id']}"
            queue.append({
                "judge_request_id": request_id,
                "message_id": package["message_id"],
                "package_id": package["package_id"],
                "package_sha256": package["package_sha256"],
                "base_item_id": package["base_item_id"],
                "variant_id": package["variant_id"],
                "trajectory_id": package["trajectory_id"],
                "evidence_stage": package["evidence_stage"],
                "round": package["round"],
                "agent_id": package["agent_id"],
                "judge_protocol": protocol,
                "is_paired_sample": package["message_id"] in paired_ids,
                "is_preflight": package["message_id"] in preflight_ids,
                "messages_sha256": sha256_json(messages),
                "input_sha256": sha256_json({"messages": messages, "package_sha256": package["package_sha256"]}),
            })
    if len(queue) != 1800 or len({row["judge_request_id"] for row in queue}) != 1800:
        raise ValueError("Expected exactly 1800 unique Judge requests")

    def queue_key(row: dict[str, Any]) -> tuple[Any, ...]:
        preflight_priority = 0 if row["is_preflight"] else 1
        protocol_priority = 0 if row["judge_protocol"] == "structured_assistance" else 1
        rotation = int(sha256_json([config["experiment_id"], row["base_item_id"]])[:8], 16)
        within = int(sha256_json([config["experiment_id"], row["judge_request_id"]])[:12], 16)
        return preflight_priority, rotation, protocol_priority, within

    queue.sort(key=queue_key)
    config_hash = sha256_json(config)
    manifest = {
        "experiment_id": config["experiment_id"],
        "runner_version": RUNNER_VERSION,
        "created_at": utc_now(),
        "config_sha256": config_hash,
        "config": config,
        "data": {
            "judge_packages_path": str(packages_path.relative_to(root)),
            "judge_packages_sha256": sha256_file(packages_path),
            "judge_packages_canonical_sha256": sha256_json(packages),
            "mad_outputs_sha256": sha256_file(root / "results/mad/raw_outputs.jsonl"),
            "program_diagnostics_sha256": sha256_file(root / "results/program/message_diagnostics.jsonl"),
        },
        "prompts": {
            "direct_system_sha256": sha256_json(JUDGE_DIRECT_SYSTEM),
            "structured_system_sha256": sha256_json(JUDGE_STRUCTURED_SYSTEM),
            "rendering_sha256": sha256_json([judge_user_message(row, structured=True) for row in packages]),
        },
        "inventory": {
            "packages": len(packages),
            "paired_messages": len(paired),
            "preflight_messages": len(preflight),
            "structured_requests": sum(row["judge_protocol"] == "structured_assistance" for row in queue),
            "direct_requests": sum(row["judge_protocol"] == "direct" for row in queue),
            "total_requests": len(queue),
        },
        "credential_storage": "environment variable only; secret not persisted",
    }
    manifest["experiment_fingerprint"] = sha256_json({key: value for key, value in manifest.items() if key not in {"created_at"}})

    frozen = {
        results / "experiment_manifest.json": manifest,
        results / "paired_sample_manifest.jsonl": paired,
        results / "preflight_manifest.jsonl": preflight,
        results / "request_queue.jsonl": queue,
    }
    for path, value in frozen.items():
        if path.exists():
            existing = read_json(path) if path.suffix == ".json" else read_jsonl(path)
            if path.name == "experiment_manifest.json":
                existing = {key: val for key, val in existing.items() if key != "created_at"}
                comparison = {key: val for key, val in value.items() if key != "created_at"}
            else:
                comparison = value
            if existing != comparison:
                raise RuntimeError(f"Frozen artifact differs: {path}")
        elif path.suffix == ".json":
            atomic_write_json(path, value)
        else:
            write_jsonl(path, value)
    return manifest


@contextlib.contextmanager
def scheduler_lock(path: Path) -> Iterator[None]:
    """Prevent duplicate dispatch with a crash-releasing kernel file lock."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            os.lseek(descriptor, 0, os.SEEK_SET)
            owner = os.read(descriptor, 4096).decode("utf-8", errors="replace") or "unknown"
            raise RuntimeError(f"Judge scheduler is already locked: {owner}") from exc
        os.ftruncate(descriptor, 0)
        os.write(descriptor, json.dumps({"pid": os.getpid(), "started_at": utc_now()}).encode("utf-8"))
        os.fsync(descriptor)
        yield
    finally:
        with contextlib.suppress(OSError):
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def _retry_after(headers: Any) -> float | None:
    raw = headers.get("Retry-After") if headers else None
    if raw is None:
        return None
    try:
        return max(float(raw), 0.0)
    except ValueError:
        return None


def _safe_headers(headers: Any) -> dict[str, str]:
    if not headers:
        return {}
    allowed = {
        "x-request-id", "request-id", "retry-after", "x-ratelimit-limit-requests",
        "x-ratelimit-remaining-requests", "x-ratelimit-reset-requests",
        "x-ratelimit-limit-tokens", "x-ratelimit-remaining-tokens", "x-ratelimit-reset-tokens",
        "location",
    }
    return {key.lower(): value for key, value in headers.items() if key.lower() in allowed}


def _decode_error_body(text: str) -> Any:
    """Decode an HTTP error body without retaining an unbounded gateway page."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text[:2000]


def _new_stream_accumulator() -> dict[str, Any]:
    """Create mutable state for one OpenAI-compatible SSE response."""
    return {
        "content_parts": [],
        "reasoning_parts": [],
        "delta_key_counts": {},
        "finish_reason": None,
        "usage": None,
        "response_id": None,
        "model": None,
        "system_fingerprint": None,
        "data_events": 0,
        "done_received": False,
    }


def _consume_sse_line(accumulator: dict[str, Any], line: str) -> None:
    """Consume one SSE line while retaining final text and usage metadata."""
    stripped = line.strip()
    if not stripped or stripped.startswith(":"):
        return
    if not stripped.startswith("data:"):
        raise ValueError(f"Unexpected SSE line prefix: {stripped[:80]}")
    data = stripped[5:].strip()
    if data == "[DONE]":
        accumulator["done_received"] = True
        return
    chunk = json.loads(data)
    accumulator["data_events"] += 1
    for key in ("id", "model", "system_fingerprint"):
        if chunk.get(key) is not None:
            target = "response_id" if key == "id" else key
            accumulator[target] = chunk[key]
    if chunk.get("usage") is not None:
        accumulator["usage"] = chunk["usage"]
    choices = chunk.get("choices") or []
    if not choices:
        return
    choice = choices[0]
    delta = choice.get("delta") or {}
    for key in delta:
        accumulator["delta_key_counts"][key] = accumulator["delta_key_counts"].get(key, 0) + 1
    if delta.get("content"):
        accumulator["content_parts"].append(delta["content"])
    if delta.get("reasoning_content"):
        accumulator["reasoning_parts"].append(delta["reasoning_content"])
    if delta.get("reasoning"):
        accumulator["reasoning_parts"].append(delta["reasoning"])
    if choice.get("finish_reason") is not None:
        accumulator["finish_reason"] = choice["finish_reason"]


def _stream_body(accumulator: dict[str, Any]) -> dict[str, Any]:
    """Convert accumulated SSE chunks into the non-stream response shape used downstream."""
    return {
        "id": accumulator["response_id"],
        "model": accumulator["model"],
        "system_fingerprint": accumulator["system_fingerprint"],
        "choices": [{
            "message": {
                "content": "".join(accumulator["content_parts"]),
                "reasoning_content": "".join(accumulator["reasoning_parts"]),
            },
            "finish_reason": accumulator["finish_reason"],
        }],
        "usage": accumulator["usage"],
    }


def _is_quota_error(status: int | None, body: Any) -> bool:
    text = json.dumps(body, ensure_ascii=False).lower() if not isinstance(body, str) else body.lower()
    return status == 429 and any(token in text for token in ("usage", "quota", "credit", "limit", "reset"))


def _retryable_record(row: dict[str, Any]) -> bool:
    """Return whether a stored logical judgment ended only in infrastructure failure."""
    if row.get("api_success"):
        return False
    if "retryable_after_run" in row:
        return bool(row["retryable_after_run"])
    attempts = row.get("attempts") or []
    return any(
        attempt.get("status") == "infrastructure_error"
        or attempt.get("http_status") in INFRASTRUCTURE_ERROR_CODES
        or (
            attempt.get("http_status") == 404
            and "GET " in json.dumps(attempt.get("error_body"), ensure_ascii=False)
        )
        for attempt in attempts
    )


class TokenPlanJudgeRunner:
    """Execute a frozen queue with atomic records and conservative quota windows."""

    def __init__(self, root: Path, config: dict[str, Any]) -> None:
        self.root = root
        self.results = root / RESULTS_RELATIVE
        self.config = config
        self.manifest = read_json(self.results / "experiment_manifest.json")
        if sha256_json(config) != self.manifest["config_sha256"]:
            raise RuntimeError("TokenPlan Judge config fingerprint mismatch")
        self.fingerprint = self.manifest["experiment_fingerprint"]
        self.packages = {
            row["message_id"]: row for row in read_jsonl(root / "results/judge/judge_input_packages.jsonl")
        }
        self.queue = read_jsonl(self.results / "request_queue.jsonl")
        self.records_dir = self.results / "records"
        self.records_dir.mkdir(parents=True, exist_ok=True)
        self.key = os.environ.get(str(config["api_key_env"]))
        if not self.key:
            raise RuntimeError(f"Missing required environment variable: {config['api_key_env']}")
        timeout = float(config["request_timeout_seconds"])
        self.client = httpx.Client(
            follow_redirects=False,
            timeout=httpx.Timeout(timeout, connect=min(timeout, 30.0), write=min(timeout, 60.0)),
            limits=httpx.Limits(max_connections=1, max_keepalive_connections=1),
            headers={
                "Authorization": f"Bearer {self.key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": f"cbm-drift-diagnostic/{RUNNER_VERSION}",
            },
        )

    def _record_path(self, request_id: str) -> Path:
        return self.records_dir / _safe_filename(request_id)

    def _completed(self) -> dict[str, dict[str, Any]]:
        return load_atomic_records(self.results, self.queue, self.fingerprint)

    def _window_state(self) -> dict[str, Any]:
        path = self.results / "scheduler_state.json"
        state = read_json(path) if path.exists() else {
            "window_started_at": None,
            "window_started_epoch": None,
            "attempts_started_in_window": 0,
            "next_eligible_at": None,
            "status": "ready",
            "in_flight": [],
            "last_updated_at": utc_now(),
        }
        now = time.time()
        start = state.get("window_started_epoch")
        if start is not None and now >= float(start) + float(self.config["quota"]["window_seconds"]):
            state.update({
                "window_started_at": None, "window_started_epoch": None,
                "attempts_started_in_window": 0, "next_eligible_at": None, "status": "ready",
            })
        return state

    def _save_state(self, state: dict[str, Any]) -> None:
        state["last_updated_at"] = utc_now()
        atomic_write_json(self.results / "scheduler_state.json", state)

    def _call(
        self, job: dict[str, Any], state: dict[str, Any], prior_record: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        package = self.packages[job["message_id"]]
        messages = _protocol_messages(package, job["judge_protocol"])
        payload = {
            "model": self.config["model_name"],
            "messages": messages,
            "max_tokens": self.config["max_tokens"],
            "response_format": self.config["response_format"],
            "thinking": self.config["thinking"],
            "reasoning_effort": self.config["reasoning_effort"],
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        if sha256_json(messages) != job["messages_sha256"]:
            raise RuntimeError(f"Prompt changed after queue freeze: {job['judge_request_id']}")
        url = self.config["base_url"].rstrip("/") + self.config["endpoint"]
        attempts: list[dict[str, Any]] = []
        response_body: dict[str, Any] | None = None
        partial_stream_body: dict[str, Any] | None = None
        stream_metadata: dict[str, Any] = {
            "enabled": True, "data_events": 0, "done_received": False,
        }
        response_headers: dict[str, str] = {}
        started = time.monotonic()
        terminal_reason = None
        for attempt_index in range(int(self.config["max_infrastructure_retries"]) + 1):
            cap = int(self.config["quota"]["max_attempts_per_unknown_window"])
            if int(state["attempts_started_in_window"]) >= cap:
                terminal_reason = "retry_deferred_quota_window"
                break
            state["attempts_started_in_window"] += 1
            self._save_state(state)
            attempt_started = utc_now()
            try:
                with self.client.stream("POST", url, json=payload) as response:
                    response_headers = _safe_headers(response.headers)
                    if response.status_code != 200:
                        response.read()
                        body = _decode_error_body(response.text)
                        attempts.append({
                            "attempt": attempt_index + 1, "started_at": attempt_started,
                            "status": "http_error", "http_status": response.status_code,
                            "http_version": response.http_version,
                            "response_headers": response_headers, "error_body": body,
                        })
                        if response.status_code in AUTHORIZATION_ERROR_CODES:
                            terminal_reason = "authentication_or_permission_error"
                            break
                        if _is_quota_error(response.status_code, body):
                            terminal_reason = "quota_exhausted"
                            wait = _retry_after(response.headers)
                            if wait is not None:
                                state["next_eligible_at"] = (
                                    dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=wait + 30)
                                ).isoformat()
                            break
                        if (
                            response.status_code not in INFRASTRUCTURE_ERROR_CODES
                            or attempt_index >= int(self.config["max_infrastructure_retries"])
                        ):
                            terminal_reason = (
                                "infrastructure_error"
                                if response.status_code in INFRASTRUCTURE_ERROR_CODES
                                else "http_error"
                            )
                            break
                        wait = _retry_after(response.headers)
                        time.sleep(
                            wait if wait is not None
                            else float(self.config["initial_retry_seconds"]) * 2**attempt_index
                        )
                        continue

                    accumulator = _new_stream_accumulator()
                    try:
                        for line in response.iter_lines():
                            _consume_sse_line(accumulator, line)
                    except (httpx.TimeoutException, httpx.TransportError, json.JSONDecodeError, ValueError) as exc:
                        partial_stream_body = _stream_body(accumulator)
                        stream_metadata = {
                            "enabled": True,
                            "data_events": accumulator["data_events"],
                            "done_received": accumulator["done_received"],
                            "delta_key_counts": accumulator["delta_key_counts"],
                        }
                        attempts.append({
                            "attempt": attempt_index + 1, "started_at": attempt_started,
                            "status": "stream_interrupted", "http_status": 200,
                            "http_version": response.http_version,
                            "response_headers": response_headers,
                            "error_type": type(exc).__name__, "error_message": str(exc)[:1000],
                            "completion_state": "unknown",
                            **stream_metadata,
                        })
                        terminal_reason = "stream_interrupted"
                        break

                    stream_metadata = {
                        "enabled": True,
                        "data_events": accumulator["data_events"],
                        "done_received": accumulator["done_received"],
                        "delta_key_counts": accumulator["delta_key_counts"],
                    }
                    if accumulator["finish_reason"] is None:
                        partial_stream_body = _stream_body(accumulator)
                        attempts.append({
                            "attempt": attempt_index + 1, "started_at": attempt_started,
                            "status": "stream_incomplete", "http_status": 200,
                            "http_version": response.http_version,
                            "response_headers": response_headers,
                            "completion_state": "unknown",
                            **stream_metadata,
                        })
                        terminal_reason = "stream_interrupted"
                        break
                    response_body = _stream_body(accumulator)
                    attempts.append({
                        "attempt": attempt_index + 1, "started_at": attempt_started,
                        "status": "success", "http_status": 200,
                        "http_version": response.http_version,
                        "response_headers": response_headers,
                        **stream_metadata,
                    })
                    break
            except (httpx.TimeoutException, httpx.TransportError, json.JSONDecodeError) as exc:
                attempts.append({
                    "attempt": attempt_index + 1, "started_at": attempt_started,
                    "status": "infrastructure_error", "error_type": type(exc).__name__,
                    "error_message": str(exc)[:1000],
                    "completion_state": "unknown" if isinstance(exc, httpx.TimeoutException) else "not_confirmed",
                })
                if attempt_index >= int(self.config["max_infrastructure_retries"]):
                    terminal_reason = "infrastructure_error"
                    break
                time.sleep(float(self.config["initial_retry_seconds"]) * 2**attempt_index)

        api_success = response_body is not None
        choice = response_body.get("choices", [{}])[0] if api_success else {}
        message = choice.get("message") or {}
        content = message.get("content") or ""
        reasoning_content = message.get("reasoning_content") or ""
        parsed, parse_source = _extract_json(content) if api_success else (None, "api_failure")
        checked = validate_prediction(parsed, package)
        retryable_after_run = not api_success and terminal_reason in {
            "infrastructure_error", "retry_deferred_quota_window"
        }
        return {
            **job,
            "experiment_id": self.config["experiment_id"],
            "experiment_fingerprint": self.fingerprint,
            "runner_version": RUNNER_VERSION,
            "transport_version": TRANSPORT_VERSION,
            "requested_model": self.config["model_name"],
            "response_model": response_body.get("model") if api_success else None,
            "response_id": response_body.get("id") if api_success else None,
            "request_payload": payload,
            "request_configuration": {
                "thinking": self.config["thinking"],
                "reasoning_effort": self.config["reasoning_effort"],
                "max_tokens": self.config["max_tokens"],
                "temperature_sent": False,
                "top_p_sent": False,
                "tools_sent": False,
                "delivery_mode": "server_sent_events",
            },
            "api_success": api_success,
            "terminal_reason": terminal_reason,
            "retryable_after_run": retryable_after_run,
            "prior_attempt_batches": (
                (prior_record.get("prior_attempt_batches") or [])
                + [{
                    "completed_at": prior_record.get("completed_at"),
                    "terminal_reason": prior_record.get("terminal_reason"),
                    "attempts": prior_record.get("attempts") or [],
                }]
                if prior_record else []
            ),
            "attempts": attempts,
            "attempt_count": len(attempts),
            "response_headers": response_headers,
            "raw_response": content or (
                ((partial_stream_body or {}).get("choices") or [{}])[0]
                .get("message", {}).get("content", "")
            ),
            "reasoning_content": reasoning_content or (
                ((partial_stream_body or {}).get("choices") or [{}])[0]
                .get("message", {}).get("reasoning_content", "")
            ),
            "stream_metadata": stream_metadata,
            "parse_source": parse_source,
            "parse_success": parsed is not None,
            "schema_valid": checked["schema_valid"],
            "validation_errors": checked["validation_errors"],
            "normalization_actions": checked["normalization_actions"],
            "prediction": checked["normalized"],
            "finish_reason": choice.get("finish_reason"),
            "usage": response_body.get("usage") if api_success else None,
            "system_fingerprint": response_body.get("system_fingerprint") if api_success else None,
            "latency_seconds": round(time.monotonic() - started, 4),
            "completed_at": utc_now(),
        }

    def materialize(self) -> dict[str, Any]:
        """Create deterministic JSONL and a progress summary from atomic records."""
        return materialize_atomic_records(self.results)

    def run(self, phase: str, max_new: int | None = None) -> dict[str, Any]:
        """Run preflight or formal jobs while respecting the persisted unknown-quota window cap."""
        if phase not in {"preflight", "formal"}:
            raise ValueError("phase must be preflight or formal")
        with scheduler_lock(self.results / "scheduler.lock"):
            completed = self._completed()
            state = self._window_state()
            now = dt.datetime.now(dt.timezone.utc)
            next_at = state.get("next_eligible_at")
            if next_at and now < dt.datetime.fromisoformat(next_at):
                state["status"] = "waiting_for_quota_window"
                self._save_state(state)
                return self.materialize()
            if state["window_started_epoch"] is None:
                state["window_started_epoch"] = time.time()
                state["window_started_at"] = utc_now()
            cap = int(self.config["quota"]["max_attempts_per_unknown_window"])
            available = max(cap - int(state["attempts_started_in_window"]), 0)
            jobs = [
                row for row in self.queue
                if (
                    row["judge_request_id"] not in completed
                    or _retryable_record(completed[row["judge_request_id"]])
                )
                and ((phase == "preflight" and row["is_preflight"]) or phase == "formal")
            ]
            if max_new is not None:
                jobs = jobs[:max_new]
            jobs = jobs[:available]
            consecutive_infrastructure_errors = 0
            last_start = 0.0
            for job in jobs:
                if (self.results / "STOP").exists():
                    state["status"] = "stopped_by_user"
                    self._save_state(state)
                    break
                elapsed = time.monotonic() - last_start
                delay = float(self.config["minimum_request_start_interval_seconds"]) - elapsed
                if last_start and delay > 0:
                    time.sleep(delay)
                state["in_flight"] = [job["judge_request_id"]]
                state["status"] = "running"
                self._save_state(state)
                last_start = time.monotonic()
                row = self._call(job, state, completed.get(job["judge_request_id"]))
                atomic_write_json(self._record_path(job["judge_request_id"]), row)
                completed[job["judge_request_id"]] = row
                state["in_flight"] = []
                if row["api_success"]:
                    consecutive_infrastructure_errors = 0
                else:
                    consecutive_infrastructure_errors += 1
                if row.get("terminal_reason") in {"authentication_or_permission_error", "quota_exhausted"}:
                    state["status"] = row["terminal_reason"]
                    if row["terminal_reason"] == "quota_exhausted" and not state.get("next_eligible_at"):
                        state["next_eligible_at"] = (
                            dt.datetime.now(dt.timezone.utc)
                            + dt.timedelta(seconds=float(self.config["quota"]["window_seconds"]) + 30)
                        ).isoformat()
                    self._save_state(state)
                    break
                if consecutive_infrastructure_errors >= 5:
                    state["status"] = "paused_after_five_infrastructure_errors"
                    self._save_state(state)
                    break
                if state["attempts_started_in_window"] >= cap:
                    break
                self._save_state(state)
            if state["attempts_started_in_window"] >= cap:
                state["status"] = "waiting_for_unknown_quota_window"
                state["next_eligible_at"] = (
                    dt.datetime.fromtimestamp(float(state["window_started_epoch"]), dt.timezone.utc)
                    + dt.timedelta(seconds=float(self.config["quota"]["window_seconds"]) + 30)
                ).isoformat()
            elif state["status"] == "running":
                state["status"] = "ready"
            self._save_state(state)
            return self.materialize()


def validate_preflight(root: Path) -> dict[str, Any]:
    """Audit protocol coverage, output budget, parsing, and quote/object mapping."""
    results = root / RESULTS_RELATIVE
    manifest = read_jsonl(results / "preflight_manifest.jsonl")
    ids = {row["message_id"] for row in manifest}
    outputs = [row for row in read_jsonl(results / "judge_outputs.jsonl") if row["message_id"] in ids]
    errors = []
    if len(manifest) != 12 or len(ids) != 12:
        errors.append("preflight manifest is not 12 unique messages")
    request_ids = {row["judge_request_id"] for row in outputs}
    expected = {f"{protocol}:{message_id}" for message_id in ids for protocol in ("direct", "structured_assistance")}
    if request_ids != expected:
        errors.append("preflight protocol coverage mismatch")
    api_success = sum(row["api_success"] for row in outputs)
    parse_success = sum(row["parse_success"] for row in outputs)
    schema_valid = sum(row["schema_valid"] for row in outputs)
    truncated = sum(row.get("finish_reason") == "length" for row in outputs)
    empty_final_content = sum(row["api_success"] and not row.get("raw_response") for row in outputs)
    result = {
        "passed": (
            not errors
            and len(outputs) == 24
            and api_success == 24
            and parse_success == 24
            and schema_valid == 24
            and truncated == 0
            and empty_final_content == 0
        ),
        "errors": errors,
        "messages": len(manifest),
        "requests": len(outputs),
        "api_success": api_success,
        "parse_success": parse_success,
        "schema_valid": schema_valid,
        "truncated": truncated,
        "reasoning_content_present": sum(bool(row.get("reasoning_content")) for row in outputs),
        "empty_final_content": empty_final_content,
        "finish_reasons": dict(sorted(
            Counter(str(row.get("finish_reason")) for row in outputs).items()
        )),
        "response_models": dict(sorted(
            Counter(str(row.get("response_model")) for row in outputs).items()
        )),
        "usage": {
            "prompt_tokens": sum((row.get("usage") or {}).get("prompt_tokens", 0) for row in outputs),
            "completion_tokens": sum((row.get("usage") or {}).get("completion_tokens", 0) for row in outputs),
            "reasoning_tokens": sum(
                ((row.get("usage") or {}).get("completion_tokens_details") or {}).get("reasoning_tokens", 0)
                for row in outputs
            ),
        },
    }
    atomic_write_json(results / "preflight_validation.json", result)
    return result
