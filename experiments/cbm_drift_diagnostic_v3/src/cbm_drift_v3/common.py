"""Canonical hashing, fail-closed frozen outputs and atomic record I/O."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

LABELS = ("A", "B", "C", "D")
AGENTS = ("agent_1", "agent_2", "agent_3")
BRANCHES = ("clean", "update", "noise", "update_noise")
SCHEMA_VERSION = "cbm-drift-v3-r2"


def canonical_json(value: Any) -> str:
    """Serialize without incidental whitespace or key-order differences."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(value: Any) -> str:
    """Fingerprint structured non-secret input."""
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def sha256_file(path: Path) -> str:
    """Stream file bytes, including large legacy records."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_seed(*parts: object) -> int:
    """Derive a stable 31-bit seed, not a promise of backend determinism."""
    return int.from_bytes(hashlib.sha256("\x1f".join(map(str, parts)).encode()).digest()[:8], "big") % 2**31


def read_json(path: Path) -> Any:
    """Read JSON."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read records with line-number errors rather than silently dropping lines."""
    rows = []
    with Path(path).open(encoding="utf-8") as handle:
        for index, line in enumerate(handle, 1):
            if line.strip():
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise ValueError(f"{path}:{index}: expected an object")
                rows.append(row)
    return rows


def atomic_text(path: Path, text: str) -> None:
    """Replace a complete derived output atomically, never a partial record."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_json(path: Path, value: Any) -> None:
    """Write an atomic non-secret JSON artifact."""
    atomic_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write JSON lines atomically."""
    atomic_text(path, "".join(canonical_json(row) + "\n" for row in rows))


def freeze_json(path: Path, value: Any) -> None:
    """Allow exact resume only; refuse overwriting frozen incompatible material."""
    if path.exists():
        if read_json(path) != value:
            raise ValueError(f"Frozen content mismatch: {path}; use a new run/version")
    else:
        write_json(path, value)


def freeze_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    """Keep immutable data and request graphs byte-stable on resume."""
    if path.exists():
        if read_jsonl(path) != rows:
            raise ValueError(f"Frozen content mismatch: {path}; use a new version")
    else:
        write_jsonl(path, rows)
