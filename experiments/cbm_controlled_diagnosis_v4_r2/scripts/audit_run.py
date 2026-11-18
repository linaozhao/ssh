"""Read-only post-run integrity and raw-offset audit; never invokes a model."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'lib'))
from common import ROOT, REPO, digest, file_hash, read_json, read_rows, write_json, write_rows, write_text
from protocol import render
from runner import fingerprint, load_tasks
from scoring import core, pairs, prf


def main() -> None:
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--final', action='store_true')
    args = parser.parse_args()
    frozen = read_json(ROOT / 'freeze.json')
    tasks = {t['task_id']: t for t in load_tasks()}
    queue = {q['request_id']: q for q in read_rows(ROOT / 'queue.jsonl')}
    ledger_path = ROOT / 'results/attempts.jsonl'
    ledger = read_rows(ledger_path) if ledger_path.exists() else []
    calls = {p.stem: read_json(p) for p in (ROOT / 'results/calls').glob('*.json')}
    units = {p.stem: read_json(p) for p in (ROOT / 'results/units').glob('*.json')}
    errors, pending = [], []
    if fingerprint() != frozen['files']:
        errors.append('frozen_source_or_data_changed')
    for name, expected in frozen.get('prior_artifact_hashes', {}).items():
        if file_hash(REPO / name) != expected:
            errors.append('stopped_version_artifact_changed')
    gate = ROOT / 'dev_review.json'
    if gate.exists():
        for name, expected in read_json(gate).get('auxiliary_scripts_sha256', {}).items():
            if file_hash(ROOT / name) != expected:
                errors.append('auxiliary_script_changed_after_development_gate')
    if len({r['attempt_id'] for r in ledger}) != len(ledger):
        errors.append('duplicate_attempt_id')
    for r in ledger:
        if r['request_id'] not in queue or r['fingerprint'] != frozen['fingerprint']:
            errors.append('unknown_request_or_fingerprint')
        if r['attempt_id'] not in calls:
            pending.append(r['attempt_id'])
    audits = []
    for aid, c in calls.items():
        q = queue.get(c['request_id'])
        if q is None:
            errors.append('unknown_call_request')
            continue
        if c['payload_sha256'] != digest(c['payload']):
            errors.append('payload_hash')
        if c['phase'] != 'supplement' and c['payload']['messages'] != render(tasks[q['task_id']], q['method'], c['phase']):
            errors.append('prompt_mismatch')
        public = json.loads(c['payload']['messages'][1]['content'])
        if {'variant', 'expected_labels', 'reference', 'group_id', 'split'} & public.keys():
            errors.append('private_metadata_in_prompt')
        if tasks[q['task_id']]['task_kind'] == 'B2' and 'target_message_id' in public:
            errors.append('B2_target_leak')
        audits.append({'attempt_id': aid, 'task_id': q['task_id'], 'method': q['method'], 'split': q['split'],
                       'phase': c['phase'], 'status': c['status'], 'finish_reason': c.get('finish_reason'),
                       'parse_source': c.get('parse_source'), 'usage': c.get('usage', {})})
    for qid, unit in units.items():
        if qid not in queue or unit['fingerprint'] != frozen['fingerprint']:
            errors.append('unknown_unit_or_fingerprint')
        phases = {c['phase'] for c in calls.values() if c['request_id'] == qid}
        allowed = {'extract', 'supplement'} if unit['method'] == 'M2' else {'diagnose'}
        if not phases <= allowed:
            errors.append('unexpected_phase')
    if args.final and pending:
        errors.append('unfinished_attempts')
    report = {'status': 'passed' if not errors else 'failed', 'final_audit': args.final,
              'expected_units': 576, 'completed_units': len(units), 'pending_units': 576 - len(units),
              'physical_attempts': len(ledger), 'persisted_calls': len(calls), 'inflight_or_unresolved': pending,
              'api_failures': sum(c['status'] != 'api_success' for c in calls.values()),
              'truncated_calls': sum(c.get('finish_reason') == 'length' for c in calls.values()),
              'extra_semantic_calls': sum(c['phase'] == 'supplement' and not c['retry'] for c in calls.values()),
              'retry_attempts': sum(c['retry'] for c in calls.values()),
              'split_method_units': dict(Counter(q['split'] + '/' + q['method'] for q in units.values())),
              'returned_models': dict(Counter(c.get('returned_model', 'unknown') for c in calls.values())),
              'reported_total_tokens': sum(c.get('usage', {}).get('total_tokens', 0) for c in calls.values()),
              'errors': errors, 'human_verified': 0, 'real_trajectory_evaluation': 'not_started'}
    write_json(ROOT / 'results/integrity_audit.json', report)
    write_rows(ROOT / 'results/call_audit.jsonl', audits)

    # Supplemental raw-offset metric: this does not change the frozen primary scorer.
    # M2's deterministic indices are not falsely called model-generated indices.
    refs = {r['task_id']: r for k in ('A', 'B1', 'B2') for r in read_rows(ROOT / f'references/{k}_references.jsonl')}
    offset_rows = []
    for qid, u in units.items():
        cs = [calls[x] for x in u['api_attempt_ids'] if x in calls and calls[x]['status'] == 'api_success']
        final = next((c for c in reversed(cs) if c['phase'] in ('diagnose', 'supplement')), None)
        if final is None:
            continue
        parsed = final.get('parsed')
        if not isinstance(parsed, dict) or not isinstance(parsed.get('claims'), list):
            continue
        pc = [c for c in parsed['claims'] if isinstance(c, dict)]
        rc = refs[u['task_id']]['claims']
        matches = pairs(pc, rc, lambda p, r: core(p, r, True))
        offset_rows.append({'task_id': u['task_id'], 'method': u['method'], 'split': u['split'],
                            'raw_core_exact': prf(len(matches), len(pc) - len(matches), len(rc) - len(matches)),
                            'repaired_claim_count': sum(c.get('offset_repaired', False) for c in (u.get('prediction') or {}).get('claims', []))})
    write_rows(ROOT / 'results/raw_offset_audit.jsonl', offset_rows)
    write_json(ROOT / 'results/raw_offset_summary.json', {
        s: {m: prf(*(sum(r['raw_core_exact'][key] for r in offset_rows if r['split'] == s and r['method'] == m)
                      for key in ('tp', 'fp', 'fn'))) for m in ('M0', 'M1', 'M2')} for s in ('dev', 'holdout')})
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
