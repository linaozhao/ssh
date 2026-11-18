"""Additional fail-closed operational guard; does not alter frozen API payloads."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'lib'))
from common import ROOT, read_json, read_rows, file_hash
from runner import execute, load_tasks


def validate_queue() -> None:
    """Verify the queue hash and its Cartesian coverage before any API access."""
    frozen = read_json(ROOT / 'freeze.json')
    if file_hash(ROOT / 'queue.jsonl') != frozen['queue_sha256']:
        raise ValueError('Frozen request queue changed')
    queue = read_rows(ROOT / 'queue.jsonl')
    ids = {t['task_id'] for t in load_tasks()}
    expected = {(tid, method) for tid in ids for method in ('M0', 'M1', 'M2')}
    if len(queue) != len(expected) or {(q['task_id'], q['method']) for q in queue} != expected or len({q['request_id'] for q in queue}) != len(queue):
        raise ValueError('Missing, duplicate or unknown method-task requests')
    gate = ROOT / 'dev_review.json'
    if gate.exists():
        for name, expected_hash in read_json(gate).get('auxiliary_scripts_sha256', {}).items():
            if file_hash(ROOT / name) != expected_hash:
                raise ValueError('Frozen auxiliary script changed')


def main() -> None:
    p = argparse.ArgumentParser(__doc__)
    p.add_argument('--split', choices=['dev', 'holdout'], required=True)
    p.add_argument('--online', action='store_true')
    p.add_argument('--prompt-key', action='store_true')
    p.add_argument('--check-only', action='store_true')
    args = p.parse_args()
    validate_queue()
    if args.check_only:
        print('Frozen queue and auxiliary scripts match; no API calls made')
    else:
        print(execute(args.split, args.online, args.prompt_key))


if __name__ == '__main__':
    main()
