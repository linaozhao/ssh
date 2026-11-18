"""Small immutable-artifact helpers for CPU-only controlled experiments."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(REPO / 'src'))
sys.path.insert(0, str(REPO / 'experiments/cbm_drift_diagnostic_v3/src'))


def digest(value: Any) -> str:
    """Hash canonical JSON, not Python repr."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def read_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write_json(path: Path, value: Any, immutable: bool = False) -> None:
    """Optionally refuse to replace differing frozen content."""
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n'
    write_text(path, text, immutable)


def write_text(path: Path, text: str, immutable: bool = False) -> None:
    if immutable and path.exists() and path.read_text() != text:
        raise ValueError(f'Frozen artifact differs: {path}')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def write_rows(path: Path, values: list[dict], immutable: bool = False) -> None:
    write_text(path, ''.join(json.dumps(v, sort_keys=True, ensure_ascii=False) + '\n' for v in values), immutable)


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def span(text: str, quote: str) -> dict:
    if text.count(quote) != 1:
        raise ValueError('Reference quotation must occur exactly once')
    start = text.index(quote)
    return {'quote': quote, 'start': start, 'end': start + len(quote)}
