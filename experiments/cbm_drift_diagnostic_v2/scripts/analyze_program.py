#!/usr/bin/env python3
"""Generate deterministic message and event diagnostics."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cbm_drift_v2.diagnostics import analyze_program

if __name__ == "__main__":
    print(json.dumps(analyze_program(ROOT), indent=2))
