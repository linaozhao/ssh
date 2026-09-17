"""Shared deterministic IO, hashing, and identity helpers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


LABELS = ("A", "B", "C", "D")
AGENTS = ("agent_1", "agent_2", "agent_3")


def read_json(path: str | Path) -> dict[str, Any]:
    """Read one JSON object."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, value: Any) -> None:
    """Write stable, human-readable JSON."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """Read JSON Lines records."""
    with Path(path).open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: str | Path, rows: Iterable[dict[str, Any]]) -> None:
    """Write JSON Lines records atomically enough for generated artifacts."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def sha256_json(value: Any) -> str:
    """Hash a JSON-serializable value using canonical serialization."""
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def file_sha256(path: str | Path) -> str:
    """Hash a file in chunks."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_seed(*parts: object) -> int:
    """Derive a deterministic 31-bit request seed."""
    joined = "\x1f".join(str(part) for part in parts)
    return int(hashlib.sha256(joined.encode("utf-8")).hexdigest()[:8], 16) & 0x7FFFFFFF


def difficulty_cell(item: dict[str, Any]) -> str:
    """Return the frozen CL x DS x source-IL cell."""
    factors = item["difficulty_factors"]
    return "__".join(
        (factors["constraint_load"], factors["distractor_similarity"], factors["information_load"])
    )

