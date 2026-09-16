"""Shared constants and deterministic I/O helpers for CBM-Attr v1."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

LABELS = ("A", "B", "C", "D")
EXPERIMENT_VERSION = "cbm_attr_v1.0"
PROMPT_VERSION = "cbm_attr_set_v1.2"
PARSER_VERSION = "cbm_attr_parser_v1"


def canonical_json(value: Any) -> str:
    """Return stable compact JSON used for content fingerprints."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(value: Any) -> str:
    """Hash a JSON-compatible value deterministically."""
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256_text(value: str) -> str:
    """Hash UTF-8 text."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def stable_seed(*parts: object) -> int:
    """Derive a reproducible 31-bit seed from arbitrary identifiers."""
    digest = hashlib.sha256("|".join(map(str, parts)).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % (2**31)


def read_json(path: Path) -> Any:
    """Read one UTF-8 JSON document."""
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    """Write pretty, deterministic UTF-8 JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read nonempty JSONL records."""
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    """Write JSONL atomically enough for deterministic generated artifacts."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def file_sha256(path: Path) -> str:
    """Hash a file without loading it all into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def difficulty_cell(item: dict[str, Any]) -> str:
    """Return the canonical CL x DS x IL cell identifier."""
    factors = item["difficulty_factors"]
    return "__".join(
        (factors["constraint_load"], factors["distractor_similarity"], factors["information_load"])
    )
