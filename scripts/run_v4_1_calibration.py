#!/usr/bin/env python3
"""Run stratified preflight or formal v4.1 single-agent calibration."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mad_attr_filter.io import load_json, read_jsonl, write_json, write_jsonl
from mad_attr_filter.v4_calibration import (
    CalibrationError,
    assert_manifest_compatible,
    audit_existing_records,
    build_fingerprints,
    copy_preflight_into_formal,
    expected_keys,
    make_experiment_manifest,
    preflight_manifest_records,
    probe_model_services,
    run_records,
    select_preflight_items,
    summarize_preflight,
)
from mad_attr_filter.v4_validation import validate_v4_pool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run v4.1 single-agent calibration.")
    parser.add_argument("--config", default="config/v4_1_calibration_config.json")
    parser.add_argument("--phase", choices=("preflight", "formal"), required=True)
    parser.add_argument("--resume", action="store_true", help="Audit and resume existing records.")
    parser.add_argument(
        "--reuse-preflight",
        action="store_true",
        help="Copy protocol-identical preflight observations into formal results.",
    )
    return parser.parse_args()


def _resolve(path: str) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else ROOT / candidate


def main() -> int:
    args = parse_args()
    config_path = _resolve(args.config)
    config = load_json(config_path)
    dataset_path = _resolve(str(config["dataset"]))
    results_dir = _resolve(str(config["results_dir"]))
    results_dir.mkdir(parents=True, exist_ok=True)
    samples = read_jsonl(dataset_path)
    validate_v4_pool(samples, expected_items_per_cell=10)

    fingerprints = build_fingerprints(dataset_path, config)
    manifest_path = results_dir / "experiment_manifest.json"
    if manifest_path.exists():
        manifest = load_json(manifest_path)
        assert_manifest_compatible(manifest, fingerprints, str(config["experiment_id"]))
    else:
        manifest = make_experiment_manifest(
            dataset_path=dataset_path.relative_to(ROOT),
            samples=samples,
            config=config,
            fingerprints=fingerprints,
        )
        write_json(manifest_path, manifest)

    if args.phase == "preflight":
        selected = select_preflight_items(samples)
        preflight_manifest = results_dir / "preflight_manifest.jsonl"
        expected_manifest = preflight_manifest_records(selected)
        if preflight_manifest.exists():
            if read_jsonl(preflight_manifest) != expected_manifest:
                raise CalibrationError("Existing preflight manifest differs from deterministic selection")
        else:
            write_jsonl(preflight_manifest, expected_manifest)
        output_path = results_dir / "preflight_outputs.jsonl"
        run_summary = run_records(
            samples=selected,
            config=config,
            output_path=output_path,
            experiment_fingerprint=fingerprints["experiment_sha256"],
            phase="preflight",
        )
        records, _ = audit_existing_records(
            output_path,
            expected_keys(selected, config),
            fingerprints["experiment_sha256"],
        )
        phase_summary = summarize_preflight(records)
        manifest["preflight_summary"] = phase_summary
        manifest["status"]["preflight"] = (
            "complete" if run_summary["completed"] == run_summary["expected"] else "incomplete"
        )
    else:
        output_path = results_dir / "single_agent_outputs.jsonl"
        reused = 0
        if args.reuse_preflight:
            preflight_path = results_dir / "preflight_outputs.jsonl"
            if not preflight_path.exists():
                raise CalibrationError("Cannot reuse preflight because preflight_outputs.jsonl is missing")
            reused = copy_preflight_into_formal(
                preflight_path=preflight_path,
                formal_path=output_path,
                formal_allowed_keys=expected_keys(samples, config),
                experiment_fingerprint=fingerprints["experiment_sha256"],
            )
        run_summary = run_records(
            samples=samples,
            config=config,
            output_path=output_path,
            experiment_fingerprint=fingerprints["experiment_sha256"],
            phase="formal",
        )
        existing_reused = sum(
            record.get("request_metadata", {}).get("reused_from_preflight") is True
            for record in read_jsonl(output_path)
        )
        previous_reused = int(
            manifest.get("formal_summary", {}).get("reused_from_preflight", 0)
        )
        run_summary["reused_from_preflight"] = max(previous_reused, reused, existing_reused)
        manifest["formal_summary"] = run_summary
        manifest["status"]["formal"] = (
            "complete" if run_summary["completed"] == run_summary["expected"] else "incomplete"
        )
        phase_summary = run_summary

    manifest["service_observations"] = probe_model_services(config)
    write_json(manifest_path, manifest)
    print(json.dumps(phase_summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
