#!/usr/bin/env python3
"""Long-running conservative scheduler for multi-window TokenPlan Judge execution."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cbm_drift_v2.common import read_json
from cbm_drift_v2.tokenplan_analysis import build_chinese_report
from cbm_drift_v2.tokenplan_judge import (
    TokenPlanJudgeRunner,
    atomic_write_json,
    results_directory,
    validate_preflight,
)

INFRASTRUCTURE_COOLDOWN_SECONDS = 900


def status(results: Path, value: str, **extra: object) -> None:
    atomic_write_json(results / "daemon_status.json", {
        "pid": os.getpid(), "status": value,
        "updated_at": datetime.now(timezone.utc).isoformat(), **extra,
    })


def wait_until(stop_file: Path, timestamp: str | None, default_seconds: int) -> None:
    if timestamp:
        target = datetime.fromisoformat(timestamp).timestamp()
        seconds = max(target - time.time(), 0)
    else:
        seconds = default_seconds
    deadline = time.time() + seconds
    while time.time() < deadline:
        if stop_file.exists():
            return
        time.sleep(min(30, max(deadline - time.time(), 0)))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config/tokenplan_deepseek_v4_pro.json")
    args = parser.parse_args()
    config = read_json(args.config)
    results = results_directory(ROOT, config)
    stop_file = results / "STOP"
    if not os.environ.get(config["api_key_env"]):
        raise RuntimeError(f"Missing {config['api_key_env']}")
    stop_file.unlink(missing_ok=True)
    consecutive_probe_failures = 0
    while not stop_file.exists():
        runner = TokenPlanJudgeRunner(ROOT, config)
        progress_path = results / "progress_summary.json"
        progress = read_json(progress_path) if progress_path.exists() else {"completed_records": 0}
        preflight = validate_preflight(ROOT, config) if progress.get("completed_records") else {"passed": False, "requests": 0}
        if preflight.get("requests", 0) >= 24 and not preflight["passed"]:
            status(results, "stopped_preflight_protocol_failure", preflight=preflight)
            break

        phase = "formal" if preflight.get("passed") else "preflight"
        scheduler_state_path = results / "scheduler_state.json"
        scheduler_state = read_json(scheduler_state_path) if scheduler_state_path.exists() else {}
        paused_for_infra = scheduler_state.get("status") == "paused_after_five_infrastructure_errors"
        status(results, "running", phase=phase, probe_after_infrastructure_pause=paused_for_infra)
        api_success_before = int(progress.get("api_success", 0))
        summary = runner.run(phase, max_new=1 if paused_for_infra else None)
        build_chinese_report(ROOT, config)
        scheduler_state = read_json(scheduler_state_path)

        if paused_for_infra and int(summary.get("api_success", 0)) <= api_success_before:
            scheduler_state["status"] = "paused_after_five_infrastructure_errors"
            atomic_write_json(scheduler_state_path, scheduler_state)

        if summary["remaining_requests"] == 0:
            status(results, "complete", summary=summary)
            break
        if scheduler_state.get("status") in {
            "authentication_or_permission_error", "stopped_preflight_protocol_failure"
        }:
            status(results, scheduler_state["status"], summary=summary)
            break
        if scheduler_state.get("status") in {
            "waiting_for_unknown_quota_window", "waiting_for_quota_window", "quota_exhausted"
        }:
            status(results, "waiting_for_quota_window", next_eligible_at=scheduler_state.get("next_eligible_at"))
            wait_until(stop_file, scheduler_state.get("next_eligible_at"), int(config["quota"]["window_seconds"]) + 30)
            continue
        if scheduler_state.get("status") == "paused_after_five_infrastructure_errors":
            consecutive_probe_failures += 1
            status(
                results,
                "waiting_after_infrastructure_errors",
                consecutive_probe_failures=consecutive_probe_failures,
                cooldown_seconds=INFRASTRUCTURE_COOLDOWN_SECONDS,
            )
            wait_until(stop_file, None, INFRASTRUCTURE_COOLDOWN_SECONDS)
            continue
        consecutive_probe_failures = 0

    if stop_file.exists():
        status(results, "stopped_by_user")


if __name__ == "__main__":
    main()
