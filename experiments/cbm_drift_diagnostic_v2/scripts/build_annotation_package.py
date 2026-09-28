#!/usr/bin/env python3
"""Export Judge-blind annotation materials for all trajectories."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cbm_drift_v2.annotation import export_annotation_package

if __name__ == "__main__":
    print(json.dumps(export_annotation_package(ROOT), indent=2))
