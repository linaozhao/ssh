#!/usr/bin/env python3
# ruff: noqa: E402
"""Build semantic and name-aware scoring audits from saved calibration outputs."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mad_attr_filter.io import read_jsonl, write_json, write_jsonl
from mad_attr_filter.qwen_followup_analysis import (
    build_reparse_audit,
    build_semantic_review,
)


def main() -> int:
    output_dir = ROOT / "results/qwen_v4_1_followup"
    output_dir.mkdir(parents=True, exist_ok=True)
    samples = read_jsonl(ROOT / "data/multi_constraint_v4_1_prototype.jsonl")
    item_rows = read_jsonl(ROOT / "results/v4_1_calibration/item_model_analysis.jsonl")
    outputs = read_jsonl(ROOT / "results/v4_1_calibration/single_agent_outputs.jsonl")
    reviews, summary = build_semantic_review(samples, item_rows, outputs)
    write_jsonl(output_dir / "qwen_error_semantic_review.jsonl", reviews)
    write_json(output_dir / "qwen_error_semantic_review_summary.json", summary)
    write_json(
        output_dir / "data_issue_list.json",
        {
            "issue_count": sum(review["dataset_defect_found"] for review in reviews),
            "issues": [review for review in reviews if review["dataset_defect_found"]],
            "old_data_or_gold_modified": False,
        },
    )
    write_json(output_dir / "scoring_reparse_audit.json", build_reparse_audit(samples, outputs))

    lines = [
        "# Qwen v4.1 稳定错误语义复核",
        "",
        "本文件是智能体依据题面、结构化字段和已保存输出完成的语义复核，不是人工标注，"
        "也不把输出文本诊断解释为模型内部认知机制。",
        "",
        f"- 复核题目：{summary['reviewed_items']}（稳定全错 {summary['stable_wrong_items']}，正误共存 {summary['mixed_items']}）",
        f"- 发现题面或标注缺陷：{summary['dataset_defect_count']}",
        f"- 错误响应：{summary['wrong_response_count']}",
        f"- 输出文本诊断：`{summary['diagnostic_counts']}`",
        "",
    ]
    for review in reviews:
        lines.extend(
            [
                f"## {review['item_id']}",
                "",
                f"- 状态：`{review['screening_status']}`；组合：`{review['difficulty_cell']}`；Gold：`{review['gold_answer']}`",
                f"- 复核结论：{review['review_conclusion']}",
                f"- 远程与现场同时要求（不冲突但较特殊）：{review['unusual_but_satisfiable_remote_and_onsite_pair']}",
            ]
        )
        for evidence in review["run_evidence"]:
            if evidence["correct"]:
                lines.append(
                    f"- run {evidence['run_id']}：回答 {evidence['answer']}，正确。解释：{evidence['reasoning']}"
                )
                continue
            violations = "; ".join(
                f"{value['constraint_id']} {value['requirement_text']} / 题面事实: {value['selected_candidate_fact']}"
                for value in evidence["violated_constraints"]
            )
            lines.append(
                f"- run {evidence['run_id']}：回答 {evidence['answer']}（{evidence['selected_candidate']}），"
                f"违反 `{evidence['violation_signature']}`；{violations}。"
            )
            lines.append(
                f"  输出文本证据：{evidence['reasoning']} 诊断：`{evidence['reasoning_diagnostic']}`。"
            )
        lines.append("")
    (output_dir / "qwen_error_semantic_review.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
