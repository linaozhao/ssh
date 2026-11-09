"""Conservative set parsing, keeping JSON conformance separate from recognition."""

from __future__ import annotations

import json
import re
from typing import Any

from .common import LABELS


def parse_answer_set(raw: str, names: dict[str, str]) -> dict[str, Any]:
    """Reject conflicting explicit conclusions and never guess from explanation."""
    answers: list[tuple[list[str], Any, str | None, str]] = []
    strict = False
    try:
        whole = json.loads(raw)
    except (ValueError, TypeError):
        whole = None
    decoder = json.JSONDecoder()
    objects = []
    for i, char in enumerate(raw):
        if char == "{":
            try:
                obj, _ = decoder.raw_decode(raw[i:])
            except ValueError:
                continue
            if isinstance(obj, dict) and "answer_set" in obj:
                objects.append(obj)

    def normalize(value: Any) -> list[str] | None:
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            return None
        result = []
        for text in value:
            label = text.strip().upper()
            if label not in LABELS:
                matches = [c for c, name in names.items() if name.casefold() == text.strip().casefold()]
                if len(matches) != 1:
                    return None
                label = matches[0]
            if label in result:
                return None
            result.append(label)
        return sorted(result)

    malformed_explicit = False
    for obj in objects:
        answer = normalize(obj["answer_set"])
        if answer is None:
            malformed_explicit = True
        else:
            answers.append((answer, obj["answer_set"], obj.get("explanation"), "json_answer_set"))
    for match in re.finditer(r"(?im)^\s*(?:final\s+)?answer(?:\s+set)?\s*:\s*\[([^\]\n]*)\]\s*$", raw):
        values = [x.strip().strip('\"\'') for x in match[1].split(",")] if match[1].strip() else []
        answer = normalize(values)
        if answer is None:
            malformed_explicit = True
        else:
            answers.append((answer, values, None, "explicit_final_line"))
    unique = {tuple(r[0]) for r in answers}
    recognized = len(unique) == 1 and not malformed_explicit
    if recognized and isinstance(whole, dict):
        strict = (set(whole) == {"answer_set", "explanation"} and isinstance(whole.get("explanation"), str)
                  and isinstance(whole.get("answer_set"), list) and all(v in LABELS for v in whole["answer_set"]))
    best = answers[0] if recognized else (None, None, None, "ambiguous" if answers else "unrecognized")
    return {"recognized": recognized, "answer_set": best[0], "raw_answer": best[1], "explanation": best[2],
            "strict_json": strict, "parse_source": best[3],
            "ambiguity_reason": None if recognized else "No unique valid explicit answer set"}
