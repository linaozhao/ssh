"""Resumable OpenAI-compatible runner for Qwen v4.1 follow-up experiments."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Mapping, Sequence
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mad_attr_filter.io import read_jsonl
from mad_attr_filter.qwen_followup import (
    FOLLOWUP_PARSER_REVISION,
    FOLLOWUP_PROTOCOL_VERSION,
    parse_followup_response,
)
from mad_attr_filter.single_agent import call_with_retries
from mad_attr_filter.v4_calibration import PROMPT_TEMPLATE, VALID_OPTIONS, build_prompt
from mad_attr_filter.v4_validation import validate_v4_item


def materialize_experiment_config(
    config: Mapping[str, Any], experiment_name: str
) -> dict[str, Any]:
    """Build the exact isolated config whose hash governs one experiment."""
    try:
        experiment = config["experiments"][experiment_name]
    except KeyError as exc:
        raise ValueError(f"Unknown follow-up experiment: {experiment_name}") from exc
    return {
        "experiment_name": experiment_name,
        "experiment_id": experiment["experiment_id"],
        "dataset": experiment["dataset"],
        "results_dir": experiment["results_dir"],
        "seeds": list(experiment["seeds"]),
        "model": dict(config["model"]),
        "temperature": float(config["temperature"]),
        "top_p": float(config["top_p"]),
        "max_tokens": int(config["max_tokens"]),
        "request_timeout_seconds": int(config.get("request_timeout_seconds", 120)),
        "max_retries": int(config.get("max_retries", 2)),
        "retry_sleep_seconds": float(config.get("retry_sleep_seconds", 2)),
        "max_concurrent_requests": int(config.get("max_concurrent_requests", 1)),
    }


def record_variant_id(item: Mapping[str, Any]) -> str:
    """Return the diagnostic variant ID, or the item ID for extension items."""
    return str(item.get("variant_id") or item["item_id"])


def expected_keys(
    samples: Sequence[Mapping[str, Any]], experiment_config: Mapping[str, Any]
) -> set[tuple[str, str, int]]:
    """Build the frozen variant/model/run key set."""
    alias = str(experiment_config["model"]["alias"])
    return {
        (record_variant_id(sample), alias, run_id)
        for sample in samples
        for run_id, _ in enumerate(experiment_config["seeds"], start=1)
    }


def output_key(record: Mapping[str, Any]) -> tuple[str, str, int]:
    return (
        str(record.get("variant_id")),
        str(record.get("model_alias")),
        int(record.get("run_id", 0)),
    )


def audit_output_inventory(
    path: str | Path,
    samples: Sequence[Mapping[str, Any]],
    experiment_config: Mapping[str, Any],
    experiment_fingerprint: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Reject duplicate, unknown, and fingerprint-mismatched resume records."""
    expected = expected_keys(samples, experiment_config)
    records = read_jsonl(path) if Path(path).exists() else []
    observed: set[tuple[str, str, int]] = set()
    duplicates: list[tuple[str, str, int]] = []
    unknown: list[tuple[str, str, int]] = []
    mismatches: list[tuple[str, str, int]] = []
    for record in records:
        key = output_key(record)
        if key in observed:
            duplicates.append(key)
        observed.add(key)
        if key not in expected:
            unknown.append(key)
        if record.get("experiment_fingerprint") != experiment_fingerprint:
            mismatches.append(key)
    missing = sorted(expected - observed)
    audit = {
        "expected_runs": len(expected),
        "completed_records": len(records),
        "unique_completed_runs": len(observed),
        "missing_count": len(missing),
        "duplicate_count": len(duplicates),
        "unknown_count": len(unknown),
        "fingerprint_mismatch_count": len(mismatches),
        "missing": [list(key) for key in missing],
        "duplicates": [list(key) for key in sorted(duplicates)],
        "unknown": [list(key) for key in sorted(unknown)],
        "fingerprint_mismatches": [list(key) for key in sorted(mismatches)],
        "complete": not (missing or duplicates or unknown or mismatches),
    }
    if duplicates or unknown or mismatches:
        raise ValueError(f"Existing output inventory is incompatible: {audit}")
    return records, audit


def probe_service(model: Mapping[str, Any]) -> dict[str, Any]:
    """Record the model IDs and vLLM version currently exposed by the endpoint."""
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    base_url = str(model["base_url"]).rstrip("/")
    observation: dict[str, Any] = {
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "configured_model_name": model["model_name"],
    }
    try:
        with opener.open(f"{base_url}/models", timeout=10) as response:
            available = json.loads(response.read().decode("utf-8"))
        with opener.open(f"{base_url.removesuffix('/v1')}/version", timeout=10) as response:
            version = json.loads(response.read().decode("utf-8"))
        observation.update(
            {
                "probe_success": True,
                "available_model_ids": [row.get("id") for row in available.get("data", [])],
                "backend_version": version,
                "probe_error": None,
            }
        )
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        observation.update(
            {
                "probe_success": False,
                "available_model_ids": [],
                "backend_version": None,
                "probe_error": f"{type(exc).__name__}: {exc}",
            }
        )
    return observation


