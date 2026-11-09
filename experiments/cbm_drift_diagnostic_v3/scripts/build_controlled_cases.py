"""Build the frozen R2 controlled set without API or GPU access."""
from pathlib import Path
import sys
import json

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cbm_drift_v3.common import read_jsonl
from cbm_drift_v3.controlled_cases import build_controlled

if __name__ == "__main__":
    print(json.dumps(build_controlled(read_jsonl(ROOT / "data/evidence_sequences.jsonl"), ROOT / "data/controlled"), indent=2))
