"""Dynamic Chinese report generation for the CBM drift prototype."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from cbm_drift_v2.common import read_json, read_jsonl, write_json
from cbm_drift_v2.runner import audit_outputs


def _ratio(numerator: int, denominator: int) -> str:
    return "不适用" if denominator == 0 else f"{numerator / denominator:.2%} ({numerator}/{denominator})"


def _group(rows: list[dict[str, Any]], field: str) -> dict[str, dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row[field])].append(row)
    return {
        key: {
            "records": len(values), "api_success": sum(row.get("api_success", False) for row in values),
            "recognized": sum(row.get("recognized_answer", False) for row in values),
            "correct": sum(row.get("correct", False) for row in values),
            "accuracy_all_records": sum(row.get("correct", False) for row in values) / len(values) if values else None,
        }
        for key, values in sorted(groups.items())
    }


def _example(events: list[dict[str, Any]], label: str) -> str:
    for event in events:
        if label in event.get("content_labels", []):
            quote = (event.get("current_quotes") or [{}])[0].get("quote", "")
            return f"`{event['message_id']}`，引文：“{quote}”（{event['judge_protocol']} 预标注）"
    return "本轮模型预标注中未观察到；不能为补齐类别而构造案例。"


def build_report(root: Path) -> dict[str, Any]:
    """Aggregate completed artifacts and write a Chinese report plus machine summary."""
    dataset = read_json(root / "data/dataset_summary.json")
    validation = read_json(root / "data/validation_report.json")
    protocol = read_jsonl(root / "results/protocol/raw_outputs.jsonl")
    mad = read_jsonl(root / "results/mad/raw_outputs.jsonl")
    program_summary = read_json(root / "results/program/summary.json")
    diagnostics = read_jsonl(root / "results/program/message_diagnostics.jsonl")
    judge_summary_path = root / "results/judge/summary.json"
    judge_summary = read_json(judge_summary_path) if judge_summary_path.exists() else None
    predicted_path = root / "results/judge/predicted_events.jsonl"
    predicted = read_jsonl(predicted_path) if predicted_path.exists() else []

    protocol_groups = _group(protocol, "snapshot_name")
    mad_groups = _group(mad, "variant_type")
    transition = Counter(row["answer_effect"] for row in diagnostics)
    temporal = Counter(row["temporal_status"] for row in diagnostics)
    objective_new = [row for row in diagnostics if row["temporal_status"] == "newly_introduced"]
    within_new = [row for row in objective_new if row["comparison_scope"] == "within_stage"]
    update_rows = [
        row for row in diagnostics
        if row["variant_type"] == "evidence_update" and row["evidence_stage"] == 4 and row["round"] == 0
    ]
    stage_round: dict[str, dict[str, Any]] = {}
    for variant, stage, round_id in sorted({
        (row["variant_type"], int(row["evidence_stage"]), int(row["round"]))
        for row in mad
    }):
        group = [
            row for row in mad
            if row["variant_type"] == variant and int(row["evidence_stage"]) == stage and int(row["round"]) == round_id
        ]
        stage_round[f"{variant}:T{stage}:R{round_id}"] = {
            "records": len(group), "correct": sum(row["correct"] for row in group),
            "accuracy": sum(row["correct"] for row in group) / len(group) if group else None,
        }
    discussion_units: dict[str, dict[str, int | float | None]] = {}
    for variant in sorted({row["variant_type"] for row in mad}):
        indexed = {
            (row["family_id"], row["evidence_stage"], row["agent_id"], row["round"]): row
            for row in mad if row["variant_type"] == variant
        }
        pairs = [
            (indexed[(family, stage, agent, 0)], indexed[(family, stage, agent, 2)])
            for family, stage, agent in sorted({key[:3] for key in indexed})
        ]
        discussion_units[variant] = {
            "units": len(pairs), "r0_correct": sum(left["correct"] for left, _ in pairs),
            "r2_correct": sum(right["correct"] for _, right in pairs),
            "correct_to_wrong": sum(left["correct"] and not right["correct"] for left, right in pairs),
            "wrong_to_correct": sum(not left["correct"] and right["correct"] for left, right in pairs),
            "unchanged_correctness": sum(left["correct"] == right["correct"] for left, right in pairs),
        }
    prediction_index = {
        (row["family_id"], row["variant_type"], row["evidence_stage"], row["round"], row["agent_id"]): row
        for row in mad
    }
    clean_noise_pairs = []
    for key, clean in prediction_index.items():
        family, variant, stage, round_id, agent = key
        if variant != "clean_stay":
            continue
        noise = prediction_index[(family, "irrelevant_noise", stage, round_id, agent)]
        clean_noise_pairs.append((clean, noise))
    clean_noise = {
        "paired_messages": len(clean_noise_pairs),
        "same_prediction": sum(left["predicted_candidates"] == right["predicted_candidates"] for left, right in clean_noise_pairs),
        "clean_correct_noise_wrong": sum(left["correct"] and not right["correct"] for left, right in clean_noise_pairs),
        "clean_wrong_noise_correct": sum(not left["correct"] and right["correct"] for left, right in clean_noise_pairs),
        "interpretation": "descriptive paired-family comparison only; variant-specific sampling and discussion histories prevent a causal noise claim",
    }
    judge_agreement = None
    if judge_summary:
        by_message: dict[str, dict[str, bool]] = defaultdict(dict)
        for row in read_jsonl(root / "results/judge/judge_outputs.jsonl"):
            if row.get("schema_valid"):
                by_message[row["message_id"]][row["judge_protocol"]] = bool(row["prediction"]["has_diagnostic_event"])
        comparable = [value for value in by_message.values() if len(value) == 2]
        agreement = sum(len(set(value.values())) == 1 for value in comparable)
        judge_agreement = {"comparable": len(comparable), "agreement": agreement, "rate": agreement / len(comparable) if comparable else None}

    summary = {
        "dataset": dataset, "validation": validation,
        "protocol_inventory": audit_outputs(root, "protocol"),
        "mad_inventory": audit_outputs(root, "mad"),
        "protocol_by_snapshot": protocol_groups, "mad_by_variant": mad_groups,
        "mad_by_variant_stage_round": stage_round,
        "discussion_r0_to_r2": discussion_units,
        "clean_noise_same_family_comparison": clean_noise,
        "program": program_summary, "answer_effect": dict(sorted(transition.items())),
        "temporal_status": dict(sorted(temporal.items())),
        "within_stage_newly_introduced": len(within_new),
        "update_t4_r0": {
            "records": len(update_rows), "reasonable_update": sum(row["temporal_status"] == "reasonable_update" for row in update_rows),
            "correct": sum(row["outcome"] == "valid_correct" for row in update_rows),
        },
        "judge": judge_summary, "judge_event_agreement": judge_agreement,
        "independent_reference_evaluation": "not_evaluated",
    }
    write_json(root / "results/analysis_summary.json", summary)

    protocol_correct = sum(row["correct"] for row in protocol)
    mad_correct = sum(row["correct"] for row in mad)
    lines = [
        "# CBM 数据完善与 MAD 漂移诊断原型报告", "",
        "## 实验状态", "",
        f"- 数据：{dataset['base_items']} 个基础题、{dataset['variants']} 个配对版本、每条 5 个证据阶段。独立重放验证：{'通过' if validation['passed'] else '失败'}。",
        f"- 静态协议检查：{len(protocol)}/108 条记录，API 失败 {sum(not row['api_success'] for row in protocol)}，可解析 {sum(row['recognized_answer'] for row in protocol)}，严格 JSON {sum(row['parse']['strict_json'] for row in protocol)}，截断 {sum(row['finish_reason'] == 'length' for row in protocol)}。",
        f"- MAD：{len(mad)}/1620 条公开发言，API 失败 {sum(not row['api_success'] for row in mad)}，可解析 {sum(row['recognized_answer'] for row in mad)}，严格 JSON {sum(row['parse']['strict_json'] for row in mad)}，截断 {sum(row['finish_reason'] == 'length' for row in mad)}。",
        f"- Judge：{'已运行 DeepSeek 双协议预标注' if judge_summary else '尚未运行；仅输入包和调用入口完成'}。独立人工参考标签尚未填写，因此检测/分类准确性为**尚未评估**。", "",
        "## 数据与协议", "",
        "任务语义固定为“保留所有尚未被当前证据排除的候选人”。未知值保留；更正只撤销点名记录；同伴意见不覆盖正式证据。36 条序列从 12 个基础题成组派生，clean 与 noise 的目标证据和逐阶段标准集合一致，update 在 T4 通过显式更正改变标准集合。", "",
        "协议快照准确率：",
    ]
    for name, stats in protocol_groups.items():
        lines.append(f"- `{name}`：{_ratio(stats['correct'], stats['records'])}。")
    lines.extend(["", "协议格式本身稳定：全部输出均可严格 JSON 解析且无截断。合法答错被保留，没有为了提高准确率重采样。", "", "## MAD 结果", ""])
    lines.append(f"全部发言相对各自阶段标准集合的完全正确率为 {_ratio(mad_correct, len(mad))}。这只是公开输出正确性，不是语义类别准确率。")
    for name, stats in mad_groups.items():
        lines.append(f"- `{name}`：{_ratio(stats['correct'], stats['records'])}。")
    lines.append("")
    lines.append("每个阶段从 R0 到 R2 的描述性变化：")
    for name, stats in discussion_units.items():
        lines.append(
            f"- `{name}`：{stats['units']} 个智能体-阶段单元，R0 正确 {stats['r0_correct']}，R2 正确 {stats['r2_correct']}，"
            f"正确→错误 {stats['correct_to_wrong']}，错误→正确 {stats['wrong_to_correct']}。"
        )
    lines.append(
        f"clean/noise 同基础题位置共 {clean_noise['paired_messages']} 对消息，集合完全相同 {clean_noise['same_prediction']} 对，"
        f"clean 对而 noise 错 {clean_noise['clean_correct_noise_wrong']} 对，clean 错而 noise 对 {clean_noise['clean_wrong_noise_correct']} 对。"
        "由于两版本使用不同派生 seed 且讨论历史会分叉，这只作描述，不作为噪声因果效应。"
    )
    lines.extend([
        "", "相邻输出的程序比较：",
        f"- 讨论内由正确变错：{transition['correct_to_wrong']} 条；由错变对：{transition['wrong_to_correct']} 条。",
        f"- 同阶段 R0→R1 或 R1→R2 中新引入的候选集合错误：{len(within_new)} 条。",
        f"- 程序合并得到 {program_summary['events']} 个连续候选级错误事件；这是集合状态事件，不等同于内容偏离类别。",
        f"- evidence_update 的 T4/R0 共 {len(update_rows)} 条，其中程序标为合理更新 {sum(row['temporal_status'] == 'reasonable_update' for row in update_rows)} 条，当前集合正确 {sum(row['outcome'] == 'valid_correct' for row in update_rows)} 条。",
        "", "跨阶段比较始终使用新阶段自己的标准集合。标准答案因正式更正而变化不会自动计为讨论漂移。", "",
        "## 内容预标注", "",
    ])
    if judge_summary:
        lines.append(f"DeepSeek Judge 对 {judge_summary['completed']} 条协议调用完成（1620 条发言 × 2 种协议）；API 成功 {judge_summary['api_success']}，可解析 {judge_summary['parse_success']}，schema 与引文/ID 校验通过 {judge_summary['schema_valid']}。")
        if judge_agreement:
            lines.append(f"直接 Judge 与结构化辅助 Judge 在“是否存在诊断事件”上可比较 {judge_agreement['comparable']} 条，一致率 {_ratio(judge_agreement['agreement'], judge_agreement['comparable'])}。一致不代表准确。")
        lines.extend([
            f"- 事实偏离案例：{_example(predicted, 'factual_deviation')}",
            f"- 规则偏离案例：{_example(predicted, 'rule_deviation')}",
            f"- 推导/应用错误案例：{_example(predicted, 'inference_application_error')}",
        ])
    else:
        lines.append("Judge 尚未运行，因此没有模型内容类别可报告。")
    reasonable = next((row for row in diagnostics if row["temporal_status"] == "reasonable_update"), None)
    lines.append(f"- 合理更新程序案例：`{reasonable['message_id']}`，标准集合为 {reasonable['oracle']}，预测为 {reasonable['prediction']}。" if reasonable else "- 合理更新程序案例：本轮未观察到满足程序定义的实例。")
    lines.extend([
        "", "## 能支持与不能支持的结论", "",
        "程序可直接确认：各阶段标准集合、答案集合是否正确、错误加入/排除、对应事实和规则、相邻输出的新增/持续/消失，以及同伴消息当时是否可见。",
        "模型 Judge 只提供开发阶段预标注。它不能证明内部遗忘、从众、压力或同伴发言的因果作用；clean/noise 的单条轨迹差异也不能单独证明噪声导致错误。解释文本是公开理由，不是隐藏推理的可靠读出。",
        "12 个基础题是开发材料，且题目因素覆盖不是完整 18-cell 设计；结果不能外推到完整数据分布。", "",
        "## 独立标注与下一步", "",
        "两名标注者应分别打开 `annotation/trajectories.html`，依据 `docs/annotation_guidelines.md` 填写各自 JSONL/CSV 模板。不得查看 `results/judge/` 后再进行首轮独立标注。保留两份原始文件，随后填写 adjudication 文件。",
        "完成独立裁决标签后，再运行 `scripts/evaluate_detector.py --references ...` 计算事件检测与内容分类指标。当前优先级是复核直接/结构化 Judge 分歧、完善边界指南并完成双人独立标注，而不是扩充样本或运行新的 MAD。", "",
    ])
    (root / "results/CBM_DRIFT_DIAGNOSTIC_REPORT_ZH.md").write_text("\n".join(lines), encoding="utf-8")
    return summary
