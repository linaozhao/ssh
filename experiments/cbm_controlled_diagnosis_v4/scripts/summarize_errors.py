"""Produce case-level failure audit without changing the frozen matching policy."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'lib'))
from common import ROOT, read_json, read_rows, write_json, write_rows, write_text
from runner import load_tasks
from scoring import core, basis_ok, support_ok


def main() -> None:
    tasks = {t['task_id']: t for t in load_tasks()}
    refs = {r['task_id']: r for k in ('A', 'B1', 'B2') for r in read_rows(ROOT / f'references/{k}_references.jsonl')}
    units = {(u['task_id'], u['method']): u for p in (ROOT / 'results/units').glob('*.json') if (u := read_json(p))}
    scores = read_rows(ROOT / 'results/per_task_scores.jsonl')
    audit, categories = [], Counter()
    for s in scores:
        u = units.get((s['task_id'], s['method']))
        if not u:
            continue
        task, ref = tasks[s['task_id']], refs[s['task_id']]
        pred = u.get('prediction') or {}
        reasons = []
        if not s['valid_detection']:
            reasons.append('missing_valid_diagnostic')
        elif not s['detection_correct']:
            reasons.append('error_detection')
        if not s['labels_correct']:
            reasons.append('message_classification')
        for r in ref['claims']:
            compatible = [p for p in pred.get('claims', []) if p.get('message_id') == r['message_id'] and p.get('candidate_id') == r['candidate_id']]
            if not compatible:
                reasons.append('message_or_candidate')
                continue
            attrs = [p for p in compatible if p.get('attribute') == r.get('attribute')]
            if not attrs:
                reasons.append('attribute_binding')
                continue
            matched = [p for p in attrs if core(p, r, False)]
            if not matched:
                reasons.append('quote_span')
                continue
            if not any(basis_ok(p, r) for p in matched):
                reasons.append('evidence_rule_or_version_binding')
            if not any(support_ok(p, r) for p in matched):
                reasons.append('temporal_status_or_history_support')
        if s['task_kind'] == 'B2' and not s['first_message_correct']:
            reasons.append('autonomous_first_error_location')
        if not reasons:
            continue
        reasons = sorted(set(reasons))
        for reason in reasons:
            categories[(s['split'], s['method'], reason)] += 1
        audit.append({'task_id': s['task_id'], 'split': s['split'], 'method': s['method'], 'task_kind': s['task_kind'],
                      'variant': s['variant'], 'issues': reasons, 'reference': ref, 'prediction': pred,
                      'messages': task['messages'], 'official_rules': task['rules']})
    write_rows(ROOT / 'results/error_audit.jsonl', audit)
    write_json(ROOT / 'results/error_counts.json', [{'split': s, 'method': m, 'issue': issue, 'count': n}
                                                    for (s, m, issue), n in sorted(categories.items())])
    lines = ['# 逐例诊断差异审计', '', '这是自动比对后的输出文本审计，不是独立人工标注或模型内部机制解释。',
             '主评分规则未变；一例可以出现在多个差异类别，数量不可相加作总错误数。', '',
             '|划分|方法|差异|数量|', '|---|---|---|---|']
    for (s, m, issue), n in sorted(categories.items()):
        lines.append(f'|{s}|{m}|{issue}|{n}|')
    shown = Counter()
    for row in audit:
        key = row['split'], row['method']
        if shown[key] >= 3:
            continue
        shown[key] += 1
        lines += ['', f"## {row['split']} / {row['method']} / {row['variant']} / {row['task_id']}",
                  '差异：' + ', '.join(row['issues']), '公开发言：']
        lines += [f"- {m['message_id']} {m['agent_id']} T{m['evidence_stage']} R{m['round']}: {m['text']}" for m in row['messages']]
        lines += ['参考主张：', '```json', json.dumps(row['reference']['claims'], ensure_ascii=False, indent=2), '```',
                  'Judge 主张：', '```json', json.dumps(row['prediction'].get('claims', []), ensure_ascii=False, indent=2), '```']
    write_text(ROOT / 'reports/ERROR_ANALYSIS_ZH.md', '\n'.join(lines) + '\n')
    print(f'{len(audit)} units with one or more diagnostic differences')


if __name__ == '__main__':
    main()
