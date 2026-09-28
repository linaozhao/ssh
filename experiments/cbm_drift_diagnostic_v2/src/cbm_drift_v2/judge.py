"""DeepSeek Judge execution, parsing, and auditable event validation."""

from __future__ import annotations

import copy
import json
import os
import threading
import time
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from cbm_drift_v2.common import read_json, read_jsonl, sha256_json, write_json, write_jsonl
from cbm_drift_v2.prompts import JUDGE_DIRECT_SYSTEM, JUDGE_STRUCTURED_SYSTEM, judge_user_message

JUDGE_RUNNER_VERSION = "cbm_drift_v2.deepseek_judge.2"
CONTENT_LABELS = {"factual_deviation", "rule_deviation", "inference_application_error", "unresolved"}
TEMPORAL = {"initial_error", "newly_introduced", "persistent", "corrected", "recurrence", "reasonable_update", "correct_maintenance", "uncertain"}
EFFECTS = {"none", "correct_to_wrong", "wrong_to_correct", "wrong_to_wrong", "correct_to_correct", "uncertain"}
STANCES = {"asserted", "quoted", "rejected", "hypothetical", "uncertain"}


def _extract_json(text: str) -> tuple[dict[str, Any] | None, str]:
    """Prefer exact JSON; otherwise accept one unambiguous embedded object."""
    try:
        value = json.loads(text)
        return (value, "strict_json") if isinstance(value, dict) else (None, "non_object_json")
    except json.JSONDecodeError:
        pass
    decoder, found = json.JSONDecoder(), []
    for index, character in enumerate(text):
        if character != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            found.append(value)
    unique = {json.dumps(value, sort_keys=True, ensure_ascii=False): value for value in found}
    return (next(iter(unique.values())), "embedded_json") if len(unique) == 1 else (None, "ambiguous_or_missing_json")


def validate_prediction(value: dict[str, Any] | None, package: dict[str, Any]) -> dict[str, Any]:
    """Validate schema, exact quotes, IDs, and peer visibility without judging semantics."""
    errors: list[str] = []
    if value is None:
        return {
            "schema_valid": False, "validation_errors": ["no JSON object"],
            "normalization_actions": [], "normalized": None,
        }
    required = {"has_diagnostic_event", "temporal_status", "content_labels", "claims", "answer_effect", "related_peer_message_ids", "uncertainty_reason"}
    missing = required - set(value)
    if missing:
        errors.append(f"missing fields: {sorted(missing)}")
    if not isinstance(value.get("has_diagnostic_event"), bool):
        errors.append("has_diagnostic_event must be boolean")
    temporal = value.get("temporal_status")
    if temporal not in TEMPORAL:
        errors.append("invalid temporal_status")
    effect = value.get("answer_effect")
    if effect not in EFFECTS:
        errors.append("invalid answer_effect")
    labels = value.get("content_labels")
    if not isinstance(labels, list) or any(label not in CONTENT_LABELS for label in labels):
        errors.append("invalid content_labels")
    peers = value.get("related_peer_message_ids")
    visible = set(package.get("visible_peer_message_ids", []))
    if not isinstance(peers, list) or any(peer not in visible for peer in peers):
        errors.append("related peer ID was not visible")
    normalized = copy.deepcopy(value)
    claims = normalized.get("claims")
    current = package["current_message_text"]
    valid_facts = {row["evidence_id"] for row in package["reference_structure"]["active_evidence"]}
    valid_rules = {row["id"] for row in package["reference_structure"]["rules"]}
    if not isinstance(claims, list):
        errors.append("claims must be a list")
        claims = []
    normalization_actions: list[str] = []
    for index, claim in enumerate(claims):
        if not isinstance(claim, dict):
            errors.append(f"claim {index} is not an object")
            continue
        quote, start, end = claim.get("quote"), claim.get("start"), claim.get("end")
        if not isinstance(quote, str) or not quote:
            errors.append(f"claim {index} has no exact quote")
        elif isinstance(start, int) and isinstance(end, int) and start >= 0 and end >= start and current[start:end] == quote:
            pass
        elif current.count(quote) == 1:
            actual_start = current.index(quote)
            claim["start"], claim["end"] = actual_start, actual_start + len(quote)
            normalization_actions.append(f"claim {index} offsets derived from unique exact quote")
        elif current.count(quote) > 1:
            errors.append(f"claim {index} exact quote is ambiguous in current message")
        else:
            errors.append(f"claim {index} quote does not match current message")
        if any(value not in {"A", "B", "C", "D"} for value in claim.get("target_entity_ids", [])):
            errors.append(f"claim {index} has invalid target entity")
        if any(value not in valid_facts for value in claim.get("violated_fact_ids", [])):
            errors.append(f"claim {index} has invalid fact ID")
        if any(value not in valid_rules for value in claim.get("violated_rule_ids", [])):
            errors.append(f"claim {index} has invalid rule ID")
        if claim.get("stance") not in STANCES:
            errors.append(f"claim {index} has invalid stance")
    normalized["content_labels"] = sorted(set(labels or []))
    normalized["related_peer_message_ids"] = sorted(set(peers or []))
    return {
        "schema_valid": not errors, "validation_errors": errors,
        "normalization_actions": normalization_actions, "normalized": normalized,
    }


