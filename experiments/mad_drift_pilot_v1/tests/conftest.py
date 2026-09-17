"""Test import paths for the independent experiment package."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path[:0] = [str(ROOT / "src"), str(REPO / "src"), str(REPO / "experiments/cbm_attr_v1/src")]

