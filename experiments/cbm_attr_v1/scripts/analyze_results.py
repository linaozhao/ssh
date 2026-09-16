#!/usr/bin/env python3
"""Analyze completed CBM-Attr v1 responses."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(EXPERIMENT / "src")]

from cbm_attr_v1.analysis import analyze  # noqa: E402


if __name__ == "__main__":
    print(json.dumps(analyze(EXPERIMENT), indent=2))
