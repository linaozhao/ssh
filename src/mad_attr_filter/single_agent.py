"""Single-agent OpenAI-compatible runner for English pilot screening."""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from mad_attr_filter.io import read_jsonl

VALID_OPTIONS = {"A", "B", "C", "D"}

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


def model_alias(model_config: Mapping[str, Any]) -> str:
    """Return the configured model alias, accepting both v1 and v2 config keys."""
    alias = model_config.get("alias", model_config.get("model_alias"))
    if not alias:
        raise ValueError("Model config must define 'alias' or 'model_alias'")
    return str(alias)


def build_prompt(question: str) -> str:
    """Build the single-agent prompt from the natural-language question only."""
    return PROMPT_TEMPLATE.format(question=question)


def _find_json_object(text: str) -> str | None:
    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return None


def _normalize_answer(value: Any) -> str | None:
    """Normalize common answer strings to A/B/C/D without guessing from reasoning."""
    text = str(value).strip().upper()
    if text in VALID_OPTIONS:
        return text
    match = re.fullmatch(r"(?:OPTION|CANDIDATE)?\s*([ABCD])\.?", text)
    if match:
        return match.group(1)
    return None


def _fallback_answer(raw_response: str) -> str | None:
    """Conservatively extract an answer from non-JSON text."""
    stripped = raw_response.strip().upper()
    if stripped in VALID_OPTIONS:
        return stripped
    patterns = (
        r"\bANSWER\s*[:：-]\s*([ABCD])\b",
        r"\bSELECTED\s+ANSWER\s*[:：-]\s*([ABCD])\b",
        r"\bOPTION\s+([ABCD])\b",
        r"\bCANDIDATE\s+([ABCD])\b",
    )
    for pattern in patterns:
        match = re.search(pattern, raw_response, flags=re.IGNORECASE)
        if match:
            return match.group(1).upper()
    return None


def _parse_confidence(value: Any) -> tuple[float | None, str | None]:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return None, "Confidence is missing or not numeric"
    if not 0.0 <= confidence <= 1.0:
        return confidence, "Confidence is outside [0, 1]"
    return confidence, None


def _validate_parsed_object(parsed: Any) -> dict[str, Any]:
    if not isinstance(parsed, dict):
        return {
            "parse_success": False,
            "answer": None,
            "reasoning": "",
            "confidence": None,
            "parse_error": "Parsed JSON is not an object",
        }
    answer = _normalize_answer(parsed.get("answer"))
    reasoning = str(parsed.get("reasoning", ""))
    confidence, confidence_error = _parse_confidence(parsed.get("confidence"))
    errors: list[str] = []
    if answer is None:
        errors.append("Answer is not one of A/B/C/D")
    if confidence_error is not None:
        errors.append(confidence_error)
    return {
        "parse_success": not errors,
        "answer": answer,
        "reasoning": reasoning,
        "confidence": confidence,
        "parse_error": "; ".join(errors) if errors else None,
    }


def parse_model_response(raw_response: str) -> dict[str, Any]:
    """Parse model output while retaining conservative fallback answers.

    ``parse_success`` means the response contained valid JSON with a valid answer
    and a numeric confidence in ``[0, 1]``. If strict JSON parsing fails, a simple
    answer fallback may still populate ``answer`` so correctness can be audited
    without hiding the formatting failure.
    """
    stripped = raw_response.strip()
    try:
        strict_parsed = json.loads(stripped)
    except json.JSONDecodeError:
        strict_parsed = None
    else:
        parsed = _validate_parsed_object(strict_parsed)
        parsed["strict_json_success"] = parsed["parse_success"]
        parsed["fallback_parse_success"] = False
        if not parsed["parse_success"]:
            parsed["answer"] = parsed["answer"] or _fallback_answer(raw_response)
        return parsed

    json_text = _find_json_object(raw_response)
    if json_text is None:
        return {
            "parse_success": False,
            "answer": _fallback_answer(raw_response),
            "reasoning": "",
            "confidence": None,
            "parse_error": "No JSON object found",
            "strict_json_success": False,
            "fallback_parse_success": False,
        }
    try:
        parsed = json.loads(json_text)
    except json.JSONDecodeError as exc:
        return {
            "parse_success": False,
            "answer": _fallback_answer(raw_response),
            "reasoning": "",
            "confidence": None,
            "parse_error": f"JSON decode error: {exc}",
            "strict_json_success": False,
            "fallback_parse_success": False,
        }
    parsed_result = _validate_parsed_object(parsed)
    parsed_result["strict_json_success"] = False
    parsed_result["fallback_parse_success"] = parsed_result["parse_success"]
    if not parsed_result["parse_success"]:
        parsed_result["answer"] = parsed_result["answer"] or _fallback_answer(raw_response)
    return parsed_result


def load_completed_keys(path: str | Path, *, retry_failed: bool = False) -> set[tuple[str, str, int]]:
    """Load completed item/model/run_id keys from an existing output JSONL."""
    output_path = Path(path)
    if not output_path.exists():
        return set()
    completed: set[tuple[str, str, int]] = set()
    for record in read_jsonl(output_path):
        request_error = record.get("metadata", {}).get("request_error")
        # API failures may be retried because no model response was obtained.
        # Formatting failures are completed experimental samples and must not
        # trigger another inference call.
        if retry_failed and request_error:
            continue
        run_id = record.get("run_id", record.get("seed"))
        completed.add((str(record["item_id"]), str(record["model_alias"]), int(run_id)))
    return completed


