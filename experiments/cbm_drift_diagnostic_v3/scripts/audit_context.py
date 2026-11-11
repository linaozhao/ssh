"""Recount real saved prompts; keep incorrect legacy metadata unchanged."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cbm_drift_v3.common import read_json, sha256_file, write_json, write_jsonl


def audit_context(config: dict, result: Path) -> dict:
    """Use explicit token-ID output and compare it with provider prompt usage."""
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(config["model"]["weights_path"], local_files_only=True)
    limit = config["model"]["deployment"]["max_model_len"]
    budget = config["generation"]["max_tokens"]
    rows = []
    for stage in ("protocol", "mad"):
        for path in sorted((result / stage / "records").glob("*.json")):
            record = read_json(path)
            if not record["api_success"]:
                continue
            ids = tokenizer.apply_chat_template(record["messages"], tokenize=True,
                                               add_generation_prompt=True, enable_thinking=False,
                                               return_dict=False)
            if not isinstance(ids, list) or any(type(token) is not int for token in ids):
                raise ValueError("Expected a single flat list of token IDs")
            count = len(ids)
            provider_count = (record.get("usage") or {}).get("prompt_tokens")
            rows.append({"stage": stage, "request_id": record["request_id"],
                         "stored_input_tokens_counted": record["input_tokens_counted"],
                         "recomputed_input_tokens": count, "provider_prompt_tokens": provider_count,
                         "provider_matches_recount": count == provider_count,
                         "stored_metadata_matches": count == record["input_tokens_counted"],
                         "output_budget": budget, "context_limit": limit,
                         "within_reserved_context": count + budget <= limit,
                         "finish_reason": record.get("finish_reason")})
    summary = {"status": "passed" if rows and all(r["provider_matches_recount"] and r["within_reserved_context"] for r in rows) else "failed",
               "audited_responses": len(rows),
               "stored_metadata_mismatches": sum(not r["stored_metadata_matches"] for r in rows),
               "provider_count_mismatches": sum(not r["provider_matches_recount"] for r in rows),
               "context_violations": sum(not r["within_reserved_context"] for r in rows),
               "max_recomputed_input_tokens": max((r["recomputed_input_tokens"] for r in rows), default=None),
               "max_model_len": limit, "reserved_output_tokens": budget,
               "raw_records_modified": False, "new_inference_calls": 0,
               "scope": "Input integrity/context audit, not endorsement of the original metadata counter.",
               "counter_issue": "This transformers version returns BatchEncoding by default; len(...) measured its two keys. Explicit return_dict=False counts token IDs."}
    write_jsonl(result / "context_token_recount.jsonl", rows)
    write_json(result / "context_validation.json", summary)
    archives = {"runner.py": "executed_runner_before_token_fix.py",
                "runtime.py": "executed_runtime_before_shutdown_fix.py"}
    if all((result / path).exists() for path in archives.values()):
        executed = read_json(result / "mad/execution_manifest.json")["code"]
        sources = {}
        for name, expected in executed.items():
            path = result / archives[name] if name in archives else ROOT / "src/cbm_drift_v3" / name
            if sha256_file(path) != expected:
                raise ValueError(f"Executed source snapshot mismatch: {name}")
            sources[name] = {"executed_sha256": expected, "preserved_path": str(path.relative_to(ROOT)),
                             "current_sha256": sha256_file(ROOT / "src/cbm_drift_v3" / name)}
        write_json(result / "post_run_compatibility_fixes.json", {
            "executed_sources_preserved": True, "sources": sources,
            "mad_execution_status": read_json(result / "mad/status.json")["status"],
            "raw_records_modified": False, "extra_inference_calls": 0,
            "fixes": ["Explicit token-ID return instead of BatchEncoding key count.",
                      "Startup deadline is not reused during a verified service's graceful shutdown."],
            "resume_policy": "Completed run is read-only. Changed source fingerprints intentionally reject generation resume; use a new run_id for future model experiments."})
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    config = read_json(args.config)
    summary = audit_context(config, ROOT / "results" / config["run_id"])
    print(json.dumps(summary, indent=2))
    return 0 if summary["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