def make_manifest(
    dataset_path: str | Path,
    samples: Sequence[Mapping[str, Any]],
    experiment_config: Mapping[str, Any],
    fingerprints: Mapping[str, str],
) -> dict[str, Any]:
    """Create one immutable experiment manifest without exposing API credentials."""
    public_config = json.loads(json.dumps(experiment_config))
    public_config["model"].pop("api_key", None)
    return {
        "experiment_id": experiment_config["experiment_id"],
        "experiment_name": experiment_config["experiment_name"],
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_path": str(dataset_path),
        "item_count": len(samples),
        "expected_runs": len(samples) * len(experiment_config["seeds"]),
        "fingerprints": dict(fingerprints),
        "protocol_version": FOLLOWUP_PROTOCOL_VERSION,
        "parser_revision": FOLLOWUP_PARSER_REVISION,
        "prompt_template": PROMPT_TEMPLATE,
        "config": public_config,
        "independence": {
            "each_call_has_fresh_messages": True,
            "prompt_input_field": "question",
            "gold_or_formal_fields_exposed": False,
            "other_responses_exposed": False,
        },
        "status": "pending",
    }


def assert_manifest_compatible(
    manifest: Mapping[str, Any],
    experiment_config: Mapping[str, Any],
    fingerprints: Mapping[str, str],
) -> None:
    """Prevent resume across changed data, prompts, parser protocol, or parameters."""
    if manifest.get("experiment_id") != experiment_config["experiment_id"]:
        raise ValueError("Experiment ID changed since the manifest was frozen")
    if manifest.get("fingerprints") != dict(fingerprints):
        raise ValueError("Dataset, config, prompt, or parser fingerprint changed")


def build_output_record(
    *,
    sample: Mapping[str, Any],
    experiment_config: Mapping[str, Any],
    run_id: int,
    seed: int,
    experiment_fingerprint: str,
    raw_response: str,
    api_metadata: Mapping[str, Any],
    request_error: str | None,
) -> dict[str, Any]:
    """Build one scored record while keeping format and semantic validity separate."""
    if request_error is None:
        parsed = parse_followup_response(raw_response, sample)
    else:
        parsed = {
            "answer": None,
            "raw_answer": None,
            "reasoning": "",
            "confidence": None,
            "answer_extractable": False,
            "json_compliant": False,
            "strict_json_syntax": False,
            "strict_answer_format": False,
            "semantic_name_mapping_used": False,
            "parse_source": "request_error",
            "fallback_used": False,
            "ambiguous_answer": False,
            "answer_candidates": [],
            "parse_error": request_error,
        }
    answer = parsed["answer"]
    valid_answer = answer in VALID_OPTIONS
    selected_name = (
        sample["entities"][answer]["name"] if valid_answer else None
    )
    finish_reason = api_metadata.get("finish_reason")
    usage = api_metadata.get("usage")
    if not isinstance(usage, Mapping):
        usage = None
    factors = dict(sample["difficulty_factors"])
    model = experiment_config["model"]
    return {
        "experiment_id": experiment_config["experiment_id"],
        "experiment_fingerprint": experiment_fingerprint,
        "protocol_version": FOLLOWUP_PROTOCOL_VERSION,
        "parser_revision": FOLLOWUP_PARSER_REVISION,
        "item_id": sample["item_id"],
        "source_item_id": sample.get("source_item_id", sample["item_id"]),
        "base_item_id": sample.get("base_item_id"),
        "variant_id": record_variant_id(sample),
        "variant_type": sample.get("variant_type", "original"),
        "generator_version": sample["generator_version"],
        "difficulty_factors": factors,
        "difficulty_cell": sample["metadata"]["difficulty_cell"],
        "scenario": sample["scenario"],
        "selection_group": sample.get("selection_group"),
        "pair_version": sample.get("pair_version"),
        "model_alias": model["alias"],
        "model_name": model["model_name"],
        "run_id": run_id,
        "seed": seed,
        "raw_answer": parsed["raw_answer"],
        "answer": answer,
        "selected_candidate_name": selected_name,
        "gold_answer": sample["gold_answer"],
        "gold_candidate_name": sample["entities"][sample["gold_answer"]]["name"],
        "correct": bool(valid_answer and answer == sample["gold_answer"]),
        "strict_format_correct": bool(
            parsed["strict_answer_format"] and answer == sample["gold_answer"]
        ),
        "reasoning": parsed["reasoning"],
        "confidence": parsed["confidence"],
        "answer_extractable": parsed["answer_extractable"],
        "json_compliant": parsed["json_compliant"],
        "strict_json_syntax": parsed["strict_json_syntax"],
        "strict_answer_format": parsed["strict_answer_format"],
        "semantic_name_mapping_used": parsed["semantic_name_mapping_used"],
        "parse_source": parsed["parse_source"],
        "fallback_used": parsed["fallback_used"],
        "ambiguous_answer": parsed["ambiguous_answer"],
        "answer_candidates": parsed["answer_candidates"],
        "parse_error": parsed["parse_error"],
        "raw_response": raw_response,
        "selected_option_violation_signature": (
            list(sample["option_violation_signature"][answer]) if valid_answer else []
        ),
        "request_error": request_error,
        "finish_reason": finish_reason,
        "truncated": finish_reason == "length",
        "token_usage": dict(usage) if usage is not None else None,
        "generation_config": {
            "temperature": experiment_config["temperature"],
            "top_p": experiment_config["top_p"],
            "max_tokens": experiment_config["max_tokens"],
            "thinking_enabled": bool(model.get("thinking_enabled", False)),
            "seed_requested": True,
        },
        "request_metadata": {
            "base_url": model["base_url"],
            "api_response_id": api_metadata.get("api_response_id"),
            "attempts": api_metadata.get("attempts"),
        },
    }


