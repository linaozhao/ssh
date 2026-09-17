#!/usr/bin/env python3
"""Freeze the 18-item pilot and both logical request plans."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path[:0] = [str(ROOT / "src"), str(REPO / "src"), str(REPO / "experiments/cbm_attr_v1/src")]

from mad_drift_pilot.prepare import prepare  # noqa: E402


if __name__ == "__main__":
    print(json.dumps(prepare(ROOT, REPO), indent=2, ensure_ascii=False))
