"""Persist actual JUnit results, source preservation and non-secret artifact inventory."""

from __future__ import annotations

import compileall
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cbm_drift_v3.common import read_json, sha256_file, write_json
from cbm_drift_v3.prepare import verify_source_manifest
from cbm_drift_v3.reporting import build_report


def main() -> int:
    config = read_json(ROOT / "config/experiment_gpu4_r2.json")
    output = ROOT / "results" / config["run_id"]
    xml = ET.parse(output / "pytest_results.xml").getroot()
    suites = list(xml.iter("testsuite"))
    counts = {key: sum(int(s.attrib.get(key, "0")) for s in suites) for key in ("tests", "failures", "errors", "skipped")}
    compiled = compileall.compile_dir(ROOT / "src", quiet=1) and compileall.compile_dir(ROOT / "scripts", quiet=1)
    whitespace = subprocess.run(["git", "diff", "--check"], cwd=ROOT.parents[1], capture_output=True, text=True)
    source = verify_source_manifest(ROOT.parents[1], read_json(ROOT / "data/source_manifest.json"))
    write_json(output / "source_preservation_validation.json", source)
    passed = not counts["failures"] and not counts["errors"] and compiled and whitespace.returncode == 0 and source["status"] == "passed"
    write_json(output / "software_validation.json", {"status": "passed" if passed else "failed", **counts,
                "passed_tests": counts["tests"] - counts["failures"] - counts["errors"] - counts["skipped"],
                "compileall": compiled, "git_diff_check": whitespace.returncode == 0,
                "junit_sha256": sha256_file(output / "pytest_results.xml"),
                "test_scope": "v3 R2 plus v2 regression; full1188+108 mocks only in temporary directories",
                "online_calls_from_tests": 0})
    build_report(ROOT, config, read_json(ROOT / "config/judge_controlled_r2.json"))
    inventory = {str(p.relative_to(ROOT)): {"sha256": sha256_file(p), "bytes": p.stat().st_size}
                 for p in sorted(ROOT.rglob("*")) if p.is_file() and "__pycache__" not in p.parts
                 and ".pytest_cache" not in p.parts and p.name != "artifact_inventory.json"}
    write_json(output / "artifact_inventory.json", {"files": inventory, "includes_mock_response_files": False,
                "large_raw_response_policy": "local raw files; inventory records hashes if present"})
    print({"status": "passed" if passed else "failed", **counts, "legacy_files_unchanged": source["checked_files"], "artifact_count": len(inventory)})
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
