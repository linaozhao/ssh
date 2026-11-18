"""Document actual public-input differences between paired variants; no API use."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'lib'))
from common import ROOT, read_rows, write_rows, digest
from runner import load_tasks


def main() -> None:
    tasks = {t['task_id']: t for t in load_tasks()}
    groups = {}
    for m in read_rows(ROOT / 'data/group_manifest.jsonl'):
        groups.setdefault(m['group_id'], []).append(m)
    rows = []
    for gid, members in sorted(groups.items()):
        members.sort(key=lambda m: m['variant'])
        anchor = tasks[members[0]['task_id']]
        for meta in members[1:]:
            t = tasks[meta['task_id']]
            key = lambda m: (m['evidence_stage'], m['round'], m['agent_id'])
            a, b = {key(m): m for m in anchor['messages']}, {key(m): m for m in t['messages']}
            changes = [{'location': list(k), 'before': a[k]['text'] if k in a else None,
                        'after': b[k]['text'] if k in b else None}
                       for k in sorted(a.keys() | b.keys())
                       if (a[k]['text'] if k in a else None) != (b[k]['text'] if k in b else None)]
            rows.append({'group_id': gid, 'split': meta['split'], 'task_kind': meta['task_kind'],
                         'anchor_variant': members[0]['variant'], 'comparison_variant': meta['variant'],
                         'anchor_task_id': anchor['task_id'], 'comparison_task_id': t['task_id'],
                         'same_rules': digest(anchor['rules']) == digest(t['rules']),
                         'same_public_evidence': digest(anchor['evidence']) == digest(t['evidence']),
                         'same_candidates': anchor['candidates'] == t['candidates'],
                         'changed_message_locations_and_text': changes,
                         'note': 'IDs regenerated for each task; align by stage/round/agent, never storage order.'})
    write_rows(ROOT / 'review/variant_deltas.jsonl', rows, True)
    print(f'{len(rows)} within-group comparisons documented')


if __name__ == '__main__':
    main()
