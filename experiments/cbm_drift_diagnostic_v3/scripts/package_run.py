"""Package explicitly selected raw experiment artifacts without model calls."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
import tarfile

ROOT = Path(__file__).resolve().parents[1]
SECRET = re.compile(rb"(?:sk-[A-Za-z0-9]{24,}|user_[A-Za-z0-9]{40,}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)")


def digest(data: bytes) -> str:
    """Return the content fingerprint used by the archive inventory."""
    return hashlib.sha256(data).hexdigest()


def package(run_id: str, destination: Path) -> dict:
    """Write and read back a deterministic archive with explicit file selection."""
    if Path(run_id).name != run_id or run_id in {".", ".."}:
        raise ValueError("run_id must be a directory name")
    run = ROOT / "results" / run_id
    paths = []
    for part, count in (("mad/records", 1188), ("protocol/records", 108), ("mad/checkpoints", 12)):
        selected = sorted((run / part).glob("*.json"))
        if len(selected) != count:
            raise ValueError(f"Unexpected file count in {part}: {len(selected)}")
        paths.extend(selected)
    for directory, count in (("controlled_judge_official_flash", 12),
                             ("controlled_judge_official_flash_parser_v2", 144)):
        path = run / directory / "outputs.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        if len(rows) != count or len({r["request_id"] for r in rows}) != count:
            raise ValueError(f"Unexpected Judge output count in {directory}")
        paths.append(path)
    paths.append(run / "service_manifest.json")
    entries = []
    for path in sorted(paths):
        if path.is_symlink() or not path.is_file():
            raise ValueError("Only regular files may be packaged")
        content = path.read_bytes()
        if SECRET.search(content):
            raise ValueError(f"Potential credential found in {path.name}; packaging refused")
        entries.append({"path": str(path.relative_to(ROOT)), "bytes": len(content), "sha256": digest(content)})
    destination.mkdir(parents=True, exist_ok=True)
    archive = destination / f"{run_id}_raw.tar.gz"
    manifest = destination / f"{run_id}_raw.manifest.json"
    if archive.exists() or manifest.exists():
        raise ValueError("Archive destination must be new; existing bundles are not overwritten")
    with archive.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w") as tar:
                for entry in entries:
                    path = ROOT / entry["path"]
                    info = tar.gettarinfo(str(path), arcname=entry["path"])
                    info.uid = info.gid = info.mtime = 0
                    info.uname = info.gname = ""
                    info.mode = 0o644
                    with path.open("rb") as stream:
                        tar.addfile(info, stream)
    with tarfile.open(archive, "r:gz") as tar:
        members = tar.getmembers()
        if [m.name for m in members] != [e["path"] for e in entries]:
            raise ValueError("Archive member inventory mismatch")
        for member, entry in zip(members, entries):
            stream = tar.extractfile(member)
            if stream is None or digest(stream.read()) != entry["sha256"]:
                raise ValueError(f"Archive read-back verification failed: {member.name}")
    summary = {"run_id": run_id, "archive": archive.name, "archive_bytes": archive.stat().st_size,
               "archive_sha256": digest(archive.read_bytes()), "file_count": len(entries),
               "uncompressed_bytes": sum(e["bytes"] for e in entries), "read_back_verified": True,
               "scope": "Raw responses, 12 MAD checkpoints and experiment service manifest; no model weights, credentials or logs.",
               "counting_note": "The original 12 Judge preflight responses are also included in the 144-response continuation; they are not extra calls.",
               "human_annotation": "deferred", "real_diagnostic_evaluation": "not_evaluated", "files": entries}
    manifest.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {k: v for k, v in summary.items() if k != "files"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts")
    args = parser.parse_args()
    print(json.dumps(package(args.run_id, args.output_dir), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
