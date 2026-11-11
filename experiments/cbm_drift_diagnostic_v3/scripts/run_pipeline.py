"""R2 entry point: independent offline stages, explicitly gated online stages."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cbm_drift_v3.common import read_json, read_jsonl, write_json, write_jsonl, sha256_json
from cbm_drift_v3.prepare import prepare_dataset, verify_source_manifest
from cbm_drift_v3.validation import validate_dataset
from cbm_drift_v3.controlled_cases import build_controlled, validate_controlled
from cbm_drift_v3.judge import prepare_controlled_judge, run_controlled_judge, credential_gate
from cbm_drift_v3.evaluation import evaluate_controlled
from cbm_drift_v3.runner import run_requests, run_protocol
from cbm_drift_v3.runtime import check_gpu
from cbm_drift_v3.diagnostics import analyze_program, load_records
from cbm_drift_v3.annotation import prepare_deferred_real
from cbm_drift_v3.reporting import build_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config/experiment_gpu4_r2.json")
    parser.add_argument("--judge-config", type=Path, default=ROOT / "config/judge_controlled_r2.json")
    parser.add_argument("--judge-results-subdir", help="Read an explicitly versioned validation continuation")
    parser.add_argument("--dataset", choices=["controlled"], default="controlled")
    parser.add_argument("--logical-request-cap", type=int, default=144)
    stages = ("prepare", "validate", "build-controlled", "validate-controlled", "run-protocol", "run-mad", "preflight",
              "resume", "analyze-program", "prepare-controlled-judge", "prepare-deferred-real", "report", "run-online-judge", "evaluate-controlled")
    for name in stages:
        parser.add_argument("--" + name, action="store_true")
    args = parser.parse_args()
    if args.logical_request_cap != 144:
        parser.error("R2 controlled logical cap is exactly144; real queue is deferred")
    config, judge_config = read_json(args.config), read_json(args.judge_config)
    data_dir = ROOT / config.get("data_subdir", "data")
    result = ROOT / "results" / config["run_id"]
    result.mkdir(parents=True, exist_ok=True)
    judge_subdir = args.judge_results_subdir or judge_config.get("results_subdir", "controlled_judge")
    if Path(judge_subdir).name != judge_subdir:
        raise ValueError("Judge results_subdir must be a single new run-local directory name")
    judge_dir = result / judge_subdir
    if not any(getattr(args, name.replace("-", "_")) for name in stages):
        for name in ("prepare", "validate", "build_controlled", "validate_controlled", "run_protocol", "run_mad", "analyze_program", "prepare_controlled_judge", "prepare_deferred_real", "report"):
            setattr(args, name, True)
    outputs = {}
    if args.prepare:
        outputs["prepare"] = prepare_dataset(ROOT.parents[1], ROOT, config)
    sequences = read_jsonl(data_dir / "evidence_sequences.jsonl")
    plan = read_jsonl(data_dir / "mad_request_plan.jsonl")
    views = read_jsonl(data_dir / "branch_views.jsonl")
    if args.validate:
        source = read_jsonl(ROOT.parent / "cbm_drift_diagnostic_v2/data/evidence_sequences.jsonl")
        report = validate_dataset(sequences, plan, views, source)
        write_json(data_dir / "validation_report.json", report)
        outputs["data_validation"] = report
        preserved = verify_source_manifest(ROOT.parents[1], read_json(data_dir / "source_manifest.json"))
        write_json(result / "source_preservation_validation.json", preserved)
        if report["status"] != "passed" or preserved["status"] != "passed":
            raise ValueError("Source/data validation failed")
    if args.build_controlled:
        outputs["controlled"] = build_controlled(sequences, ROOT / "data/controlled")
    if args.validate_controlled:
        outputs["controlled_validation"] = validate_controlled(read_jsonl(ROOT / "data/controlled/cases.jsonl"), read_jsonl(ROOT / "data/controlled/expected_labels.jsonl"))
        if outputs["controlled_validation"]["status"] != "passed":
            raise ValueError("Controlled reference validation failed")
    if args.run_protocol or args.run_mad:
        audit = validate_dataset(sequences, plan, views, read_jsonl(ROOT.parent / "cbm_drift_diagnostic_v2/data/evidence_sequences.jsonl"))
        if audit["status"] != "passed":
            raise ValueError("MAD execution refused: graph/data validation failed")
        service_file = result / "service_manifest.json"
        service = read_json(service_file) if service_file.exists() else None
        if service and (service.get("run_id") != config["run_id"] or service.get("model_config_sha256") != sha256_json(config["model"])):
            raise ValueError("Existing owned-service manifest belongs to another run/model")
        runtime = check_gpu(config, owned_service=service)
        write_json(result / "runtime_manifest.json", runtime | {"run_id": config["run_id"]})
        if not runtime["allowed"]:
            for name, selected in (("protocol", read_jsonl(data_dir / "protocol_request_plan.jsonl")), ("mad", plan)):
                if getattr(args, "run_" + name):
                    existing = load_records(result / name)
                    ids = {r["request_id"] for r in selected}
                    if any(r.get("run_id") != config["run_id"] or r["request_id"] not in ids or r.get("is_mock") for r in existing):
                        raise ValueError("Foreign or mock records in online experiment directory")
                    attempts_file = result / name / "attempts.jsonl"
                    attempts = read_jsonl(attempts_file) if attempts_file.exists() else []
                    if not attempts_file.exists():
                        write_jsonl(attempts_file, [])
                    success = {r["request_id"] for r in existing if r.get("api_success")}
                    failed = {r["request_id"] for r in existing if not r.get("api_success")}
                    blocked_ids = ids - success - failed
                    status = {"status": "blocked", "reason": runtime["reason"], "planned": len(selected),
                              "attempted": len({a["request_id"] for a in attempts}), "attempts": len(attempts),
                              "api_success": len(success), "parsed": sum(r.get("parsed", {}).get("recognized", False) for r in existing),
                              "failed": len(failed), "blocked": len(blocked_ids),
                              "complete_branch_views": sum(all(mid in success for mid in v["message_ids"]) for v in views) if name == "mad" else None}
                    write_json(result / name / "status.json", status)
                    write_jsonl(result / name / "blocked.jsonl", [{"request_id": r["request_id"], "status": "blocked", "reason": runtime["reason"]} for r in selected if r["request_id"] in blocked_ids])
                    outputs[name] = status
        else:
            if args.run_protocol:
                outputs["protocol"] = run_protocol(config, read_jsonl(data_dir / "protocol_request_plan.jsonl"), sequences, result / "protocol", resume=args.resume)
            if args.run_mad:
                protocol_status = read_json(result / "protocol/status.json") if (result / "protocol/status.json").exists() else {}
                if protocol_status.get("api_success") != 108:
                    outputs["mad"] = {"status": "blocked", "reason": "static_preflight_incomplete", "planned": 1188, "blocked": 1188}
                    write_json(result / "mad/status.json", outputs["mad"])
                elif args.preflight:
                    outputs["mad"] = run_requests(config, plan, sequences, result / "mad", resume=args.resume, preflight=True)
                    write_json(result / "mad/preflight_status.json", outputs["mad"])
                else:
                    pf = read_json(result / "mad/preflight_status.json") if (result / "mad/preflight_status.json").exists() else {}
                    if pf.get("api_success") != 198:
                        outputs["mad"] = {"status": "blocked", "reason": "two_family_preflight_incomplete"}
                    else:
                        outputs["mad"] = run_requests(config, plan, sequences, result / "mad", resume=args.resume)
    records = load_records(result / "mad")
    if args.analyze_program:
        outputs["program"] = analyze_program(plan, sequences, records, result / "program")
    if args.prepare_controlled_judge:
        outputs["queue"] = prepare_controlled_judge(read_jsonl(ROOT / "data/controlled/cases.jsonl"), judge_config, judge_dir)
        write_json(judge_dir / "credential_gate.json", credential_gate(judge_config, enabled=False))
    if args.run_online_judge:
        outputs["judge"] = run_controlled_judge(judge_config, judge_dir, enabled=True, resume=args.resume)
        write_json(judge_dir / "status.json", outputs["judge"])
    if args.evaluate_controlled:
        file = judge_dir / "outputs.jsonl"
        outputs["evaluation"] = evaluate_controlled(read_jsonl(file) if file.exists() else [], read_jsonl(ROOT / "data/controlled/expected_labels.jsonl"))
        write_json(judge_dir / "evaluation.json", outputs["evaluation"])
    if args.prepare_deferred_real:
        outputs["deferred"] = prepare_deferred_real(plan, sequences, records, ROOT / config.get("annotation_subdir", "annotation/deferred_real"), config["selection_seed"])
    if args.report:
        build_report(ROOT, config, judge_config, judge_results_subdir=judge_subdir)
        outputs["report"] = str(result / "RUN_SUMMARY_ZH.md")
    print(json.dumps(outputs, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
