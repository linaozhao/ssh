#!/usr/bin/env python3
"""Long-running conservative scheduler for multi-window TokenPlan Judge execution."""

from __future__ import annotations

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
    RESULTS_RELATIVE,
    TokenPlanJudgeRunner,
    atomic_write_json,
    validate_preflight,
)

RESULTS = ROOT / RESULTS_RELATIVE
STOP_FILE = RESULTS / "STOP"
DAEMON_STATUS = RESULTS / "daemon_status.json"
INFRASTRUCTURE_COOLDOWN_SECONDS = 900


def status(value: str, **extra: object) -> None:
    atomic_write_json(DAEMON_STATUS, {
        "pid": os.getpid(), "status": value,
        "updated_at": datetime.now(timezone.utc).isoformat(), **extra,
    })


def wait_until(timestamp: str | None, default_seconds: int) -> None:
    if timestamp:
        target = datetime.fromisoformat(timestamp).timestamp()
        seconds = max(target - time.time(), 0)
    else:
        seconds = default_seconds
    deadline = time.time() + seconds
    while time.time() < deadline:
        if STOP_FILE.exists():
            return
        time.sleep(min(30, max(deadline - time.time(), 0)))


def main() -> None:
    config = read_json(ROOT / "config/tokenplan_deepseek_v4_pro.json")
    if not os.environ.get(config["api_key_env"]):
        raise RuntimeError(f"Missing {config['api_key_env']}")
    STOP_FILE.unlink(missing_ok=True)
    consecutive_probe_failures = 0
    while not STOP_FILE.exists():
        runner = TokenPlanJudgeRunner(ROOT, config)
        progress_path = RESULTS / "progress_summary.json"
        progress = read_json(progress_path) if progress_path.exists() else {"completed_records": 0}
        preflight = validate_preflight(ROOT) if progress.get("completed_records") else {"passed": False, "requests": 0}
        if preflight.get("requests", 0) >= 24 and not preflight["passed"]:
            status("stopped_preflight_protocol_failure", preflight=preflight)
            break

        phase = "formal" if preflight.get("passed") else "preflight"
        scheduler_state_path = RESULTS / "scheduler_state.json"
        scheduler_state = read_json(scheduler_state_path) if scheduler_state_path.exists() else {}
        paused_for_infra = scheduler_state.get("status") == "paused_after_five_infrastructure_errors"
        status("running", phase=phase, probe_after_infrastructure_pause=paused_for_infra)
        api_success_before = int(progress.get("api_success", 0))
        summary = runner.run(phase, max_new=1 if paused_for_infra else None)
        build_chinese_report(ROOT)
        scheduler_state = read_json(scheduler_state_path)

        if paused_for_infra and int(summary.get("api_success", 0)) <= api_success_before:
            scheduler_state["status"] = "paused_after_five_infrastructure_errors"
            atomic_write_json(scheduler_state_path, scheduler_state)

        if summary["remaining_requests"] == 0:
            status("complete", summary=summary)
            break
        if scheduler_state.get("status") in {
            "authentication_or_permission_error", "stopped_preflight_protocol_failure"
        }:
            status(scheduler_state["status"], summary=summary)
            break
        if scheduler_state.get("status") in {
            "waiting_for_unknown_quota_window", "waiting_for_quota_window", "quota_exhausted"
        }:
            status("waiting_for_quota_window", next_eligible_at=scheduler_state.get("next_eligible_at"))
            wait_until(scheduler_state.get("next_eligible_at"), int(config["quota"]["window_seconds"]) + 30)
            continue
        if scheduler_state.get("status") == "paused_after_five_infrastructure_errors":
            consecutive_probe_failures += 1
            status(
                "waiting_after_infrastructure_errors",
                consecutive_probe_failures=consecutive_probe_failures,
                cooldown_seconds=INFRASTRUCTURE_COOLDOWN_SECONDS,
            )
            wait_until(None, INFRASTRUCTURE_COOLDOWN_SECONDS)
            continue
        consecutive_probe_failures = 0

    if STOP_FILE.exists():
        status("stopped_by_user")


if __name__ == "__main__":
    main()
