"""Label-level metrics on the already frozen, label-independent core pairing."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'lib'))
from common import ROOT, read_json, read_rows, write_json, file_hash
from scoring import prf


def main() -> None:
    refs = {r['task_id']: r for k in ('A', 'B1', 'B2') for r in read_rows(ROOT / f'references/{k}_references.jsonl')}
    units = {(u['task_id'], u['method']): u for p in (ROOT / 'results/units').glob('*.json') if (u := read_json(p))}
    scores = read_rows(ROOT / 'results/per_task_scores.jsonl')
    output = {}
    for split in ('dev', 'holdout'):
        output[split] = {}
        for task in ('A', 'B1', 'B2'):
            output[split][task] = {}
            for method in ('M0', 'M1', 'M2'):
                rows = [s for s in scores if s['split'] == split and s['task_kind'] == task and s['method'] == method]
                labels = {}
                for label in ('F', 'R', 'I', 'unresolved'):
                    tp, predicted, expected, matched_expected = 0, 0, 0, 0
                    for s in rows:
                        pc = ((units.get((s['task_id'], method)) or {}).get('prediction') or {}).get('claims', [])
                        rc = refs[s['task_id']]['claims']
                        predicted += sum(label in c.get('labels', []) for c in pc)
                        expected += sum(label in c['labels'] for c in rc)
                        for i, j in s['core_pairs']:
                            matched_expected += label in rc[j]['labels']
                            tp += label in pc[i].get('labels', []) and label in rc[j]['labels']
                    labels[label] = {'end_to_end': prf(tp, predicted - tp, expected - tp),
                                     'recall_given_core': {'correct': tp, 'denominator': matched_expected}}
                output[split][task][method] = {'received': sum(s['received'] for s in rows), 'labels': labels}
    write_json(ROOT / 'results/claim_classification.json', output)
    print('Claim metrics computed using unchanged core_pairs')


if __name__ == '__main__':
    main()
