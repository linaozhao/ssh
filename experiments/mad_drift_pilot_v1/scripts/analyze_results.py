#!/usr/bin/env python3
"""Analyze protocol checking and MAD trajectories, then write the report."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path[:0] = [str(ROOT / "src"), str(REPO / "src"), str(REPO / "experiments/cbm_attr_v1/src")]

from mad_drift_pilot.analysis import analyze_mad, analyze_protocol, write_report  # noqa: E402


if __name__ == "__main__":
    protocol = analyze_protocol(ROOT, REPO)
    analysis = analyze_mad(ROOT)
    write_report(ROOT, protocol, analysis)
    print(json.dumps({"protocol_records": protocol["new_records"], **analysis["integrity"]}, indent=2))

