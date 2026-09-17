#!/usr/bin/env python3
"""Record the configured deployment and user-supplied live process metadata."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path[:0] = [str(ROOT / "src"), str(REPO / "src")]

from mad_drift_pilot.common import read_json, write_json  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-json", required=True, help="JSON file generated from live nvidia-smi/ss inspection")
    args = parser.parse_args()
    config = read_json(ROOT / "config/experiment_config.json")
    live = json.loads(Path(args.live_json).read_text(encoding="utf-8"))
    write_json(ROOT / "results/resource_manifest.json", {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "model_deployment": config["model"]["deployment"],
        "configured_endpoints": config["model"]["base_urls"],
        "generation": config["generation"],
        "live_services": live,
        "backend_default_top_k": 20,
        "top_k_explicitly_sent": False,
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

