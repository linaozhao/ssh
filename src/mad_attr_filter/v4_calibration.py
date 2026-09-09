"""Execution support for v4.1 single-agent difficulty calibration."""

from __future__ import annotations

import hashlib
import json
import re
import urllib.error
import urllib.request
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mad_attr_filter.io import read_jsonl
from mad_attr_filter.single_agent import call_with_retries, model_alias
from mad_attr_filter.v4_validation import validate_v4_pool

VALID_OPTIONS = ("A", "B", "C", "D")
PROTOCOL_VERSION = "v4.1-calibration-1"
PARSER_REVISION = "v4.1-answer-parser-2"

PROMPT_TEMPLATE = """Solve the following multiple-choice problem independently.

Carefully evaluate every stated requirement and determine which candidate satisfies all of them.

Provide your answer and a concise explanation of your reasoning.

Return only valid JSON in the following format:

{{
  "answer": "A",
  "reasoning": "Briefly explain how you checked the relevant requirements.",
  "confidence": 0.85
}}

Rules:
- "answer" must be exactly one of A, B, C, or D.
- "confidence" must be a number between 0 and 1.
- Do not use Markdown.
- Do not refer to other agents.
- Solve the problem independently.

Problem:

{question}
"""


class CalibrationError(ValueError):
    """Raised when a calibration artifact violates the frozen protocol."""


def build_prompt(question: str) -> str:
    """Build a prompt containing only the natural-language problem."""
    return PROMPT_TEMPLATE.format(question=question)


def sha256_bytes(content: bytes) -> str:
    """Return a SHA-256 hexadecimal digest."""
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: str | Path) -> str:
    """Hash a file exactly as stored on disk."""
    return sha256_bytes(Path(path).read_bytes())


def canonical_hash(value: Any) -> str:
    """Hash JSON-compatible data using a stable serialization."""
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256_bytes(encoded)


def public_config(config: Mapping[str, Any]) -> dict[str, Any]:
    """Return a manifest-safe configuration without API secrets."""
    result = dict(config)
    result["models"] = []
    for model in config.get("models", []):
        public_model = dict(model)
        public_model.pop("api_key", None)
        result["models"].append(public_model)
    return result


def build_fingerprints(
    dataset_path: str | Path,
    config: Mapping[str, Any],
) -> dict[str, str]:
    """Build the dataset, configuration, prompt, and aggregate fingerprints."""
    config_hash = canonical_hash(public_config(config))
    fingerprints = {
        "dataset_sha256": sha256_file(dataset_path),
        "config_sha256": config_hash,
        "prompt_sha256": sha256_bytes(PROMPT_TEMPLATE.encode("utf-8")),
        "protocol_version": PROTOCOL_VERSION,
    }
    fingerprints["experiment_sha256"] = canonical_hash(fingerprints)
    return fingerprints


