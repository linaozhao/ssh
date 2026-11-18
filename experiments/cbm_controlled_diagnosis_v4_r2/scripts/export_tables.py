"""Export frozen metric values without changing scoring or selecting outcomes."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'lib'))
from common import ROOT, read_json, write_text


def fraction(row: dict) -> float | None:
    return row['correct'] / row['denominator'] if row['denominator'] else None


def main() -> None:
    metrics = read_json(ROOT / 'results/metrics.json')
    rows = []
    for split, kinds in metrics.items():
        for task, methods in kinds.items():
            for method, r in methods.items():
                row = {'split': split, 'task': task, 'method': method,
                       'expected_units': r['expected_units'], 'received': r['received'],
                       'detection_f1': r['detection']['f1'],
                       'negative_false_positive_rate': r['negative_false_positive_rate'],
                       'core_exact_f1': r['core_exact']['f1'], 'core_overlap_f1': r['core_overlap']['f1'],
                       'strict_full_f1': r['strict_full']['f1'],
                       'temporal_label_given_core': fraction(r['temporal_label_given_core']),
                       'temporal_with_support_end_to_end': fraction(r['temporal_with_support_end_to_end']),
                       'basis_end_to_end': fraction(r['basis_end_to_end']),
                       'joint_class_time': fraction(r['joint_class_time'])}
                row.update({f'{label}_f1': r['labels'][label]['f1'] for label in ('F', 'R', 'I', 'unresolved')})
                row['A1_A4_groups_correct'] = r.get('paired', {}).get('A1_A4_all_correct')
                row['A1_A5_pairs_correct'] = r.get('paired', {}).get('A1_A5_both_correct')
                row['A1_A6_pairs_correct_core'] = r.get('paired', {}).get('A1_A6_both_correct_and_core')
                row['B2_first_message_accuracy'] = fraction(r['first_error']['first_message_correct']) if 'first_error' in r else None
                if not r['received']:
                    for key in row.keys() - {'split', 'task', 'method', 'expected_units', 'received'}:
                        row[key] = None
                rows.append(row)
    with (ROOT / 'results/summary_tables.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    display = lambda x: '尚未评估/不适用' if x is None else f'{x:.3f}'
    lines = ['# 留出集核心结果表', '',
             '每任务每方法只有6个基础题family；报告为描述性结果，未计算显著性或独立题目置信区间。',
             '数据来自冻结的主评分器。参考为程序核验，不是人工金标。', '',
             '|任务|方法|完成|检测F1|核心精确F1|核心重叠F1|完整严格F1|',
             '|---|---|---|---|---|---|---|']
    for r in rows:
        if r['split'] == 'holdout':
            values = [display(r[k]) for k in ('detection_f1', 'core_exact_f1', 'core_overlap_f1', 'strict_full_f1')]
            lines.append(f"|{r['task']}|{r['method']}|{r['received']}/{r['expected_units']}|" + '|'.join(values) + '|')
    lines += ['', 'B2在每条轨迹内只有一个证据阶段，阶段匹配本身不是强定位证据；重点看轮次、智能体和消息匹配。',
              'A/B1目标消息已知，其核心定位不是自主发现错误位置的成绩。',
              'M2部分形式核验与程序参考共享实现，较高成绩仍需要独立人工参考确认。']
    write_text(ROOT / 'reports/HOLDOUT_TABLES_ZH.md', '\n'.join(lines) + '\n')
    print('Exported 18 split-task-method rows')


if __name__ == '__main__':
    main()
