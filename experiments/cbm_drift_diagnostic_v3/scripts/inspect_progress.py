"""Read live execution artifacts without credentials or model calls."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cbm_drift_v3.common import read_json, read_jsonl


def inspect(result: Path, judge_subdir: str) -> dict:
    """Separate persisted responses, technical validation and pending requests."""
    summary = {}
    for stage, expected in (("protocol", 108), ("mad", 1188)):
        directory = result / stage
        rows = [read_json(p) for p in (directory / "records").glob("*.json")]
        summary[stage] = {"expected": expected, "records": len(rows),
                          "api_success": sum(r.get("api_success", False) for r in rows),
                          "recognized": sum(r.get("parsed", {}).get("recognized", False) for r in rows),
                          "truncated": sum(r.get("finish_reason") == "length" for r in rows),
                          "failed_records": sum(not r.get("api_success", False) for r in rows),
                          "not_recorded": expected - len(rows)}
    directory = result / judge_subdir
    rows = read_jsonl(directory / "outputs.jsonl") if (directory / "outputs.jsonl").exists() else []
    attempts = read_jsonl(directory / "attempts.jsonl") if (directory / "attempts.jsonl").exists() else []
    summary["controlled_judge"] = {"expected": 144, "terminal": len(rows), "attempts": len(attempts),
                                   "api_success": sum(r.get("api_success", False) for r in rows),
                                   "technical_valid": sum(all(r.get(k) for k in ("api_success", "schema_valid", "quote_valid", "object_valid")) and r.get("finish_reason") != "length" for r in rows),
                                   "status_counts": dict(Counter(r["status"] for r in rows)),
                                   "tokens": {k: sum((r.get("usage") or {}).get(k, 0) for r in rows) for k in ("prompt_tokens", "completion_tokens", "total_tokens")},
                                   "not_terminal": 144 - len(rows)}
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("--judge-subdir", default="controlled_judge_official_flash_parser_v2")
    args = parser.parse_args()
    print(json.dumps(inspect(args.result, args.judge_subdir), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
