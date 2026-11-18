"""Preregistered layered metrics. Core matching never looks at predicted labels."""
from __future__ import annotations

from collections import Counter
from typing import Callable
from common import ROOT, read_json, read_rows, write_json, write_rows, write_text
from runner import load_tasks


def ratio(a: int | float, b: int | float) -> float | None:
    return a / b if b else None


def prf(tp: int, fp: int, fn: int) -> dict:
    return {'tp': tp, 'fp': fp, 'fn': fn, 'precision': ratio(tp, tp + fp), 'recall': ratio(tp, tp + fn),
            'f1': ratio(2 * tp, 2 * tp + fp + fn)}


def span_iou(p: dict, r: dict) -> float:
    if any(type(c.get(k)) is not int for c in (p, r) for k in ('start', 'end')):
        return 0.0
    overlap = max(0, min(p['end'], r['end']) - max(p['start'], r['start']))
    union = max(p['end'], r['end']) - min(p['start'], r['start'])
    return overlap / union if union else 0.0


def core(p: dict, r: dict, exact: bool) -> bool:
    for key in ('message_id', 'candidate_id', 'attribute'):
        if p.get(key) != r.get(key):
            return False
    return (p.get('quote'), p.get('start'), p.get('end')) == (r.get('quote'), r.get('start'), r.get('end')) if exact else span_iou(p, r) >= 0.5


def pairs(preds: list[dict], refs: list[dict], predicate: Callable) -> list[tuple[int, int]]:
    """Maximum cardinality matching with frozen input-order tie breaking."""
    owners = {}
    def augment(i: int, seen: set) -> bool:
        for j, ref in enumerate(refs):
            if j not in seen and predicate(preds[i], ref):
                seen.add(j)
                if j not in owners or augment(owners[j], seen):
                    owners[j] = i
                    return True
        return False
    for i in range(len(preds)):
        augment(i, set())
    return sorted((i, j) for j, i in owners.items())


def support_ok(p: dict, r: dict) -> bool:
    return (p.get('temporal_status') == r.get('temporal_status')
            and set(p.get('support_message_ids', [])) == set(r.get('support_message_ids', [])))


def basis_ok(p: dict, r: dict) -> bool:
    return all(set(p.get(k, [])) == set(r.get(k, [])) for k in ('required_rule_ids', 'conflicting_evidence_ids', 'cited_evidence_ids')) and all(p.get(k) == r.get(k) for k in ('active_version', 'cited_version'))


def score(task: dict, ref: dict, output: dict | None, meta: dict, method: str) -> dict:
    pred = output.get('prediction') if output else None
    if output and output.get('finish_reason') == 'length':
        pred = None
    valid = isinstance(pred, dict) and type(pred.get('current_error')) is bool
    pc, rc = pred.get('claims', []) if pred else [], ref['claims']
    strict_pairs = pairs(pc, rc, lambda p, r: core(p, r, True))
    relaxed_pairs = pairs(pc, rc, lambda p, r: core(p, r, False))
    labels = {l for c in pc for l in c.get('labels', [])}
    expected = {l for c in rc for l in c['labels']}
    detected = pred.get('current_error') if valid else None
    row = {**meta, 'method': method, 'received': output is not None,
           'api_success': output is not None and output['status'] == 'api_success',
           'valid_detection': valid, 'schema_valid': bool(output and output.get('schema_valid')),
           'truncated': bool(output and output.get('finish_reason') == 'length'),
           'expected_error': ref['current_error'], 'predicted_error': detected,
           'detection_correct': valid and detected == ref['current_error'],
           'labels': sorted(labels), 'expected_labels': sorted(expected),
           'labels_correct': valid and labels == expected,
           'core_exact': prf(len(strict_pairs), len(pc) - len(strict_pairs), len(rc) - len(strict_pairs)),
           'core_overlap': prf(len(relaxed_pairs), len(pc) - len(relaxed_pairs), len(rc) - len(relaxed_pairs)),
           'reference_claim_count': len(rc), 'predicted_claim_count': len(pc),
           'core_pairs': relaxed_pairs,
           'temporal_correct': sum(support_ok(pc[i], rc[j]) for i, j in relaxed_pairs),
           'temporal_label_correct': sum(pc[i].get('temporal_status') == rc[j].get('temporal_status') for i, j in relaxed_pairs),
           'core_matched_count': len(relaxed_pairs),
           'basis_correct': sum(basis_ok(pc[i], rc[j]) for i, j in relaxed_pairs),
           'joint_class_time_correct': sum(set(pc[i].get('labels', [])) == set(rc[j]['labels']) and support_ok(pc[i], rc[j]) for i, j in relaxed_pairs),
           'strict_full_correct': sum(set(pc[i].get('labels', [])) == set(rc[j]['labels']) and support_ok(pc[i], rc[j]) and basis_ok(pc[i], rc[j]) and pc[i].get('stance') == rc[j]['stance'] for i, j in strict_pairs)}
    if task['task_kind'] == 'B1':
        row['expected_temporal'] = rc[0]['temporal_status']
        row['predicted_temporal'] = [c.get('temporal_status') for c in pc]
    if task['task_kind'] == 'B2':
        mids = {m['message_id']: m for m in task['messages']}
        predicted_ids = set(pred.get('first_error_message_ids', [])) if pred else set()
        expected_ids = set(ref['first_error_message_ids'])
        row['first_message_correct'] = valid and predicted_ids == expected_ids and detected == ref['current_error']
        for key in ('evidence_stage', 'round', 'agent_id'):
            row['first_' + key + '_correct'] = valid and all(x in mids for x in predicted_ids) and {mids[x][key] for x in predicted_ids} == {mids[x][key] for x in expected_ids} and detected == ref['current_error']
        ptime = min(((mids[x]['evidence_stage'], mids[x]['round']) for x in predicted_ids if x in mids), default=None)
        rtime = min(((mids[x]['evidence_stage'], mids[x]['round']) for x in expected_ids), default=None)
        row['early'] = ptime is not None and rtime is not None and ptime < rtime
        row['late'] = ptime is not None and rtime is not None and ptime > rtime
        row['first_missing_or_invalid'] = bool(expected_ids) and (ptime is None or any(x not in mids for x in predicted_ids))
        row['class_and_first_correct'] = row['first_message_correct'] and row['labels_correct']
    return row


