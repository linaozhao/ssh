#!/usr/bin/env python3
"""Run resumable homogeneous three-agent, three-round MAD trajectories."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import sys
import threading
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mad_attr_filter.io import load_json, read_jsonl, write_jsonl
from mad_attr_filter.mad_pilot import (
    append_progress_record,
    build_debate_prompt,
    build_mad_response_record,
    build_round_zero_prompt,
    load_mad_progress,
    progress_key,
)
from mad_attr_filter.single_agent import call_with_retries, model_alias


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the small baseline homogeneous MAD pilot.")
    parser.add_argument("--dataset", default="data/pilot_en_v3.jsonl")
    parser.add_argument("--manifest", default="results/mad_pilot_manifest.jsonl")
    parser.add_argument("--config", default="config/mad_pilot_config.json")
    parser.add_argument("--progress-output", default="results/mad_pilot_progress.jsonl")
    parser.add_argument("--model-family", choices=("all", "qwen", "llama"), default="all")
    parser.add_argument("--limit-items", type=int, default=None)
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from call-level checkpoints (also the default behavior).",
    )
    parser.add_argument(
        "--retry-api-failures",
        action="store_true",
        help="Remove and retry API failures; formatting failures are never regenerated.",
    )
    return parser.parse_args()


def _execute_call(
    *,
    sample: dict[str, Any],
    manifest_record: dict[str, Any],
    model_config: dict[str, Any],
    agent_id: str,
    round_number: int,
    seed: int,
    prompt: str,
    peer_context: list[dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, Any]:
    raw_response, api_metadata, request_error = call_with_retries(
        model_config=model_config,
        prompt=prompt,
        temperature=float(config["temperature"]),
        top_p=float(config["top_p"]),
        max_tokens=int(config["max_tokens"]),
        seed=seed,
        timeout_seconds=int(config.get("request_timeout_seconds", 120)),
        max_retries=int(config.get("max_retries", 2)),
        retry_sleep_seconds=float(config.get("retry_sleep_seconds", 2)),
    )
    return build_mad_response_record(
        sample=sample,
        manifest_record=manifest_record,
        model_config=model_config,
        agent_id=agent_id,
        round_number=round_number,
        seed=seed,
        prompt=prompt,
        peer_context=peer_context,
        generation_config=config,
        raw_response=raw_response,
        api_metadata=api_metadata,
        request_error=request_error,
    )


def main() -> int:
    args = parse_args()
    config = load_json(ROOT / args.config)
    samples = read_jsonl(ROOT / args.dataset)
    sample_by_id = {str(sample["item_id"]): sample for sample in samples}
    manifest = read_jsonl(ROOT / args.manifest)
    if args.limit_items is not None:
        manifest = manifest[: args.limit_items]
    model_configs = [
        model_config
        for model_config in config["models"]
        if args.model_family == "all" or model_alias(model_config) == args.model_family
    ]
    if not model_configs:
        raise ValueError(f"No model config matched {args.model_family!r}")
    agents = [str(agent_id) for agent_id in config["agents"]]
    rounds = [int(round_number) for round_number in config["rounds"]]
    if rounds != [0, 1, 2] or len(agents) != 3:
        raise ValueError("The baseline pilot requires exactly agents A1-A3 and rounds 0-2")

    progress_path = ROOT / args.progress_output
    progress = load_mad_progress(progress_path)
    if args.retry_api_failures:
        retained = {
            key: record
            for key, record in progress.items()
            if not record.get("metadata", {}).get("request_error")
        }
        removed = len(progress) - len(retained)
        if removed:
            write_jsonl(progress_path, list(retained.values()))
            progress = retained
            print(f"Removed {removed} API failure checkpoints for retry.")

    selected_item_ids = {str(record["item_id"]) for record in manifest}
    selected_families = {model_alias(model_config) for model_config in model_configs}
    relevant_existing = {
        key: record
        for key, record in progress.items()
        if key[0] in selected_item_ids and key[1] in selected_families
    }
    expected_calls = len(manifest) * len(model_configs) * len(agents) * len(rounds)
    print(f"Expected calls for this invocation: {expected_calls}")
    print(f"Already completed: {len(relevant_existing)}")

    lock = threading.Lock()

    def save_record(record: dict[str, Any]) -> None:
        key = progress_key(record)
        with lock:
            if key in progress:
                return
            append_progress_record(progress_path, record, threading.Lock())
            progress[key] = record
            completed = sum(
                key_[0] in selected_item_ids and key_[1] in selected_families for key_ in progress
            )
            status = "ok" if record["parse_success"] else "failed"
            print(
                f"{completed}/{expected_calls} {record['item_id']} {record['model_family']} "
                f"{record['agent_id']} R{record['round']} {status}",
                flush=True,
            )

    def run_family(model_config: dict[str, Any]) -> None:
        family = model_alias(model_config)
        for manifest_record in manifest:
            item_id = str(manifest_record["item_id"])
            sample = sample_by_id[item_id]
            for round_number in rounds:
                previous_round: dict[str, dict[str, Any]] = {}
                if round_number > 0:
                    for agent_id in agents:
                        previous_key = (item_id, family, agent_id, round_number - 1)
                        if previous_key not in progress:
                            raise RuntimeError(f"Missing prerequisite checkpoint {previous_key}")
                        previous_round[agent_id] = progress[previous_key]

                call_specs: list[dict[str, Any]] = []
                for agent_id in agents:
                    key = (item_id, family, agent_id, round_number)
                    if key in progress:
                        continue
                    if round_number == 0:
                        prompt = build_round_zero_prompt(str(sample["question"]))
                        peer_context: list[dict[str, Any]] = []
                    else:
                        prompt, peer_context = build_debate_prompt(
                            str(sample["question"]),
                            own_agent_id=agent_id,
                            previous_round=previous_round,
                        )
                    seed = int(config["agent_round_seeds"][agent_id][str(round_number)])
                    call_specs.append(
                        {
                            "sample": sample,
                            "manifest_record": manifest_record,
                            "model_config": model_config,
                            "agent_id": agent_id,
                            "round_number": round_number,
                            "seed": seed,
                            "prompt": prompt,
                            "peer_context": peer_context,
                            "config": config,
                        }
                    )
                if not call_specs:
                    continue
                if config.get("parallel_agents_per_round", True):
                    with concurrent.futures.ThreadPoolExecutor(max_workers=len(call_specs)) as executor:
                        for record in executor.map(lambda kwargs: _execute_call(**kwargs), call_specs):
                            save_record(record)
                else:
                    for call_spec in call_specs:
                        save_record(_execute_call(**call_spec))

    if config.get("parallel_model_families", True) and len(model_configs) > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(model_configs)) as executor:
            list(executor.map(run_family, model_configs))
    else:
        for model_config in model_configs:
            run_family(model_config)

    final_completed = sum(
        key[0] in selected_item_ids and key[1] in selected_families for key in progress
    )
    print(json.dumps({"expected_calls": expected_calls, "completed_calls": final_completed}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
