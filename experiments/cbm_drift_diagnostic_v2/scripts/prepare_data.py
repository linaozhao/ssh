#!/usr/bin/env python3
"""Freeze the development pool or prepare a later independent split."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXPERIMENT / "src"))

from cbm_drift_v2.common import read_json, read_jsonl, sha256_file, write_json  # noqa: E402
from cbm_drift_v2.prepare import prepare_dataset  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("development", "test"), default="development")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--exclude-manifest", type=Path)
    args = parser.parse_args()
    config_path = EXPERIMENT / "config/experiment_config.json"
    config = read_json(config_path)
    excluded: set[str] = set()
    if args.exclude_manifest:
        excluded = {row["base_item_id"] for row in read_jsonl(args.exclude_manifest)}
    if args.split == "test" and not args.output_dir:
        raise SystemExit("--output-dir is required for a test split; this command never overwrites development data")
    summary = prepare_dataset(
        ROOT,
        EXPERIMENT,
        config,
        split=args.split,
        output_dir=args.output_dir,
        excluded_base_ids=excluded,
    )
    if args.split == "development":
        start_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        provenance = {
            "experiment_id": config["experiment_id"],
            "start_commit": start_commit,
            "source_version": config["source"]["version"],
            "source_items_path": config["source"]["items"],
            "source_items_sha256": sha256_file(ROOT / config["source"]["items"]),
            "source_episodes_path": config["source"]["episodes"],
            "source_episodes_sha256": sha256_file(ROOT / config["source"]["episodes"]),
            "config_sha256": sha256_file(config_path),
            "implementation_sha256": {
                path.name: sha256_file(path)
                for path in sorted((EXPERIMENT / "src/cbm_drift_v2").glob("*.py"))
            },
            "selection_uses_model_outputs": False,
            "method_scope": "CBM-inspired attribute filtering; not a reproduction of BeliefTrack tasks",
        }
        write_json(EXPERIMENT / "manifests/provenance.json", provenance)
    print(summary)


if __name__ == "__main__":
    main()