def aggregate(rows: list[dict]) -> dict:
    positives = [r for r in rows if r['expected_error']]
    negatives = [r for r in rows if not r['expected_error']]
    tp = sum(r['predicted_error'] is True for r in positives)
    fp = sum(r['predicted_error'] is True for r in negatives)
    labels = {}
    for label in ('F', 'R', 'I', 'unresolved'):
        lt = sum(label in r['labels'] and label in r['expected_labels'] for r in rows)
        lf = sum(label in r['labels'] and label not in r['expected_labels'] for r in rows)
        ln = sum(label not in r['labels'] and label in r['expected_labels'] for r in rows)
        labels[label] = prf(lt, lf, ln)
    count = len(rows)
    rc = sum(r['reference_claim_count'] for r in rows)
    matched = sum(r['core_matched_count'] for r in rows)
    out = {'expected_units': count, 'received': sum(r['received'] for r in rows), 'api_success': sum(r['api_success'] for r in rows),
           'schema_valid': sum(r['schema_valid'] for r in rows), 'valid_detection': sum(r['valid_detection'] for r in rows),
           'truncated': sum(r['truncated'] for r in rows), 'detection': prf(tp, fp, len(positives) - tp),
           'negative_false_positive_rate': ratio(fp, len(negatives)), 'negative_support': len(negatives),
           'negative_correct_rejection_rate': ratio(sum(r['predicted_error'] is False for r in negatives), len(negatives)),
           'labels': labels, 'message_exact_labels_rate': ratio(sum(r['labels_correct'] for r in rows), count),
           'core_exact': prf(*(sum(r['core_exact'][k] for r in rows) for k in ('tp', 'fp', 'fn'))),
           'core_overlap': prf(*(sum(r['core_overlap'][k] for r in rows) for k in ('tp', 'fp', 'fn'))),
           'basis_end_to_end': {'correct': sum(r['basis_correct'] for r in rows), 'denominator': rc},
           'temporal_with_support_end_to_end': {'correct': sum(r['temporal_correct'] for r in rows), 'denominator': rc},
           'temporal_label_given_core': {'correct': sum(r['temporal_label_correct'] for r in rows), 'denominator': matched},
           'joint_class_time': {'correct': sum(r['joint_class_time_correct'] for r in rows), 'denominator': rc},
           'strict_full': prf(sum(r['strict_full_correct'] for r in rows), sum(r['predicted_claim_count'] - r['strict_full_correct'] for r in rows), rc - sum(r['strict_full_correct'] for r in rows))}
    if rows[0]['task_kind'] == 'A':
        groups = {}
        for r in rows:
            groups.setdefault(r['group_id'], {})[r['variant']] = r
        success = lambda r: r['detection_correct'] and r['labels_correct']
        out['paired'] = {
            'group_count': len(groups),
            'A1_A4_all_correct': sum(all(success(g[f'A{i}']) for i in range(1, 5)) for g in groups.values()),
            'A1_A5_both_correct': sum(success(g['A1']) and success(g['A5']) for g in groups.values()),
            'A1_A6_both_correct_and_core': sum(success(g['A1']) and success(g['A6']) and g['A1']['core_overlap']['tp'] > 0 and g['A6']['core_overlap']['tp'] > 0 for g in groups.values())}
    if rows[0]['task_kind'] == 'B1':
        unknown = [r for r in rows if r['expected_temporal'] == 'unknown']
        out['missing_history_unknown'] = {'correct': sum(r['temporal_label_correct'] > 0 for r in unknown), 'denominator': len(unknown)}
        out['temporal_by_variant'] = {v: {'correct_with_support': sum(r['temporal_correct'] for r in rows if r['variant'] == v),
                                               'denominator': sum(r['reference_claim_count'] for r in rows if r['variant'] == v)} for v in sorted({r['variant'] for r in rows})}
    if rows[0]['task_kind'] == 'B2':
        out['first_error'] = {key: {'correct': sum(r[key] for r in rows), 'denominator': count}
                              for key in ('first_message_correct', 'first_evidence_stage_correct', 'first_round_correct', 'first_agent_id_correct', 'class_and_first_correct')}
        out['timing_errors'] = {key: sum(r[key] for r in rows) for key in ('early', 'late', 'first_missing_or_invalid')}
    return out


