"""Inject a current official key via a hidden prompt and run the bounded queue."""
from __future__ import annotations

import argparse
import getpass
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cbm_drift_v3.common import read_json, read_jsonl, write_json
from cbm_drift_v3.judge import run_controlled_judge
from cbm_drift_v3.evaluation import evaluate_controlled


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    config = read_json(args.config)
    if config["base_url"] != "https://api.deepseek.com" or config["model_name"] != "deepseek-flash":
        raise ValueError("This secret-input entry point is limited to the authorized official model")
    os.environ["JUDGE_API_KEY_V3_NEW"] = getpass.getpass("Official DeepSeek API key (hidden): ")
    try:
        status = run_controlled_judge(config, args.output_dir, enabled=True, resume=args.resume)
        write_json(args.output_dir / "status.json", status)
        outputs = args.output_dir / "outputs.jsonl"
        evaluation = evaluate_controlled(read_jsonl(outputs) if outputs.exists() else [], read_jsonl(ROOT / "data/controlled/expected_labels.jsonl"))
        write_json(args.output_dir / "evaluation.json", evaluation)
        print(json.dumps({"judge": status, "evaluation_status": evaluation["status"]}, ensure_ascii=False))
    finally:
        os.environ.pop("JUDGE_API_KEY_V3_NEW", None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
