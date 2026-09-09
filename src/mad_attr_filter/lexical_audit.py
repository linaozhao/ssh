"""Simple lexical overlap audit for English constraint and candidate realizations."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from statistics import mean
from typing import Any

TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    return set(TOKEN_RE.findall(text.lower()))


def _normalized_text(text: str) -> str:
    return " ".join(TOKEN_RE.findall(text.lower()))


def token_overlap(left: str, right: str) -> float:
    """Return normalized token overlap between two strings."""
    left_tokens = _tokens(left)
    right_tokens = _tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / min(len(left_tokens), len(right_tokens))


def build_lexical_audit(samples: Sequence[Mapping[str, Any]], *, high_overlap_threshold: float = 0.8) -> dict[str, Any]:
    """Audit constraint/candidate lexical overlap."""
    overlaps: list[float] = []
    exact_phrase_matches: list[dict[str, object]] = []
    high_overlap_pairs: list[dict[str, object]] = []

    for sample in samples:
        constraint_by_attribute = {
            str(constraint["attribute"]): constraint for constraint in sample.get("constraints", [])
        }
        for label, entity in sample.get("entities", {}).items():
            name = str(entity.get("name", ""))
            for fact in entity.get("displayed_facts", []):
                attribute = str(fact["attribute"])
                candidate_text = str(fact["text"])
                constraint = constraint_by_attribute[attribute]
                constraint_text = str(constraint["natural_language"])
                overlap = token_overlap(constraint_text, candidate_text)
                overlaps.append(overlap)
                record = {
                    "item_id": sample["item_id"],
                    "option": label,
                    "attribute": attribute,
                    "candidate_name": name,
                    "constraint_text": constraint_text,
                    "candidate_text": candidate_text,
                    "overlap": overlap,
                }
                if _normalized_text(constraint_text) == _normalized_text(candidate_text):
                    exact_phrase_matches.append(record)
                if overlap >= high_overlap_threshold:
                    high_overlap_pairs.append(record)

    return {
        "exact_phrase_match_count": len(exact_phrase_matches),
        "high_overlap_pair_count": len(high_overlap_pairs),
        "mean_constraint_candidate_overlap": mean(overlaps) if overlaps else 0.0,
        "num_pairs": len(overlaps),
        "high_overlap_threshold": high_overlap_threshold,
        "exact_phrase_matches": exact_phrase_matches,
        "high_overlap_pairs": high_overlap_pairs,
    }