def _normalize_answer(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip().upper()
    if text in VALID_OPTIONS:
        return text
    match = re.fullmatch(r"(?:OPTION|CANDIDATE)\s+([ABCD])[.]?", text)
    return match.group(1) if match else None


def _find_json_objects(text: str) -> list[str]:
    """Extract balanced JSON-object candidates without interpreting prose."""
    objects: list[str] = []
    start: int | None = None
    depth = 0
    in_string = False
    escaped = False
    for index, char in enumerate(text):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            if depth == 0:
                start = index
            depth += 1
        elif char == "}" and depth:
            depth -= 1
            if depth == 0 and start is not None:
                objects.append(text[start : index + 1])
                start = None
    return objects


def _confidence(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if 0.0 <= number <= 1.0 else None


def _json_payload(parsed: Any) -> dict[str, Any] | None:
    if not isinstance(parsed, Mapping):
        return None
    answer = _normalize_answer(parsed.get("answer"))
    reasoning = parsed.get("reasoning")
    confidence = _confidence(parsed.get("confidence"))
    return {
        "answer": answer,
        "reasoning": reasoning if isinstance(reasoning, str) else "",
        "confidence": confidence,
        "json_compliant": bool(
            answer is not None
            and isinstance(reasoning, str)
            and confidence is not None
            and set(parsed) >= {"answer", "reasoning", "confidence"}
        ),
    }


def _explicit_final_answers(text: str) -> list[str]:
    """Find explicit final-answer claims, never generic option mentions."""
    patterns = (
        r"(?im)^\s*(?:FINAL\s+ANSWER|ANSWER|SELECTED\s+ANSWER)\s*[:=\-]\s*"
        r"(?:OPTION\s+|CANDIDATE\s+)?([ABCD])\b",
        r"(?im)^\s*THE\s+FINAL\s+ANSWER\s+IS\s+(?:OPTION\s+|CANDIDATE\s+)?([ABCD])\b",
    )
    answers: list[str] = []
    for pattern in patterns:
        answers.extend(match.upper() for match in re.findall(pattern, text))
    return answers


def _malformed_json_answer_fields(text: str) -> list[str]:
    """Extract only exact A-D values from explicit JSON answer fields."""
    return [
        match.upper()
        for match in re.findall(r'"answer"\s*:\s*"([ABCD])"', text, flags=re.IGNORECASE)
    ]


def parse_calibration_response(raw_response: str) -> dict[str, Any]:
    """Parse a response while separating answer recovery from JSON compliance.

    A missing confidence can make JSON noncompliant without hiding a clear
    answer. Text fallback accepts only bare labels or explicit final-answer
    declarations. Conflicting declarations are deliberately left unresolved.
    """
    stripped = raw_response.strip()
    result: dict[str, Any] = {
        "answer": None,
        "reasoning": "",
        "confidence": None,
        "answer_extractable": False,
        "json_compliant": False,
        "strict_json_syntax": False,
        "parse_source": "none",
        "fallback_used": False,
        "ambiguous_answer": False,
        "answer_candidates": [],
        "parse_error": None,
    }

    try:
        strict = json.loads(stripped)
    except json.JSONDecodeError:
        strict = None
    else:
        result["strict_json_syntax"] = True
        payload = _json_payload(strict)
        if payload is not None and payload["answer"] is not None:
            result.update(payload)
            result["answer_extractable"] = True
            result["parse_source"] = "strict_json"
            if not payload["json_compliant"]:
                result["parse_error"] = "JSON object is missing or has an invalid required field"
            return result
        result["parse_error"] = "Strict JSON does not contain an unambiguous valid answer"

    json_candidates: list[tuple[str, dict[str, Any]]] = []
    for json_text in _find_json_objects(raw_response):
        try:
            parsed = json.loads(json_text)
        except json.JSONDecodeError:
            continue
        payload = _json_payload(parsed)
        if payload is not None and payload["answer"] is not None:
            json_candidates.append((str(payload["answer"]), payload))

    explicit = _explicit_final_answers(raw_response)
    if stripped.upper() in VALID_OPTIONS:
        explicit.append(stripped.upper())
    malformed_json_answers = _malformed_json_answer_fields(raw_response)
    candidates = [answer for answer, _ in json_candidates] + explicit + malformed_json_answers
    unique = sorted(set(candidates))
    result["answer_candidates"] = unique
    if len(unique) > 1:
        result["ambiguous_answer"] = True
        result["parse_source"] = "conflicting_answers"
        result["parse_error"] = "Conflicting explicit answers were found"
        return result
    if len(unique) == 1:
        answer = unique[0]
        result["answer"] = answer
        result["answer_extractable"] = True
        result["fallback_used"] = True
        matching_json = [payload for candidate, payload in json_candidates if candidate == answer]
        if matching_json:
            payload = matching_json[0]
            result["reasoning"] = payload["reasoning"]
            result["confidence"] = payload["confidence"]
            result["parse_source"] = "embedded_json"
        elif stripped.upper() == answer:
            result["parse_source"] = "bare_answer"
        elif malformed_json_answers:
            result["parse_source"] = "malformed_json_answer_field"
        else:
            result["parse_source"] = "explicit_final_answer"
        result["parse_error"] = "Answer recovered from noncompliant output"
        return result

    result["parse_error"] = result["parse_error"] or "No unambiguous final answer found"
    return result


def select_preflight_items(samples: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Select exactly one deterministic item from each difficulty cell."""
    by_cell: dict[str, list[Mapping[str, Any]]] = {}
    for sample in samples:
        cell = str(sample.get("metadata", {}).get("difficulty_cell", ""))
        if not cell:
            raise CalibrationError(f"{sample.get('item_id')} has no metadata.difficulty_cell")
        by_cell.setdefault(cell, []).append(sample)
    if len(by_cell) != 18:
        raise CalibrationError(f"Expected 18 difficulty cells, found {len(by_cell)}")
    selected = [min(items, key=lambda item: str(item["item_id"])) for _, items in sorted(by_cell.items())]
    return [dict(item) for item in selected]


def preflight_manifest_records(samples: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Build the human-auditable stratified preflight manifest."""
    return [
        {
            "selection_index": index,
            "item_id": sample["item_id"],
            "difficulty_cell": sample["metadata"]["difficulty_cell"],
            "difficulty_factors": sample["difficulty_factors"],
            "scenario": sample["scenario"],
        }
        for index, sample in enumerate(samples, start=1)
    ]


def make_experiment_manifest(
    *,
    dataset_path: str | Path,
    samples: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
    fingerprints: Mapping[str, str],
) -> dict[str, Any]:
    """Create a frozen manifest for the calibration protocol."""
    validation = validate_v4_pool(samples, expected_items_per_cell=10)
    models = []
    for model in config["models"]:
        models.append(
            {
                "alias": model_alias(model),
                "model_name": model["model_name"],
                "base_url": model["base_url"],
                "thinking_enabled": bool(model.get("thinking_enabled", False)),
                "deployment": dict(model.get("deployment", {})),
            }
        )
    return {
        "experiment_id": config["experiment_id"],
        "protocol_version": PROTOCOL_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_path": str(dataset_path),
        "dataset_validation": validation,
        "fingerprints": dict(fingerprints),
        "models": models,
        "generation_parameters": {
            "temperature": config["temperature"],
            "top_p": config["top_p"],
            "max_tokens": config["max_tokens"],
            "seeds": list(config["seeds"]),
            "max_concurrent_requests": config.get("max_concurrent_requests", 1),
        },
        "expected": {
            "items": len(samples),
            "preflight_items": 18,
            "preflight_runs": 18 * len(models) * len(config["seeds"]),
            "formal_runs": len(samples) * len(models) * len(config["seeds"]),
            "item_model_records": len(samples) * len(models),
            "cell_model_rows": 18 * len(models),
        },
        "prompt_template": PROMPT_TEMPLATE,
        "status": {"preflight": "pending", "formal": "pending", "analysis": "pending"},
    }


def probe_model_services(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Query model and backend identity from each configured endpoint."""
    observations: list[dict[str, Any]] = []
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    for model in config["models"]:
        base_url = str(model["base_url"]).rstrip("/")
        observation: dict[str, Any] = {
            "alias": model_alias(model),
            "configured_model_name": model["model_name"],
            "base_url": base_url,
            "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        try:
            with opener.open(f"{base_url}/models", timeout=10) as response:
                models_payload = json.loads(response.read().decode("utf-8"))
            root_url = base_url.removesuffix("/v1")
            with opener.open(f"{root_url}/version", timeout=10) as response:
                version_payload = json.loads(response.read().decode("utf-8"))
            observation["available_model_ids"] = [
                entry.get("id") for entry in models_payload.get("data", [])
            ]
            observation["backend_version"] = version_payload
            observation["probe_success"] = True
            observation["probe_error"] = None
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            observation["available_model_ids"] = []
            observation["backend_version"] = None
            observation["probe_success"] = False
            observation["probe_error"] = f"{type(exc).__name__}: {exc}"
        observations.append(observation)
    return observations


def assert_manifest_compatible(
    existing: Mapping[str, Any],
    fingerprints: Mapping[str, str],
    experiment_id: str,
) -> None:
    """Reject resume when frozen inputs or protocol differ."""
    if existing.get("experiment_id") != experiment_id:
        raise CalibrationError("Experiment ID differs from the existing manifest")
    if existing.get("fingerprints") != dict(fingerprints):
        raise CalibrationError("Dataset, config, prompt, or protocol fingerprint changed")


def expected_keys(
    samples: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
) -> set[tuple[str, str, int]]:
    """Return all expected item/model/run keys."""
    return {
        (str(sample["item_id"]), model_alias(model), run_id)
        for sample in samples
        for model in config["models"]
        for run_id, _ in enumerate(config["seeds"], start=1)
    }


def audit_existing_records(
    path: str | Path,
    allowed_keys: set[tuple[str, str, int]],
    experiment_fingerprint: str,
) -> tuple[list[dict[str, Any]], set[tuple[str, str, int]]]:
    """Audit a resumable JSONL file for duplicates, unknown keys, and drift."""
    output_path = Path(path)
    if not output_path.exists():
        return [], set()
    records = read_jsonl(output_path)
    completed: set[tuple[str, str, int]] = set()
    for record in records:
        key = (
            str(record.get("item_id")),
            str(record.get("model_alias")),
            int(record.get("run_id", 0)),
        )
        if key not in allowed_keys:
            raise CalibrationError(f"Unexpected completed key in {path}: {key}")
        if key in completed:
            raise CalibrationError(f"Duplicate completed key in {path}: {key}")
        if record.get("experiment_fingerprint") != experiment_fingerprint:
            raise CalibrationError(f"Fingerprint mismatch in {path}: {key}")
        completed.add(key)
    return records, completed


def build_output_record(
    *,
    sample: Mapping[str, Any],
    model_config: Mapping[str, Any],
    run_id: int,
    seed: int,
    generation_config: Mapping[str, Any],
    experiment_id: str,
    experiment_fingerprint: str,
    raw_response: str,
    api_metadata: Mapping[str, Any],
    request_error: str | None,
    phase: str,
    reused_from_preflight: bool = False,
) -> dict[str, Any]:
    """Build one v4.1 calibration output without v3 compatibility fields."""
    if request_error is None:
        parsed = parse_calibration_response(raw_response)
    else:
        parsed = {
            "answer": None,
            "reasoning": "",
            "confidence": None,
            "answer_extractable": False,
            "json_compliant": False,
            "strict_json_syntax": False,
            "parse_source": "request_error",
            "fallback_used": False,
            "ambiguous_answer": False,
            "answer_candidates": [],
            "parse_error": request_error,
        }
    answer = parsed["answer"]
    gold_answer = str(sample["gold_answer"])
    valid_answer = answer in VALID_OPTIONS
    signature = (
        list(sample["option_violation_signature"].get(str(answer), []))
        if valid_answer
        else []
    )
    usage = api_metadata.get("usage") if isinstance(api_metadata.get("usage"), Mapping) else None
    finish_reason = api_metadata.get("finish_reason")
    return {
        "experiment_id": experiment_id,
        "experiment_fingerprint": experiment_fingerprint,
        "parser_revision": PARSER_REVISION,
        "phase": phase,
        "item_id": sample["item_id"],
        "generator_version": sample["generator_version"],
        "difficulty_factors": dict(sample["difficulty_factors"]),
        "difficulty_cell": sample["metadata"]["difficulty_cell"],
        "scenario": sample["scenario"],
        "model_alias": model_alias(model_config),
        "model_name": model_config["model_name"],
        "run_id": run_id,
        "seed": seed,
        "answer": answer,
        "gold_answer": gold_answer,
        "correct": bool(valid_answer and answer == gold_answer),
        "reasoning": parsed["reasoning"],
        "confidence": parsed["confidence"],
        "answer_extractable": parsed["answer_extractable"],
        "json_compliant": parsed["json_compliant"],
        "strict_json_syntax": parsed["strict_json_syntax"],
        "parse_source": parsed["parse_source"],
        "fallback_used": parsed["fallback_used"],
        "ambiguous_answer": parsed["ambiguous_answer"],
        "answer_candidates": parsed["answer_candidates"],
        "parse_error": parsed["parse_error"],
        "raw_response": raw_response,
        "selected_option_violation_signature": signature,
        "request_error": request_error,
        "finish_reason": finish_reason,
        "truncated": finish_reason == "length",
        "token_usage": dict(usage) if usage is not None else None,
        "generation_config": {
            "temperature": float(generation_config["temperature"]),
            "top_p": float(generation_config["top_p"]),
            "max_tokens": int(generation_config["max_tokens"]),
            "thinking_enabled": bool(model_config.get("thinking_enabled", False)),
            "seed_requested": True,
        },
        "request_metadata": {
            "api_response_id": api_metadata.get("api_response_id"),
            "attempts": api_metadata.get("attempts"),
            "base_url": model_config.get("base_url"),
            "reused_from_preflight": reused_from_preflight,
        },
    }


def reparse_output_record(
    record: Mapping[str, Any],
    sample: Mapping[str, Any],
) -> dict[str, Any]:
    """Reparse saved raw text without issuing a new model request."""
    updated = dict(record)
    request_error = record.get("request_error")
    if request_error is None:
        parsed = parse_calibration_response(str(record.get("raw_response", "")))
    else:
        parsed = {
            "answer": None,
            "reasoning": "",
            "confidence": None,
            "answer_extractable": False,
            "json_compliant": False,
            "strict_json_syntax": False,
            "parse_source": "request_error",
            "fallback_used": False,
            "ambiguous_answer": False,
            "answer_candidates": [],
            "parse_error": request_error,
        }
    for field in (
        "answer",
        "reasoning",
        "confidence",
        "answer_extractable",
        "json_compliant",
        "strict_json_syntax",
        "parse_source",
        "fallback_used",
        "ambiguous_answer",
        "answer_candidates",
        "parse_error",
    ):
        updated[field] = parsed[field]
    answer = parsed["answer"]
    updated["correct"] = bool(answer in VALID_OPTIONS and answer == sample["gold_answer"])
    updated["selected_option_violation_signature"] = (
        list(sample["option_violation_signature"][answer])
        if answer in VALID_OPTIONS
        else []
    )
    updated["parser_revision"] = PARSER_REVISION
    return updated


def run_records(
    *,
    samples: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
    output_path: str | Path,
    experiment_fingerprint: str,
    phase: str,
) -> dict[str, int]:
    """Run independent calls with strict key/fingerprint resume semantics."""
    allowed = expected_keys(samples, config)
    existing, completed = audit_existing_records(
        output_path,
        allowed,
        experiment_fingerprint,
    )
    generation_config = {
        "temperature": float(config["temperature"]),
        "top_p": float(config["top_p"]),
        "max_tokens": int(config["max_tokens"]),
    }
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    jobs: list[
        tuple[Mapping[str, Any], Mapping[str, Any], int, int, str]
    ] = []
    for sample in samples:
        prompt = build_prompt(str(sample["question"]))
        for model in config["models"]:
            alias = model_alias(model)
            for run_id, seed in enumerate(config["seeds"], start=1):
                key = (str(sample["item_id"]), alias, run_id)
                if key not in completed:
                    jobs.append((sample, model, run_id, int(seed), prompt))

    def execute(
        job: tuple[Mapping[str, Any], Mapping[str, Any], int, int, str]
    ) -> dict[str, Any]:
        sample, model, run_id, seed, prompt = job
        raw, api_metadata, request_error = call_with_retries(
            model_config=model,
            prompt=prompt,
            temperature=generation_config["temperature"],
            top_p=generation_config["top_p"],
            max_tokens=generation_config["max_tokens"],
            seed=seed,
            timeout_seconds=int(config.get("request_timeout_seconds", 120)),
            max_retries=int(config.get("max_retries", 2)),
            retry_sleep_seconds=float(config.get("retry_sleep_seconds", 2)),
        )
        return build_output_record(
            sample=sample,
            model_config=model,
            run_id=run_id,
            seed=seed,
            generation_config=generation_config,
            experiment_id=str(config["experiment_id"]),
            experiment_fingerprint=experiment_fingerprint,
            raw_response=raw,
            api_metadata=api_metadata,
            request_error=request_error,
            phase=phase,
        )

    max_workers = int(config.get("max_concurrent_requests", 1))
    if max_workers < 1:
        raise CalibrationError("max_concurrent_requests must be positive")
    with output.open("a", encoding="utf-8") as file:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures: dict[Future[dict[str, Any]], tuple[str, str, int]] = {}
            for job in jobs:
                sample, model, run_id, _, _ = job
                key = (str(sample["item_id"]), model_alias(model), run_id)
                futures[executor.submit(execute, job)] = key
            for future in as_completed(futures):
                key = futures[future]
                record = future.result()
                file.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
                file.flush()
                completed.add(key)
                written += 1
                if written % 25 == 0 or written == len(jobs):
                    print(f"{len(completed)}/{len(allowed)} completed ({phase})", flush=True)
    return {
        "expected": len(allowed),
        "previously_completed": len(existing),
        "written": written,
        "completed": len(completed),
    }


def copy_preflight_into_formal(
    *,
    preflight_path: str | Path,
    formal_path: str | Path,
    formal_allowed_keys: set[tuple[str, str, int]],
    experiment_fingerprint: str,
) -> int:
    """Reuse protocol-identical preflight calls as formal observations."""
    preflight_records, _ = audit_existing_records(
        preflight_path,
        formal_allowed_keys,
        experiment_fingerprint,
    )
    _, formal_keys = audit_existing_records(
        formal_path,
        formal_allowed_keys,
        experiment_fingerprint,
    )
    additions: list[dict[str, Any]] = []
    for record in preflight_records:
        key = (str(record["item_id"]), str(record["model_alias"]), int(record["run_id"]))
        if key in formal_keys:
            continue
        copied = dict(record)
        copied["phase"] = "formal"
        copied["request_metadata"] = dict(copied.get("request_metadata", {}))
        copied["request_metadata"]["reused_from_preflight"] = True
        additions.append(copied)
        formal_keys.add(key)
    if additions:
        output = Path(formal_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("a", encoding="utf-8") as file:
            for record in additions:
                file.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return len(additions)


def summarize_preflight(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Summarize preflight coverage and output-limit safety."""
    cells = Counter(str(record["difficulty_cell"]) for record in records)
    models = Counter(str(record["model_alias"]) for record in records)
    return {
        "total_records": len(records),
        "difficulty_cells": len(cells),
        "cell_record_counts": dict(sorted(cells.items())),
        "model_record_counts": dict(sorted(models.items())),
        "api_failures": sum(record.get("request_error") is not None for record in records),
        "valid_answers": sum(record.get("answer_extractable") is True for record in records),
        "json_compliant": sum(record.get("json_compliant") is True for record in records),
        "truncated": sum(record.get("truncated") is True for record in records),
        "parse_audit_records": sum(
            record.get("json_compliant") is not True
            or record.get("answer_extractable") is not True
            or record.get("truncated") is True
            or record.get("request_error") is not None
            for record in records
        ),
    }
