"""Conservative parsers for single-choice and candidate-set responses."""

from __future__ import annotations

import json
import re
from typing import Any

from cbm_attr_v1.common import LABELS


def _json_objects(text: str) -> list[dict[str, Any]]:
    decoder = json.JSONDecoder()
    objects: list[dict[str, Any]] = []
    for start, character in enumerate(text):
        if character != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text[start:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            objects.append(value)
    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    for value in objects:
        fingerprint = json.dumps(value, sort_keys=True, ensure_ascii=False)
        if fingerprint not in seen:
            unique.append(value)
            seen.add(fingerprint)
    return unique


def _normalize_member(value: Any, names: dict[str, str]) -> tuple[str | None, str]:
    text = str(value).strip()
    upper = text.upper()
    if upper in LABELS:
        return upper, "label"
    matches = [label for label, name in names.items() if text.casefold() == str(name).strip().casefold()]
    if len(matches) == 1:
        return matches[0], "full_name"
    return None, "unknown"


def parse_candidate_set(raw: str, names: dict[str, str]) -> dict[str, Any]:
    """Parse only explicit final candidate fields, never labels in explanations."""
    stripped = raw.strip()
    strict_json = False
    strict_schema = False
    duplicate_members: list[str] = []
    unknown_members: list[str] = []
    mapping_sources: list[str] = []
    candidates_values: list[list[Any]] = []
    try:
        exact = json.loads(stripped)
        strict_json = isinstance(exact, dict)
        objects = [exact] if isinstance(exact, dict) else []
    except json.JSONDecodeError:
        objects = _json_objects(stripped)
    for value in objects:
        if isinstance(value.get("candidates"), list):
            candidates_values.append(value["candidates"])
            if value is objects[0] and strict_json:
                strict_schema = set(value) == {"candidates", "reasoning"} and isinstance(value.get("reasoning"), str)

    matches = re.findall(
        r"(?im)^\s*(?:final\s+)?candidates?\s*[:=]\s*\[([^\]]*)\]\s*[.!]?\s*$",
        stripped,
    )
    for match in matches:
        values = [token.strip().strip('"\'') for token in match.split(",") if token.strip()]
        candidates_values.append(values)
    fallback_used = bool(matches)

    normalized_sets: list[tuple[str, ...]] = []
    for values in candidates_values:
        normalized: list[str] = []
        local_unknown: list[str] = []
        local_sources: list[str] = []
        for value in values:
            label, source = _normalize_member(value, names)
            if label is None:
                local_unknown.append(str(value))
            else:
                normalized.append(label)
                local_sources.append(source)
        duplicates = sorted({label for label in normalized if normalized.count(label) > 1})
        if local_unknown or duplicates:
            unknown_members.extend(local_unknown)
            duplicate_members.extend(duplicates)
            continue
        normalized_sets.append(tuple(sorted(normalized)))
        mapping_sources.extend(local_sources)

    distinct = sorted(set(normalized_sets))
    ambiguous = len(distinct) > 1
    recognized = len(distinct) == 1 and not unknown_members and not duplicate_members
    candidates = list(distinct[0]) if recognized else None
    reasoning = None
    if objects and isinstance(objects[0].get("reasoning"), str):
        reasoning = objects[0]["reasoning"]
    return {
        "recognized": recognized,
        "candidates": candidates,
        "strict_json": strict_json,
        "strict_schema": strict_schema,
        "parse_source": "strict_json" if strict_schema and recognized else ("json_extraction" if objects and recognized else ("explicit_final_fallback" if fallback_used and recognized else "unrecognized")),
        "ambiguous": ambiguous,
        "unknown_members": sorted(set(unknown_members)),
        "duplicate_members": sorted(set(duplicate_members)),
        "name_mapping_used": "full_name" in mapping_sources,
        "reasoning": reasoning,
    }


def parse_single_choice(raw: str, names: dict[str, str]) -> dict[str, Any]:
    """Parse an explicit answer field without reading labels from reasoning."""
    stripped = raw.strip()
    strict_json = False
    objects: list[dict[str, Any]]
    try:
        exact = json.loads(stripped)
        strict_json = isinstance(exact, dict)
        objects = [exact] if isinstance(exact, dict) else []
    except json.JSONDecodeError:
        objects = _json_objects(stripped)
    answers: list[tuple[str, str]] = []
    for value in objects:
        if "answer" in value:
            normalized, source = _normalize_member(value["answer"], names)
            if normalized:
                answers.append((normalized, source))
    if not answers:
        matches = re.findall(r"(?im)^\s*(?:final\s+)?answer\s*[:=]\s*([A-D])\s*[.!]?\s*$", stripped)
        answers.extend((match.upper(), "label") for match in matches)
    distinct = sorted({answer for answer, _ in answers})
    recognized = len(distinct) == 1
    reasoning = objects[0].get("reasoning") if objects and isinstance(objects[0].get("reasoning"), str) else None
    strict_schema = False
    if strict_json and objects:
        confidence = objects[0].get("confidence")
        strict_schema = (
            set(objects[0]) == {"answer", "reasoning", "confidence"}
            and isinstance(objects[0].get("reasoning"), str)
            and isinstance(confidence, (int, float))
            and not isinstance(confidence, bool)
            and 0 <= confidence <= 1
        )
    return {
        "recognized": recognized,
        "answer": distinct[0] if recognized else None,
        "strict_json": strict_json,
        "strict_schema": strict_schema,
        "parse_source": "strict_json" if strict_json and recognized else ("json_extraction" if objects and recognized else ("explicit_final_fallback" if recognized else "unrecognized")),
        "ambiguous": len(distinct) > 1,
        "name_mapping_used": recognized and any(source == "full_name" for _, source in answers),
        "reasoning": reasoning,
    }