def analyze() -> dict:
    tasks = {t['task_id']: t for t in load_tasks()}
    refs = {r['task_id']: r for k in ('A', 'B1', 'B2') for r in read_rows(ROOT / f'references/{k}_references.jsonl')}
    manifest = {m['task_id']: m for m in read_rows(ROOT / 'data/group_manifest.jsonl')}
    rows = []
    for q in read_rows(ROOT / 'queue.jsonl'):
        p = ROOT / 'results/units' / (q['request_id'] + '.json')
        output = read_json(p) if p.exists() else None
        rows.append(score(tasks[q['task_id']], refs[q['task_id']], output, manifest[q['task_id']], q['method']))
    metrics = {s: {kind: {method: aggregate([r for r in rows if r['split'] == s and r['task_kind'] == kind and r['method'] == method])
                         for method in ('M0', 'M1', 'M2')} for kind in ('A', 'B1', 'B2')} for s in ('dev', 'holdout')}
    write_rows(ROOT / 'results/per_task_scores.jsonl', rows)
    write_json(ROOT / 'results/metrics.json', metrics)
    calls = [read_json(p) for p in (ROOT / 'results/calls').glob('*.json')] if (ROOT / 'results/calls').exists() else []
    resources = {m: {'physical_calls': len(cs := [c for c in calls if c['request_id'] in {q['request_id'] for q in read_rows(ROOT / 'queue.jsonl') if q['method'] == m}]),
                     'reported_total_tokens': sum(c.get('usage', {}).get('total_tokens', 0) for c in cs),
                     'reported_prompt_tokens': sum(c.get('usage', {}).get('prompt_tokens', 0) for c in cs),
                     'reported_completion_tokens': sum(c.get('usage', {}).get('completion_tokens', 0) for c in cs),
                     'unknown_usage_calls': sum(not c.get('usage') for c in cs),
                     'total_latency_seconds': sum(c.get('latency_seconds', 0) for c in cs)} for m in ('M0', 'M1', 'M2')}
    write_json(ROOT / 'results/resources.json', resources)
    lines = ['# 受控诊断 v4 R2 实验报告', '', '## 状态',
             f"192 个任务，576 个方法-任务单元；已收 {sum(r['received'] for r in rows)}，有效检测输出 {sum(r['valid_detection'] for r in rows)}。",
             f"已记录物理调用 {len(calls)}；API 失败 {sum(c['status'] == 'api_failure' for c in calls)}。",
             '参考等级：program_verified，独立人工确认 0。真实 MAD 轨迹评测尚未开展。CPU 构造与评分，不启动 GPU。', '',
             '## 分组结果', '|划分|任务|方法|已收/应收|检测 F1|核心精确 F1|核心重叠 F1|完整严格 F1|', '|---|---|---|---|---|---|---|---|']
    fmt = lambda x: '不适用' if x is None else f'{x:.3f}'
    for split, kinds in metrics.items():
        for kind, methods in kinds.items():
            for method, r in methods.items():
                if r['received'] == 0:
                    numbers = ['尚未评估'] * 4
                else:
                    numbers = [fmt(r[k]['f1']) for k in ('detection', 'core_exact', 'core_overlap', 'strict_full')]
                lines.append(f"|{split}|{kind}|{method}|{r['received']}/{r['expected_units']}|" + '|'.join(numbers) + '|')
    lines += ['', '## 研究问题', '开发集为开发表现，不能与留出合并为测试准确率。下述对比只使用已执行的留出输出。']
    for method in ('M0', 'M1', 'M2'):
        a, b, c = (metrics['holdout'][k][method] for k in ('A', 'B1', 'B2'))
        if not any(x['received'] for x in (a, b, c)):
            lines.append(f'- {method}：尚未执行留出评测，分类依据、立场/改写、历史、首次错误定位均尚未评估。')
            continue
        p = a['paired']
        lines += [f"- {method} 同错决定不同依据：A1-A4 全正确 {p['A1_A4_all_correct']}/{p['group_count']} 组。",
                  f"- {method} 立场变化：{p['A1_A5_both_correct']}/{p['group_count']} 组两条均正确；改写且核心定位正确 {p['A1_A6_both_correct_and_core']}/{p['group_count']}。",
                  f"- {method} 历史时间及支持：{b['temporal_with_support_end_to_end']}；历史不足正确未知 {b['missing_history_unknown']}。",
                  f"- {method} B2 自主首次消息定位：{c['first_error']['first_message_correct']}；过早/滞后/缺失 {c['timing_errors']}。"]
    lines += ['', '## 方法比较', '各方法增益仅为本次小样本描述；不预设 M2 优于 M0。']
    for kind in ('A', 'B1', 'B2'):
        base = metrics['holdout'][kind]['M0']
        for method in ('M1', 'M2'):
            other = metrics['holdout'][kind][method]
            if base['received'] and other['received']:
                values = []
                for key in ('detection', 'core_exact', 'core_overlap', 'strict_full'):
                    x, y = base[key]['f1'], other[key]['f1']
                    values.append(f'{key}: {y-x:+.3f}' if x is not None and y is not None else f'{key}: 不适用')
                lines.append(f"- {kind} {method} 相对 M0：" + '；'.join(values))
    lines += ['', '## 局限与解释边界',
              '- 沿用 12 道旧基础题，6/6 family 隔离；不是全新基础题泛化。开发/留出使用不同事实措辞及规则/决定句式，但仍是受控有限语言。',
              '- A/B2 采用原证据的声明发布前缀，以隔离一个决定性冲突；不修改原事实或规则，不把未发布事实当 false。',
              '- B1 前五类使用原 T4 状态重放得到的权威快照，窗口内无更正过程；仅第六类展示原始属性更正事件。只比较同一智能体、同一对象的明确可见前史。',
              '- 旧 v4 开发版发现稳定状态/更新状态背景重叠后停止，原响应与勘误保留；R2 没有复用旧响应。旧版留出调用为零。',
              '- 程序参考由独立文本识别器重读输出，并以穷举补全复核状态；正式关系判定与 M2 共享部分代码，因此不能当作独立人工金标准。',
              '- B2 为三个同步智能体、三轮的短片段；错误前消息正确且首次错误唯一。已给目标的 A/B1 不计为自主定位成绩。',
              '- 原文精确匹配与跨度 IoU>=0.5 分开；核心定位不要求规则列表完全一致，多余证据仍影响依据与完整指标。',
              '- 引文唯一时程序修复字符下标并记录 offset_repaired，原输出保留；不能把修复后定位当作纯模型字符下标成绩。',
              '- 原实验与评分不覆盖；受控结果不证明真实 MAD 诊断有效或同伴影响因果关系。',
              '- 零执行组标为尚未评估；失败保留在端到端分母。不因错误、格式或截断重复采样。',
              '', '## 成本', '```json', __import__('json').dumps(resources, ensure_ascii=False, indent=2), '```']
    write_text(ROOT / 'reports/RESULTS_ZH.md', '\n'.join(lines) + '\n')
    return metrics
