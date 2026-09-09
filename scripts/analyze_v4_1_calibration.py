#!/usr/bin/env python3
"""Analyze the formal v4.1 single-agent calibration outputs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mad_attr_filter.io import load_json, read_jsonl, write_json, write_jsonl
from mad_attr_filter.v4_calibration import (
    PARSER_REVISION,
    assert_manifest_compatible,
    build_fingerprints,
    summarize_preflight,
)
from mad_attr_filter.v4_calibration_analysis import (
    audit_run_inventory,
    build_cell_model_statistics,
    build_constraint_diagnostics,
    build_factor_analysis,
    build_item_model_analysis,
    build_parse_audit,
    build_report_markdown,
    write_cell_statistics_csv,
)
from mad_attr_filter.v4_validation import validate_v4_pool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze v4.1 calibration outputs.")
    parser.add_argument("--config", default="config/v4_1_calibration_config.json")
    parser.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="Produce provisional analysis even when formal records are incomplete.",
    )
    return parser.parse_args()


def _resolve(path: str) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else ROOT / candidate


def main() -> int:
    args = parse_args()
    config = load_json(_resolve(args.config))
    dataset_path = _resolve(str(config["dataset"]))
    results_dir = _resolve(str(config["results_dir"]))
    samples = read_jsonl(dataset_path)
    validate_v4_pool(samples, expected_items_per_cell=10)
    manifest_path = results_dir / "experiment_manifest.json"
    manifest = load_json(manifest_path)
    fingerprints = build_fingerprints(dataset_path, config)
    assert_manifest_compatible(manifest, fingerprints, str(config["experiment_id"]))

    outputs = read_jsonl(results_dir / "single_agent_outputs.jsonl")
    inventory = audit_run_inventory(
        samples,
        outputs,
        config,
        fingerprints["experiment_sha256"],
    )
    if not inventory["complete"] and not args.allow_incomplete:
        raise ValueError(
            "Formal run inventory is incomplete or inconsistent; rerun with --allow-incomplete"
        )
    preflight_path = results_dir / "preflight_outputs.jsonl"
    preflight_summary = (
        summarize_preflight(read_jsonl(preflight_path))
        if preflight_path.exists()
        else {}
    )
    item_rows = build_item_model_analysis(samples, outputs, config)
    cell_rows = build_cell_model_statistics(samples, outputs, item_rows, config)
    factor_analysis = build_factor_analysis(outputs, cell_rows, config)
    diagnostics = build_constraint_diagnostics(samples, outputs, config)
    parse_audit = build_parse_audit(outputs)
    report, decision = build_report_markdown(
        inventory=inventory,
        preflight_summary=preflight_summary,
        outputs=outputs,
        item_rows=item_rows,
        cell_rows=cell_rows,
        factor_analysis=factor_analysis,
        diagnostics=diagnostics,
        parse_audit=parse_audit,
        config=config,
    )

    write_jsonl(results_dir / "item_model_analysis.jsonl", item_rows)
    write_cell_statistics_csv(results_dir / "cell_model_statistics.csv", cell_rows)
    factor_analysis["run_inventory"] = inventory
    factor_analysis["decision_summary"] = decision
    write_json(results_dir / "factor_analysis.json", factor_analysis)
    write_json(results_dir / "constraint_diagnostics.json", diagnostics)
    write_jsonl(results_dir / "parse_audit.jsonl", parse_audit)
    (results_dir / "calibration_report.md").write_text(report, encoding="utf-8")

    manifest["formal_results"] = {
        "run_inventory": inventory,
        "item_model_analysis_records": len(item_rows),
        "cell_model_statistics_rows": len(cell_rows),
        "parse_audit_records": len(parse_audit),
        "decision": decision,
    }
    manifest["parser_revision"] = PARSER_REVISION
    manifest["status"]["analysis"] = "complete" if inventory["complete"] else "provisional"
    write_json(manifest_path, manifest)
    print(
        json.dumps(
            {
                "run_inventory": inventory,
                "item_model_rows": len(item_rows),
                "cell_model_rows": len(cell_rows),
                "parse_audit_rows": len(parse_audit),
                "decision": decision,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
