#!/usr/bin/env python3
"""Inspect the public model registry without transmitting experimental content."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cbm_drift_v2.common import read_json, sha256_json
from cbm_drift_v2.tokenplan_judge import atomic_write_json, results_directory, utc_now


def check_service(config: dict) -> dict:
    """Verify catalog availability, separately from authenticated inference access."""
    status = {
        "checked_at": utc_now(),
        "config_sha256": sha256_json(config),
        "requested_model": config["model_name"],
        "api_key_env": config["api_key_env"],
        "credential_present": bool(os.environ.get(config["api_key_env"])),
        "trust_env": bool(config.get("trust_env", True)),
        "registry_http_status": None,
        "model_in_catalog": False,
        "authenticated_inference_verified": False,
        "judge_calls_made": 0,
        "error": None,
    }
    try:
        with httpx.Client(trust_env=status["trust_env"], follow_redirects=False, timeout=20) as client:
            response = client.get(config["base_url"].rstrip("/") + "/models")
            status["registry_http_status"] = response.status_code
            response.raise_for_status()
            models = response.json()["data"]
            status["model_in_catalog"] = any(row.get("id") == config["model_name"] for row in models)
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        status["error"] = f"{type(exc).__name__}: {exc}"
    status["ready_for_authenticated_preflight"] = bool(status["model_in_catalog"] and status["credential_present"])
    return status


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config/tokenplan_deepseek_v4_pro.json")
    args = parser.parse_args()
    config = read_json(args.config)
    result = check_service(config)
    atomic_write_json(results_directory(ROOT, config) / "service_check.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