class DeepSeekJudge:
    """Run both diagnostic protocols with one frozen DeepSeek model."""

    def __init__(self, root: Path, config: dict[str, Any]) -> None:
        self.root, self.config = root, config
        self.judge = config["judge"]
        env_name = str(self.judge["api_key_env"])
        self.api_key = os.environ.get(env_name)
        if not self.api_key:
            raise RuntimeError(f"Missing required environment variable: {env_name}")
        self.packages = read_jsonl(root / "results/judge/judge_input_packages.jsonl")
        self.results_dir = root / "results/judge"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.output_path = self.results_dir / "judge_outputs.jsonl"
        safe_judge = dict(self.judge)
        self.manifest = {
            "experiment_id": config["experiment_id"], "runner_version": JUDGE_RUNNER_VERSION,
            "judge_config": safe_judge, "packages_sha256": sha256_json(self.packages),
            "prompt_sha256": sha256_json({"direct": JUDGE_DIRECT_SYSTEM, "structured": JUDGE_STRUCTURED_SYSTEM}),
            "expected_requests": len(self.packages) * len(self.judge["protocols"]),
        }
        self.manifest_hash = sha256_json(self.manifest)
        self.completed: dict[str, dict[str, Any]] = {}
        self.lock = threading.Lock()
        if self.output_path.exists():
            for row in read_jsonl(self.output_path):
                if row.get("judge_manifest_sha256") != self.manifest_hash:
                    raise RuntimeError("Existing Judge outputs have a different fingerprint")
                if row["judge_request_id"] in self.completed:
                    raise RuntimeError(f"Duplicate Judge request: {row['judge_request_id']}")
                self.completed[row["judge_request_id"]] = row

    def initialize(self) -> None:
        path = self.results_dir / "experiment_manifest.json"
        if path.exists() and read_json(path) != self.manifest:
            raise RuntimeError("Existing Judge manifest differs")
        write_json(path, self.manifest)

    def _append(self, row: dict[str, Any]) -> None:
        with self.lock:
            if row["judge_request_id"] in self.completed:
                return
            with self.output_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
                handle.flush()
            self.completed[row["judge_request_id"]] = row

    def _call(self, package: dict[str, Any], protocol: str) -> dict[str, Any]:
        structured = protocol == "structured_assistance"
        messages = [
            {"role": "system", "content": JUDGE_STRUCTURED_SYSTEM if structured else JUDGE_DIRECT_SYSTEM},
            {"role": "user", "content": judge_user_message(package, structured=structured)},
        ]
        payload = {
            "model": self.judge["model_name"], "messages": messages,
            "temperature": self.judge["temperature"], "max_tokens": self.judge["max_tokens"],
            "response_format": {"type": "json_object"},
            "thinking": {"type": "enabled" if self.judge.get("thinking_enabled") else "disabled"},
        }
        request = urllib.request.Request(
            self.judge["base_url"].rstrip("/") + "/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
            method="POST",
        )
        request_id = f"{protocol}:{package['message_id']}"
        errors, body, content = [], None, ""
        started = time.monotonic()
        for attempt in range(int(self.judge["max_retries"]) + 1):
            try:
                opener = urllib.request.build_opener()
                with opener.open(request, timeout=int(self.judge["request_timeout_seconds"])) as response:
                    body = json.loads(response.read().decode("utf-8"))
                content = body["choices"][0]["message"].get("content") or ""
                break
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, KeyError) as exc:
                errors.append(f"{type(exc).__name__}: {exc}")
                if attempt < int(self.judge["max_retries"]):
                    time.sleep(float(self.judge["retry_sleep_seconds"]))
        success = body is not None
        parsed, source = _extract_json(content) if success else (None, "api_failure")
        checked = validate_prediction(parsed, package)
        choice = body["choices"][0] if success else {}
        return {
            "judge_request_id": request_id, "judge_manifest_sha256": self.manifest_hash,
            "package_id": package["package_id"], "message_id": package["message_id"],
            "base_item_id": package["base_item_id"], "variant_id": package["variant_id"],
            "trajectory_id": package["trajectory_id"], "evidence_stage": package["evidence_stage"],
            "round": package["round"], "agent_id": package["agent_id"],
            "judge_protocol": protocol, "model_name": self.judge["model_name"],
            "api_success": success, "raw_response": content, "parse_source": source,
            "parse_success": parsed is not None, "schema_valid": checked["schema_valid"],
            "validation_errors": checked["validation_errors"],
            "normalization_actions": checked["normalization_actions"], "prediction": checked["normalized"],
            "finish_reason": choice.get("finish_reason"), "usage": body.get("usage") if success else None,
            "response_model": body.get("model") if success else None,
            "request_attempts": min(len(errors) + 1, int(self.judge["max_retries"]) + 1),
            "request_errors": errors, "latency_seconds": round(time.monotonic() - started, 4),
            "package_sha256": package["package_sha256"],
        }

    def run(self, *, limit_requests: int | None = None) -> dict[str, Any]:
        """Run each protocol exactly once per message, with resume support."""
        self.initialize()
        jobs = [
            (package, protocol)
            for package in self.packages
            for protocol in self.judge["protocols"]
            if f"{protocol}:{package['message_id']}" not in self.completed
        ]
        if limit_requests is not None:
            jobs = jobs[:limit_requests]
        with ThreadPoolExecutor(max_workers=int(self.judge["max_concurrency"])) as pool:
            futures = [pool.submit(self._call, package, protocol) for package, protocol in jobs]
            for future in as_completed(futures):
                self._append(future.result())
        rows = list(self.completed.values())
        summary = {
            "expected": len(self.packages) * len(self.judge["protocols"]), "completed": len(rows),
            "new_calls": len(jobs), "api_success": sum(row["api_success"] for row in rows),
            "parse_success": sum(row["parse_success"] for row in rows),
            "schema_valid": sum(row["schema_valid"] for row in rows),
            "by_protocol": {
                protocol: {
                    "records": sum(row["judge_protocol"] == protocol for row in rows),
                    "diagnostic_events": sum(
                        row["judge_protocol"] == protocol and bool((row.get("prediction") or {}).get("has_diagnostic_event"))
                        for row in rows
                    ),
                    "content_labels": dict(sorted(Counter(
                        label for row in rows if row["judge_protocol"] == protocol
                        for label in ((row.get("prediction") or {}).get("content_labels") or [])
                    ).items())),
                }
                for protocol in self.judge["protocols"]
            },
        }
        write_json(self.results_dir / "summary.json", summary)
        return summary


