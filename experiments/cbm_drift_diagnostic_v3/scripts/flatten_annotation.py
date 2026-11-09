"""Validate and flatten later human annotations; never infer missing labels."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cbm_drift_v3.common import read_jsonl, freeze_jsonl
from cbm_drift_v3.annotation import flatten_annotation

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    allowed = {r["message_id"] for r in read_jsonl(ROOT / "annotation/deferred_real/sampling_manifest.jsonl")}
    freeze_jsonl(args.output, flatten_annotation(read_jsonl(args.input), allowed))
