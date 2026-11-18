"""Explicit complete-development integrity gate before one-shot holdout execution."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'lib'))
from common import ROOT, read_json, read_rows, write_json, file_hash
from runner import fingerprint


def main() -> None:
    p = argparse.ArgumentParser(__doc__)
    p.add_argument('--approve-unchanged-protocol', action='store_true', required=True)
    args = p.parse_args()
    frozen = read_json(ROOT / 'freeze.json')
    if frozen['files'] != fingerprint():
        raise ValueError('Frozen sources differ')
    queue = [q for q in read_rows(ROOT / 'queue.jsonl') if q['split'] == 'dev']
    rows = []
    for q in queue:
        path = ROOT / 'results/units' / (q['request_id'] + '.json')
        if not path.exists():
            raise ValueError('Development units remain unattempted')
        row = read_json(path)
        if row['fingerprint'] != frozen['fingerprint']:
            raise ValueError('Unit fingerprint mismatch')
        rows.append(row)
    calls = [read_json(p) for p in (ROOT / 'results/calls').glob('*.json')]
    if any(c['split'] == 'holdout' for c in calls):
        raise ValueError('Holdout already observed; do not create a retroactive gate')
    if any(c.get('finish_reason') == 'length' for c in calls):
        raise ValueError('Development truncation requires explicit review in a new version, not automatic promotion')
    gate = {'status': 'approved_unchanged_protocol', 'fingerprint': frozen['fingerprint'],
            'development_units': len(rows), 'api_success_units': sum(r['status'] == 'api_success' for r in rows),
            'schema_valid_units': sum(r['schema_valid'] for r in rows),
            'truncated_calls': 0, 'holdout_calls_observed': 0,
            'review_kind': 'agent_engineering_review_not_human_reference_annotation',
            'prompt_changes': False, 'reference_changes': False, 'scorer_changes': False,
            'decision': 'Proceed once on all frozen holdout tasks, regardless of development accuracy.',
            'auxiliary_scripts_sha256': {str(p.relative_to(ROOT)): file_hash(p) for p in sorted((ROOT / 'scripts').glob('*.py'))},
            'reviewed_metrics_sha256': file_hash(ROOT / 'results/metrics.json')}
    write_json(ROOT / 'dev_review.json', gate, True)
    print(gate)


if __name__ == '__main__':
    main()