def materialize_predicted_events(root: Path) -> dict[str, Any]:
    """Convert validated Judge outputs into explicitly model-sourced prediction events."""
    outputs = read_jsonl(root / "results/judge/judge_outputs.jsonl")
    packages = {row["message_id"]: row for row in read_jsonl(root / "results/judge/judge_input_packages.jsonl")}
    rows = []
    for output in outputs:
        prediction = output.get("prediction")
        if not output.get("schema_valid") or not prediction or not prediction.get("has_diagnostic_event"):
            continue
        package = packages[output["message_id"]]
        claims = prediction.get("claims") or []
        rows.append({
            "event_id": "judge:" + sha256_json([output["judge_protocol"], output["message_id"]])[:20],
            "base_item_id": output["base_item_id"], "variant_id": output["variant_id"],
            "trajectory_id": output["trajectory_id"], "evidence_stage": output["evidence_stage"],
            "round": output["round"], "agent_id": output["agent_id"], "message_id": output["message_id"],
            "temporal_status": prediction["temporal_status"],
            "content_labels": prediction["content_labels"],
            "target_entity_ids": sorted({value for claim in claims for value in claim.get("target_entity_ids", [])}),
            "violated_fact_ids": sorted({value for claim in claims for value in claim.get("violated_fact_ids", [])}),
            "violated_rule_ids": sorted({value for claim in claims for value in claim.get("violated_rule_ids", [])}),
            "current_quotes": [
                {"quote": claim.get("quote"), "start": claim.get("start"), "end": claim.get("end"), "stance": claim.get("stance")}
                for claim in claims
            ],
            "prior_quotes": [], "answer_effect": prediction["answer_effect"],
            "related_peer_message_ids": prediction["related_peer_message_ids"],
            "uncertainty_reason": prediction.get("uncertainty_reason"),
            "detector_version": JUDGE_RUNNER_VERSION, "judge_protocol": output["judge_protocol"],
            "label_source": f"{output['model_name']}_model_preannotation",
            "quote_and_id_validation_passed": True,
            "package_sha256": package["package_sha256"],
        })
    write_jsonl(root / "results/judge/predicted_events.jsonl", rows)
    summary = {"predicted_events": len(rows), "by_protocol": dict(sorted(Counter(row["judge_protocol"] for row in rows).items()))}
    write_json(root / "results/judge/predicted_events_summary.json", summary)
    return summary
