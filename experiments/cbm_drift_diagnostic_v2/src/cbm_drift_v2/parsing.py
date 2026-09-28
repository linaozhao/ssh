"""Conservative candidate-set response parsing."""

from __future__ import annotations

import json
import re
from typing import Any

from cbm_drift_v2.common import LABELS


def _json_objects(text: str) -> list[dict[str, Any]]:
    decoder = json.JSONDecoder()
    values: list[dict[str, Any]] = []
    seen: set[str] = set()
    for start, character in enumerate(text):
        if character != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text[start:])
        except json.JSONDecodeError:
            continue
        if not isinstance(value, dict):
            continue
        key = json.dumps(value, sort_keys=True, ensure_ascii=False)
        if key not in seen:
            values.append(value)
            seen.add(key)
    return values


def _normalize(values: Any, names: dict[str, str]) -> tuple[list[str] | None, list[str]]:
    if not isinstance(values, list):
        return None, []
    labels: list[str] = []
    sources: list[str] = []
    for value in values:
        text = str(value).strip()
        upper = text.upper()
        if upper in LABELS:
            label, source = upper, "label"
        else:
            matches = [label for label, name in names.items() if text.casefold() == str(name).casefold()]
            if len(matches) != 1:
                return None, []
            label, source = matches[0], "full_name"
        if label in labels:
            return None, []
        labels.append(label)
        sources.append(source)
    return sorted(labels), sources


def parse_answer_set(raw: str, names: dict[str, str]) -> dict[str, Any]:
    """Parse only explicit answer fields or one unambiguous final-answer line."""
    objects = _json_objects(raw)
    candidates: list[tuple[list[str], str, str | None, bool, Any]] = []
    for value in objects:
        field = "answer_set" if "answer_set" in value else "candidates" if "candidates" in value else None
        if field is None:
            continue
        normalized, member_sources = _normalize(value[field], names)
        if normalized is None:
            continue
        explanation = value.get("explanation", value.get("reasoning"))
        strict = (
            field == "answer_set"
            and set(value) == {"answer_set", "explanation"}
            and isinstance(explanation, str)
            and all(source == "label" for source in member_sources)
        )
        candidates.append((normalized, f"json_{field}", explanation if isinstance(explanation, str) else None, strict, value[field]))
    unique = {tuple(row[0]) for row in candidates}
    if len(unique) == 1:
        best = next((row for row in candidates if row[3]), candidates[0])
        return {
            "recognized": True,
            "answer_set": best[0],
            "raw_answer": best[4],
            "explanation": best[2],
            "parse_source": best[1],
            "strict_json": best[3],
            "ambiguity_reason": None,
        }
    if len(unique) > 1:
        return {
            "recognized": False,
            "answer_set": None,
            "raw_answer": None,
            "explanation": None,
            "parse_source": "conflicting_json_answers",
            "strict_json": False,
            "ambiguity_reason": "multiple conflicting explicit JSON answer sets",
        }

    pattern = re.compile(r"(?im)^\s*(?:final\s+)?answer(?:\s+set)?\s*:\s*\[([^\]\n]*)\]\s*$")
    matches = pattern.findall(raw)
    fallback: set[tuple[str, ...]] = set()
    for body in matches:
        raw_values = [] if not body.strip() else [part.strip().strip("'\"") for part in body.split(",")]
        normalized, _ = _normalize(raw_values, names)
        if normalized is not None:
            fallback.add(tuple(normalized))
    if len(fallback) == 1:
        answer = list(next(iter(fallback)))
        return {
            "recognized": True,
            "answer_set": answer,
            "raw_answer": matches[-1],
            "explanation": None,
            "parse_source": "explicit_final_line_fallback",
            "strict_json": False,
            "ambiguity_reason": None,
        }
    return {
        "recognized": False,
        "answer_set": None,
        "raw_answer": None,
        "explanation": None,
        "parse_source": "ambiguous_fallback" if len(fallback) > 1 else "unrecognized",
        "strict_json": False,
        "ambiguity_reason": "conflicting explicit final lines" if len(fallback) > 1 else "no explicit unambiguous answer field",
    }

