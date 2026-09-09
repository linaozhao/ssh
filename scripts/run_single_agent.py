#!/usr/bin/env python3
"""Run independent single-agent calls on a JSONL dataset."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mad_attr_filter.io import load_json, read_jsonl, write_jsonl
from mad_attr_filter.single_agent import (
    build_output_record,
    build_prompt,
    call_with_retries,
    expected_run_count,
    load_completed_keys,
    model_alias,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run single-agent OpenAI-compatible screening.")
    parser.add_argument("--dataset", default="data/pilot_en_v3.jsonl")
    parser.add_argument("--config", default="config/single_agent_config.json")
    parser.add_argument("--output", default="results/single_agent_outputs.jsonl")
    parser.add_argument("--limit-items", type=int, default=None)
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from existing output (this is also the default behavior).",
    )
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Retry API failures only; malformed model responses remain completed runs.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dataset_path = ROOT / args.dataset
    config_path = ROOT / args.config
    output_path = ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    samples = read_jsonl(dataset_path)
    if args.limit_items is not None:
        samples = samples[: args.limit_items]
    config = load_json(config_path)

    if args.retry_failed and output_path.exists():
        existing_records = read_jsonl(output_path)
        retained_records = [
            record
            for record in existing_records
            if not record.get("metadata", {}).get("request_error")
        ]
        if len(retained_records) != len(existing_records):
            write_jsonl(output_path, retained_records)
            print(f"Removed {len(existing_records) - len(retained_records)} API failure records.")

    completed = load_completed_keys(output_path, retry_failed=args.retry_failed)
    generation_config = {
        "temperature": float(config["temperature"]),
        "top_p": float(config["top_p"]),
        "max_tokens": int(config["max_tokens"]),
    }
    total_expected = expected_run_count(samples, config)
    print(f"Expected runs: {total_expected}")
    print(f"Already completed: {len(completed)}")

    written = 0
    with output_path.open("a", encoding="utf-8") as file:
        for sample in samples:
            prompt = build_prompt(str(sample["question"]))
            for model_config in config["models"]:
                alias = model_alias(model_config)
                for run_id, seed in enumerate(config["seeds"], start=1):
                    key = (str(sample["item_id"]), alias, int(run_id))
                    if key in completed:
                        continue
                    raw_response, api_metadata, request_error = call_with_retries(
                        model_config=model_config,
                        prompt=prompt,
                        temperature=float(generation_config["temperature"]),
                        top_p=float(generation_config["top_p"]),
                        max_tokens=int(generation_config["max_tokens"]),
                        seed=int(seed),
                        timeout_seconds=int(config.get("request_timeout_seconds", 120)),
                        max_retries=int(config.get("max_retries", 2)),
                        retry_sleep_seconds=float(config.get("retry_sleep_seconds", 2)),
                    )
                    record = build_output_record(
                        sample=sample,
                        model_config=model_config,
                        run_id=int(run_id),
                        seed=int(seed),
                        generation_config=generation_config,
                        raw_response=raw_response,
                        api_metadata=api_metadata,
                        request_error=request_error,
                    )
                    file.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
                    file.write("\n")
                    file.flush()
                    completed.add(key)
                    written += 1
                    status = "ok" if record["parse_success"] else "failed"
                    print(
                        f"{len(completed)}/{total_expected} {sample['item_id']} "
                        f"{alias} run={run_id} seed={seed} {status}"
                    )

    print(f"Wrote {written} new records to {output_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
