"""Supplemental schema/object/active-evidence audit, not semantic relabeling."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'lib'))
from common import ROOT, read_json, write_rows, write_json
from runner import load_tasks
from diagnosis import state_at

TIMES = {'unknown', 'newly_introduced', 'persistent', 'corrected', 'recurrence', 'post_update_reversion', 'no_change_observed'}


def main() -> None:
    tasks = {t['task_id']: t for t in load_tasks()}
    rows = []
    for path in sorted((ROOT / 'results/units').glob('*.json')):
        u = read_json(path)
        p, t = u.get('prediction'), tasks[u['task_id']]
        errors = []
        if not isinstance(p, dict):
            errors.append('no_prediction')
            p = {}
        if 'current_error' not in p or (p['current_error'] is not None and type(p['current_error']) is not bool):
            errors.append('current_error_type')
        if 'no_error' not in p or (p['no_error'] is not None and type(p['no_error']) is not bool):
            errors.append('no_error_type')
        if type(p.get('current_error')) is bool and p.get('no_error') != (not p['current_error']):
            errors.append('contradictory_detection_flags')
        messages = {m['message_id']: m for m in t['messages']}
        rule_ids = {r['id'] for r in t['rules']}
        for i, c in enumerate(p.get('claims', [])):
            m = messages.get(c.get('message_id'))
            if m is None:
                errors.append(f'{i}:unknown_message')
                continue
            for key in ('agent_id', 'evidence_stage', 'round'):
                if c.get(key) != m[key]:
                    errors.append(f'{i}:location_{key}')
            if c.get('candidate_id') not in t['candidates']:
                errors.append(f'{i}:candidate')
            if c.get('temporal_status') not in TIMES:
                errors.append(f'{i}:temporal_enum')
            if c.get('stance') not in ('asserted', 'quoted', 'rejected', 'hypothetical'):
                errors.append(f'{i}:stance')
            if c.get('current_error') is True and c.get('stance') != 'asserted':
                errors.append(f'{i}:error_on_unadopted_claim')
            for key in ('required_rule_ids', 'conflicting_evidence_ids', 'cited_evidence_ids', 'support_message_ids'):
                if not isinstance(c.get(key), list):
                    errors.append(f'{i}:{key}_type')
            if not set(c.get('required_rule_ids', [])) <= rule_ids:
                errors.append(f'{i}:unknown_rule')
            active = {e['evidence_id']: e for e in state_at(t, m['evidence_stage'])['active_evidence']}
            for eid in c.get('conflicting_evidence_ids', []):
                e = active.get(eid)
                if not e:
                    errors.append(f'{i}:inactive_evidence')
                elif e['candidate_id'] != c.get('candidate_id') or (c.get('attribute') is not None and e['attribute'] != c['attribute']):
                    errors.append(f'{i}:evidence_object_binding')
                elif c.get('active_version') is not None and c['active_version'] != e.get('version'):
                    errors.append(f'{i}:active_version')
            for mid in c.get('support_message_ids', []):
                if mid not in m['visible_history_ids']:
                    errors.append(f'{i}:invisible_history')
                elif messages[mid]['agent_id'] != m['agent_id']:
                    errors.append(f'{i}:peer_not_self_history')
        if t['task_kind'] == 'B2' and any(mid not in messages for mid in p.get('first_error_message_ids', [])):
            errors.append('invalid_first_message_id')
        rows.append({'task_id': u['task_id'], 'split': u['split'], 'method': u['method'],
                     'contract_passed': not errors, 'errors': errors})
    write_rows(ROOT / 'results/contract_audit.jsonl', rows)
    summary = {s: {m: {'received': len(rs := [r for r in rows if r['split'] == s and r['method'] == m]),
                       'passed': sum(r['contract_passed'] for r in rs),
                       'error_counts': dict(Counter(e.split(':', 1)[-1] for r in rs for e in r['errors']))}
                   for m in ('M0', 'M1', 'M2')} for s in ('dev', 'holdout')}
    write_json(ROOT / 'results/contract_summary.json', summary)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