def run_experiment(
    *,
    samples: Sequence[Mapping[str, Any]],
    experiment_config: Mapping[str, Any],
    output_path: str | Path,
    experiment_fingerprint: str,
) -> dict[str, Any]:
    """Run all missing calls and flush every observation for interruption safety."""
    for item in samples:
        validate_v4_item(item)
    existing, before = audit_output_inventory(
        output_path, samples, experiment_config, experiment_fingerprint
    )
    completed = {output_key(record) for record in existing}
    alias = str(experiment_config["model"]["alias"])
    jobs: list[tuple[Mapping[str, Any], int, int, str]] = []
    for sample in samples:
        prompt = build_prompt(str(sample["question"]))
        for run_id, seed in enumerate(experiment_config["seeds"], start=1):
            key = (record_variant_id(sample), alias, run_id)
            if key not in completed:
                jobs.append((sample, run_id, int(seed), prompt))

    def execute(job: tuple[Mapping[str, Any], int, int, str]) -> dict[str, Any]:
        sample, run_id, seed, prompt = job
        raw, api_metadata, request_error = call_with_retries(
            model_config=experiment_config["model"],
            prompt=prompt,
            temperature=experiment_config["temperature"],
            top_p=experiment_config["top_p"],
            max_tokens=experiment_config["max_tokens"],
            seed=seed,
            timeout_seconds=experiment_config["request_timeout_seconds"],
            max_retries=experiment_config["max_retries"],
            retry_sleep_seconds=experiment_config["retry_sleep_seconds"],
        )
        return build_output_record(
            sample=sample,
            experiment_config=experiment_config,
            run_id=run_id,
            seed=seed,
            experiment_fingerprint=experiment_fingerprint,
            raw_response=raw,
            api_metadata=api_metadata,
            request_error=request_error,
        )

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with output.open("a", encoding="utf-8") as file:
        with ThreadPoolExecutor(
            max_workers=experiment_config["max_concurrent_requests"]
        ) as executor:
            futures: dict[Future[dict[str, Any]], tuple[str, str, int]] = {}
            for sample, run_id, seed, prompt in jobs:
                key = (record_variant_id(sample), alias, run_id)
                futures[executor.submit(execute, (sample, run_id, seed, prompt))] = key
            for future in as_completed(futures):
                key = futures[future]
                record = future.result()
                file.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
                file.flush()
                completed.add(key)
                written += 1
                if written % 25 == 0 or written == len(jobs):
                    print(
                        f"{len(completed)}/{before['expected_runs']} completed "
                        f"({experiment_config['experiment_name']})",
                        flush=True,
                    )
    records, after = audit_output_inventory(
        output_path, samples, experiment_config, experiment_fingerprint
    )
    return {
        **after,
        "previously_completed": len(existing),
        "written_this_invocation": written,
        "api_failure_count": sum(record.get("request_error") is not None for record in records),
        "unrecognized_answer_count": sum(
            record.get("request_error") is None
            and record.get("answer_extractable") is not True
            for record in records
        ),
        "json_noncompliant_count": sum(
            record.get("json_compliant") is not True for record in records
        ),
        "truncated_count": sum(record.get("truncated") is True for record in records),
    }
