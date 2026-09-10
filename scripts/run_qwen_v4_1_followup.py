#!/usr/bin/env python3
# ruff: noqa: E402
"""Run one frozen Qwen v4.1 follow-up experiment with resume checks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mad_attr_filter.io import load_json, read_jsonl, write_json
from mad_attr_filter.qwen_followup import build_followup_fingerprints
from mad_attr_filter.qwen_followup_runner import (
    assert_manifest_compatible,
    make_manifest,
    materialize_experiment_config,
    probe_service,
    run_experiment,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", default="config/qwen_v4_1_followup_config.json"
    )
    parser.add_argument(
        "--experiment",
        required=True,
        choices=("position_order", "information_load", "extension"),
    )
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def _resolve(path: str) -> Path:
    value = Path(path)
    return value if value.is_absolute() else ROOT / value


def main() -> int:
    args = parse_args()
    full_config = load_json(_resolve(args.config))
    config = materialize_experiment_config(full_config, args.experiment)
    dataset_path = _resolve(str(config["dataset"]))
    results_dir = _resolve(str(config["results_dir"]))
    output_path = results_dir / "single_agent_outputs.jsonl"
    manifest_path = results_dir / "experiment_manifest.json"
    samples = read_jsonl(dataset_path)
    fingerprints = build_followup_fingerprints(dataset_path, config)

    if output_path.exists() and not args.resume:
        raise ValueError(f"{output_path} exists; pass --resume to audit and continue")
    results_dir.mkdir(parents=True, exist_ok=True)
    if manifest_path.exists():
        manifest = load_json(manifest_path)
        assert_manifest_compatible(manifest, config, fingerprints)
    else:
        manifest = make_manifest(
            dataset_path=dataset_path.relative_to(ROOT),
            samples=samples,
            experiment_config=config,
            fingerprints=fingerprints,
        )
        manifest["service_observation"] = probe_service(config["model"])
        write_json(manifest_path, manifest)

    summary = run_experiment(
        samples=samples,
        experiment_config=config,
        output_path=output_path,
        experiment_fingerprint=fingerprints["experiment_sha256"],
    )
    manifest["run_summary"] = summary
    manifest["status"] = "complete" if summary["complete"] else "incomplete"
    write_json(manifest_path, manifest)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