def call_openai_compatible(
    *,
    model_config: Mapping[str, Any],
    prompt: str,
    temperature: float,
    top_p: float,
    max_tokens: int,
    seed: int,
    timeout_seconds: int,
) -> tuple[str, dict[str, Any]]:
    """Call an OpenAI-compatible chat completions endpoint using urllib."""
    base_url = str(model_config["base_url"]).rstrip("/")
    url = f"{base_url}/chat/completions"
    payload = {
        "model": model_config["model_name"],
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
        "seed": seed,
    }
    extra_body = model_config.get("extra_body")
    if isinstance(extra_body, Mapping):
        payload.update(extra_body)
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {model_config.get('api_key', 'EMPTY')}",
        },
        method="POST",
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=timeout_seconds) as response:
        response_body = response.read().decode("utf-8")
    response_json = json.loads(response_body)
    choices = response_json.get("choices", [])
    if not choices:
        raise RuntimeError("No choices returned by API")
    content = choices[0].get("message", {}).get("content", "")
    return str(content), {
        "api_response_id": response_json.get("id"),
        "usage": response_json.get("usage"),
        "finish_reason": choices[0].get("finish_reason"),
    }


def call_with_retries(
    *,
    model_config: Mapping[str, Any],
    prompt: str,
    temperature: float,
    top_p: float,
    max_tokens: int,
    seed: int,
    timeout_seconds: int,
    max_retries: int,
    retry_sleep_seconds: float,
) -> tuple[str, dict[str, Any], str | None]:
    """Call the model with bounded retries and return raw text, metadata, error."""
    last_error: str | None = None
    for attempt in range(max_retries + 1):
        try:
            raw_response, metadata = call_openai_compatible(
                model_config=model_config,
                prompt=prompt,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                seed=seed,
                timeout_seconds=timeout_seconds,
            )
            metadata["attempts"] = attempt + 1
            return raw_response, metadata, None
        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            TimeoutError,
            RuntimeError,
            json.JSONDecodeError,
        ) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt < max_retries:
                time.sleep(retry_sleep_seconds)
    return "", {"attempts": max_retries + 1}, last_error


def _reasoning_diagnostics(reasoning: str, answer: str | None) -> dict[str, Any]:
    labels = {"A", "B", "C", "D"}
    mentioned = {label for label in labels if re.search(rf"\b{label}\b", reasoning)}
    return {
        "word_count": len(re.findall(r"\b[\w'-]+\b", reasoning)),
        "mentions_all_candidate_labels": mentioned == labels,
        "mentions_selected_option": bool(answer and answer in mentioned),
    }


def build_output_record(
    *,
    sample: Mapping[str, Any],
    model_config: Mapping[str, Any],
    run_id: int,
    seed: int,
    generation_config: Mapping[str, Any],
    raw_response: str,
    api_metadata: Mapping[str, Any],
    request_error: str | None,
) -> dict[str, Any]:
    """Build one JSONL output record from a model response."""
    if request_error is None:
        parsed = parse_model_response(raw_response)
    else:
        parsed = {
            "parse_success": False,
            "answer": None,
            "reasoning": "",
            "confidence": None,
            "parse_error": request_error,
            "strict_json_success": False,
            "fallback_parse_success": False,
        }
    answer = parsed["answer"]
    gold_answer = str(sample["gold_answer"])
    correct = answer in VALID_OPTIONS and answer == gold_answer
    selected_signature = []
    if answer in sample["option_violation_signature"]:
        selected_signature = list(sample["option_violation_signature"][answer])
    num_constraints = int(sample.get("metadata", {}).get("num_constraints", len(sample.get("constraints", []))))
    return {
        "item_id": sample["item_id"],
        "model_alias": model_alias(model_config),
        "model_name": model_config["model_name"],
        "run_id": run_id,
        "seed": seed,
        "answer": answer,
        "gold_answer": gold_answer,
        "correct": bool(correct),
        "reasoning": parsed["reasoning"],
        "confidence": parsed["confidence"],
        "parse_success": parsed["parse_success"],
        "strict_json_success": parsed["strict_json_success"],
        "fallback_parse_success": parsed["fallback_parse_success"],
        "raw_response": raw_response,
        "parse_error": parsed["parse_error"],
        "selected_option_violation_signature": selected_signature,
        "option_closeness": sample.get("option_closeness"),
        "structural_complexity": sample.get("structural_complexity"),
        "scenario": sample.get("scenario"),
        "num_constraints": num_constraints,
        "generation_config": {
            "temperature": float(generation_config["temperature"]),
            "top_p": float(generation_config["top_p"]),
            "max_tokens": int(generation_config["max_tokens"]),
            "thinking_enabled": bool(model_config.get("thinking_enabled", False)),
            "seed_requested": True,
        },
        "reasoning_diagnostics": _reasoning_diagnostics(parsed["reasoning"], answer),
        "metadata": {
            "request_error": request_error,
            "api_metadata": dict(api_metadata),
            "base_url": model_config.get("base_url"),
        },
    }


def expected_run_count(samples: Sequence[Mapping[str, Any]], config: Mapping[str, Any]) -> int:
    """Return expected number of single-agent calls."""
    return len(samples) * len(config.get("models", [])) * len(config.get("seeds", []))
