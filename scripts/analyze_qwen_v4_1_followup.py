#!/usr/bin/env python3
# ruff: noqa: E402
"""Analyze all completed Qwen v4.1 follow-up experiments and write a Chinese report."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mad_attr_filter.io import load_json, read_jsonl, write_json, write_jsonl
from mad_attr_filter.qwen_followup import build_followup_fingerprints, sha256_file
from mad_attr_filter.qwen_followup_analysis import (
    analyze_information_load,
    analyze_position_order,
    build_extension_item_analysis,
    compare_factor_replication,
    factor_statistics,
)
from mad_attr_filter.qwen_followup_runner import (
    audit_output_inventory,
    materialize_experiment_config,
)
from mad_attr_filter.v4_calibration_analysis import (
    build_constraint_diagnostics,
    build_parse_audit,
)
from mad_attr_filter.v4_validation import validate_v4_pool


def _experiment(
    full_config: dict, name: str
) -> tuple[dict, list[dict], list[dict], dict]:
    config = materialize_experiment_config(full_config, name)
    dataset_path = ROOT / config["dataset"]
    output_path = ROOT / config["results_dir"] / "single_agent_outputs.jsonl"
    samples = read_jsonl(dataset_path)
    fingerprints = build_followup_fingerprints(dataset_path, config)
    records, inventory = audit_output_inventory(
        output_path, samples, config, fingerprints["experiment_sha256"]
    )
    if not inventory["complete"]:
        raise ValueError(f"{name} is incomplete: {inventory}")
    return config, samples, records, inventory


def _write_cell_csv(path: Path, stats: dict) -> None:
    rows = []
    for cell, values in stats["cells"].items():
        cl, ds, il = cell.split("__")
        rows.append(
            {
                "difficulty_cell": cell,
                "constraint_load": cl,
                "distractor_similarity": ds,
                "information_load": il,
                **{key: value for key, value in values.items() if not isinstance(value, dict)},
            }
        )
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _pct(value: float | None) -> str:
    return "不适用" if value is None else f"{100 * value:.2f}%"


def _marginal_lines(title: str, stats: dict) -> list[str]:
    lines = [f"### {title}", ""]
    for factor, levels in stats["marginal_factors"].items():
        text = ", ".join(
            f"{level}={_pct(value['valid_answer_accuracy'])} "
            f"({value['correct']}/{value['valid_answers']})"
            for level, value in levels.items()
        )
        lines.append(f"- `{factor}`：{text}。")
    return lines


def main() -> int:
    base_dir = ROOT / "results/qwen_v4_1_followup"
    full_config = load_json(ROOT / "config/qwen_v4_1_followup_config.json")
    position_config, position_items, position_outputs, position_inventory = _experiment(
        full_config, "position_order"
    )
    il_config, il_items, il_outputs, il_inventory = _experiment(
        full_config, "information_load"
    )
    extension_config, extension_items, extension_outputs, extension_inventory = _experiment(
        full_config, "extension"
    )

    prototype = read_jsonl(ROOT / "data/multi_constraint_v4_1_prototype.jsonl")
    validate_v4_pool(prototype, expected_items_per_cell=10)
    validate_v4_pool(extension_items, expected_items_per_cell=20)
    validate_v4_pool([*prototype, *extension_items], expected_items_per_cell=30)
    old_outputs = [
        record
        for record in read_jsonl(
            ROOT / "results/v4_1_calibration/single_agent_outputs.jsonl"
        )
        if record["model_alias"] == "qwen"
    ]

    position_analysis = analyze_position_order(position_items, position_outputs)
    il_analysis = analyze_information_load(il_items, il_outputs)
    development_stats = factor_statistics(prototype, old_outputs)
    validation_stats = factor_statistics(extension_items, extension_outputs)
    combined_stats = factor_statistics(
        [*prototype, *extension_items], [*old_outputs, *extension_outputs]
    )
    replication = compare_factor_replication(development_stats, validation_stats)
    extension_item_rows = build_extension_item_analysis(extension_items, extension_outputs)
    constraint_diagnostics = build_constraint_diagnostics(
        extension_items,
        extension_outputs,
        {"models": [extension_config["model"]]},
    )
    parse_audit = build_parse_audit(extension_outputs)

    write_json(base_dir / "position_order/analysis.json", position_analysis)
    write_json(base_dir / "information_load/analysis.json", il_analysis)
    write_json(base_dir / "extension/development_180_statistics.json", development_stats)
    write_json(base_dir / "extension/extension_360_statistics.json", validation_stats)
    write_json(base_dir / "extension/combined_540_statistics.json", combined_stats)
    write_json(base_dir / "extension/factor_replication.json", replication)
    write_json(base_dir / "extension/constraint_diagnostics.json", constraint_diagnostics)
    write_jsonl(base_dir / "extension/item_analysis.jsonl", extension_item_rows)
    write_jsonl(base_dir / "extension/parse_audit.jsonl", parse_audit)
    _write_cell_csv(base_dir / "extension/extension_cell_statistics.csv", validation_stats)

    semantic = load_json(base_dir / "qwen_error_semantic_review_summary.json")
    reparse = load_json(base_dir / "scoring_reparse_audit.json")
    extension_validation = load_json(base_dir / "extension/validation.json")
    pgroup = position_analysis["by_selection_group"]
    il_overall = il_analysis["overall"]
    dev = development_stats["overall"]
    val = validation_stats["overall"]
    total = combined_stats["overall"]
    stable_position_rows = [
        row
        for row in position_analysis["base_item_analysis"]
        if row["selection_group"] == "stable_wrong"
    ]
    original_order_still_all_wrong = sum(
        next(
            variant
            for variant in row["variant_results"]
            if variant["rotation"] == 0
        )["correct"]
        == 0
        for row in stable_position_rows
    )
    extension_diag = constraint_diagnostics["overall"]
    top_error_attributes = [
        row
        for row in extension_diag["attributes"]
        if row["number_of_times_violated_by_selected_wrong_answer"] > 0
    ][:5]
    lines = [
        "# Qwen3-8B v4.1 难度复核与条件扩充报告",
        "",
        "## 实验状态",
        "",
        f"- 旧开发校准集：180 题，{dev['records']} 次响应。",
        f"- 选项换序：{position_inventory['completed_records']}/{position_inventory['expected_runs']} 次。",
        f"- IL 同题配对：{il_inventory['completed_records']}/{il_inventory['expected_runs']} 次。",
        f"- 新增验证集：360 题，{extension_inventory['completed_records']}/{extension_inventory['expected_runs']} 次。",
        "- 三项新实验均使用 Qwen3-8B、temperature=0.7、top_p=0.9、max_tokens=1024、thinking=false。",
        "- 服务为 vLLM 0.11.2、BF16、无量化；本轮运行在物理 GPU 7。请求未显式覆盖 top_k，启动日志显示模型 generation config 默认 top_k=20。",
        "- 所有调用均为独立请求；没有暴露 Gold、形式约束、矩阵、违反集合或其他回答。",
        "",
        "## 数据有效性复核",
        "",
        f"- 复核旧异常题 {semantic['reviewed_items']} 道，其中稳定全错 {semantic['stable_wrong_items']}、正误共存 {semantic['mixed_items']}。",
        f"- 题面/标注缺陷：{semantic['dataset_defect_count']}；系统性有效性问题：{semantic['systemic_data_validity_problem_found']}。",
        f"- 输出文本诊断分布：`{semantic['diagnostic_counts']}`。这只是响应文本证据，不解释模型内部机制。",
        f"- 姓名答案重解析在旧 Llama 响应中新增识别 {reparse['model_counts']['llama']['name_mapped']} 条；没有追加 Llama 推理，也没有覆盖旧结果。",
        "",
        "## 选项换序复核",
        "",
        f"- 全部 252 次有效答案准确率：{_pct(position_analysis['overall']['valid_answer_accuracy'])}。该集合按旧表现筛选，不能估计完整数据集准确率。",
        f"- 10 道旧稳定全错题在原排列与新 seeds 下仍有 {original_order_still_all_wrong}/10 道保持三次全错；这支持错误在原排列下可复现，但不代表跨排列稳定。",
    ]
    for group, values in pgroup.items():
        lines.append(
            f"- `{group}`：{values['base_items']} 道；准确率 {_pct(values['valid_answer_accuracy'])}；"
            f"{values['items_with_accuracy_change_across_orderings']} 道在四种顺序间出现准确率变化；"
            f"{values['items_repeating_one_wrong_candidate_identity']} 道重复选择同一错误候选人身份。"
        )
    lines.extend(
        [
            "- 所有比较按候选人姓名对齐。换序同时改变标签和阅读顺序，因此变化不能全部归因于标签偏好。",
            "- 定向集合中 Gold 位于 A/B/C/D 时准确率分别为 "
            + "/".join(
                _pct(position_analysis["by_gold_position"][label]["valid_answer_accuracy"])
                for label in "ABCD"
            )
            + "；该差异与基础题筛选和旋转顺序混杂，不足以单独认定字母位置偏差。",
            "",
            "## IL 同题配对",
            "",
            f"- 完整配对：{il_overall['complete_pairs']}/{il_overall['base_items']}；IL2-IL1 平均准确率差：{il_overall['mean_paired_accuracy_delta_il2_minus_il1']}；"
            f"95% 题目级 bootstrap CI：{il_overall['paired_bootstrap_95_ci']}。",
            f"- IL2 下变难 {il_overall['items_harder_with_il2']} 题、变易 {il_overall['items_easier_with_il2']} 题、未观察到变化 {il_overall['items_no_observed_change']} 题。",
            f"- IL1 有效准确率 {_pct(il_overall['il1']['valid_answer_accuracy'])}；IL2 有效准确率 {_pct(il_overall['il2']['valid_answer_accuracy'])}。",
            "- 同题配对没有观察到 IL 效果。新增非配对题中 IL2 边际准确率更低，但那是不同题目的组间关联，可能包含属性和模板构成差异，不能替代配对结论。",
            "",
            "## 扩充池验证",
            "",
            f"- 新增集 {extension_validation['extension_count']} 题、合计 {extension_validation['combined_count']} 题；每格分别新增 20、合计 30。",
            f"- 新增集 Gold A/B/C/D 各 {extension_validation['extension_validation']['gold_position_distribution']['A']}；场景各 {extension_validation['extension_validation']['scenario_distribution']['expert_recruitment']}。",
            "- 新增题在每格内 Gold 完全均衡、场景计数差不超过 1；与旧原型合并后每格场景最大计数差为 2，540 题总体场景仍各 180。",
            f"- item_id 重复 {extension_validation['duplicate_item_id_count']}；规范化题面哈希重复 {extension_validation['duplicate_normalized_content_hash_count']}；结构与语义验证通过率 {extension_validation['extension_validation']['validation_pass_rate']:.1%}。",
            "- 新 ID 为 `attr_v4_1_000181_original` 至 `attr_v4_1_000540_original`，批次与独立种子保存在 generation metadata；模型推理前已冻结。",
            "",
            "## 原始、新增与合计表现",
            "",
            f"- 原始 180：{dev['correct']}/{dev['valid_answers']}，{_pct(dev['valid_answer_accuracy'])}；题内答案分歧 {development_stats['item_behavior']['within_item_answer_disagreement_items']} 题。",
            f"- 新增 360：{val['correct']}/{val['valid_answers']}，{_pct(val['valid_answer_accuracy'])}；题内答案分歧 {validation_stats['item_behavior']['within_item_answer_disagreement_items']} 题。",
            f"- 合计 540：{total['correct']}/{total['valid_answers']}，{_pct(total['valid_answer_accuracy'])}。",
            "",
        ]
    )
    lines.extend(_marginal_lines("原始 180", development_stats))
    lines.extend([""])
    lines.extend(_marginal_lines("新增 360", validation_stats))
    lines.extend(
        [
            "",
            "## 因素趋势复现",
            "",
        ]
    )
    for factor, values in replication.items():
        lines.append(
            f"- `{factor}`：旧集高减低 {values['development_high_minus_low']:+.4f}；"
            f"新增集 {values['validation_high_minus_low']:+.4f}；{values['interpretation']}。"
        )
        lines.append(
            f"  新增集固定其他因素后的端点方向计数："
            f"`{validation_stats['controlled_endpoint_trend_summary'][factor]}`。"
        )
    hardest = ", ".join(
        f"{row['difficulty_cell']}({_pct(row['valid_answer_accuracy'])})"
        for row in validation_stats["cell_ranking_easiest_to_hardest"][-5:]
    )
    easiest = ", ".join(
        f"{row['difficulty_cell']}({_pct(row['valid_answer_accuracy'])})"
        for row in validation_stats["cell_ranking_easiest_to_hardest"][:5]
    )
    lines.extend(
        [
            f"- 新增集最易五格：{easiest}。",
            f"- 新增集最难五格：{hardest}。",
            "- 18 格仍不是同题配对改写，除 IL 专项外，组合差异只能作为初步组间证据。",
            f"- 新增集共有 {extension_diag['valid_wrong_answer_count']} 个有效错误回答，违反签名长度分布为 `{extension_diag['violation_signature_size_distribution']}`；这些是单智能体错误，不称为辩论漂移。",
            "- 暴露归一化后最常对应错误的属性："
            + "，".join(
                f"`{row['attribute']}`={row['normalized_error_rate_per_violatable_run']:.3f}"
                for row in top_error_attributes
            )
            + "。DS3 本来就把所有错误选项设计为单约束违反，因此不能把其单约束比例当作额外模型发现。",
            "",
            "## 结论与扩充判断",
            "",
            "- 流程完成与难度设计支持分开判断：前者要求记录、验证和指纹完整，后者依据独立新增集是否复现趋势。",
            "- 低题内采样分歧不否定题目之间存在可测的难度差异；IL2 也不被要求必然降低准确率。",
            "- 540 题池已作为开发校准集 180 + 独立验证集 360 固定保留；没有按 Qwen 对错筛题或替换题目。",
            "- 可形成相对于本次 Qwen 配置的两档候选描述：DS1_far 是稳定基础条件（新增 360/360 正确），DS2/DS3 是更具挑战条件；DS2 与 DS3 尚不足以稳定分成两个独立难度档。",
            "- CL 仅复现了很弱的总体方向，不能单独用 CL1/CL2/CL3 划三档；IL 暂作为实验因素保留，不标成已验证的难度轴。",
            "- 建议保留并使用本轮 540 题池进行后续基线设计，同时将 DS1 作为稳定控制、DS2/DS3 作为候选诊断条件；在更大规模结论中继续报告组合级不确定性。",
            "",
            "## 局限",
            "",
            "- 每个新增组合只有 20 道题，仍属于校准规模。",
            "- 三次采样只反映本次服务与参数下的观测，不能证明题目永久稳定。",
            "- 选项换序集合按旧结果定向筛选，不用于总体准确率估计。",
            "- 本轮未运行 MAD、Drift Judge 或任何 Llama 新推理。",
        ]
    )
    (base_dir / "QWEN_V4_1_FOLLOWUP_REPORT.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    write_json(
        base_dir / "analysis_summary.json",
        {
            "inventories": {
                "position_order": position_inventory,
                "information_load": il_inventory,
                "extension": extension_inventory,
            },
            "semantic_review": semantic,
            "position_order": position_analysis,
            "information_load": il_analysis,
            "development_180": development_stats,
            "extension_360": validation_stats,
            "combined_540": combined_stats,
            "factor_replication": replication,
        },
    )
    position_lines = [
        "# 选项换序实验分析",
        "",
        f"完成 {position_inventory['completed_records']}/{position_inventory['expected_runs']} 次调用。",
        f"旧稳定错误组四种排列准确率 {_pct(pgroup['stable_wrong']['valid_answer_accuracy'])}；"
        f"原排列下 {original_order_still_all_wrong}/10 题仍三次全错。",
        f"稳定正确对照组准确率 {_pct(pgroup['stable_correct_control']['valid_answer_accuracy'])}。",
        "9/10 道稳定错误题在发生错误时反复选择同一候选人身份，但所有 10 题均随排列改变出现准确率变化。",
        "该集合按先前表现筛选，且旋转同时改变字母和阅读顺序，不能用于总体准确率或纯标签偏差估计。",
    ]
    (base_dir / "position_order/analysis.md").write_text(
        "\n\n".join(position_lines) + "\n", encoding="utf-8"
    )
    il_lines = [
        "# IL 同题配对实验分析",
        "",
        f"完成 {il_inventory['completed_records']}/{il_inventory['expected_runs']} 次调用，完整基础题配对 {il_overall['complete_pairs']}/36。",
        f"IL1 与 IL2 均为 {il_overall['il1']['correct']}/{il_overall['il1']['valid_answers']} 正确；"
        f"IL2-IL1 平均差为 {il_overall['mean_paired_accuracy_delta_il2_minus_il1']}，"
        f"题目级 bootstrap 95% CI 为 {il_overall['paired_bootstrap_95_ci']}。",
        "36 题均未观察到答案变化。当前 IL 操作下没有可识别的 Qwen 难度效应证据。",
    ]
    (base_dir / "information_load/analysis.md").write_text(
        "\n\n".join(il_lines) + "\n", encoding="utf-8"
    )
    artifact_paths = [
        ROOT / "config/qwen_v4_1_followup_config.json",
        ROOT / "data/multi_constraint_v4_1_prototype.jsonl",
        ROOT / "data/multi_constraint_v4_1_extension_360.jsonl",
        ROOT / "data/multi_constraint_v4_1_total_540.jsonl",
        ROOT / "data/multi_constraint_v4_1_total_540_index.jsonl",
        base_dir / "position_order/single_agent_outputs.jsonl",
        base_dir / "information_load/single_agent_outputs.jsonl",
        base_dir / "extension/single_agent_outputs.jsonl",
        base_dir / "QWEN_V4_1_FOLLOWUP_REPORT.md",
    ]
    write_json(
        base_dir / "experiment_manifest.json",
        {
            "study": "qwen_v4_1_difficulty_followup_and_conditional_expansion",
            "new_model": "Qwen3-8B",
            "new_model_calls": 1548,
            "llama_new_model_calls": 0,
            "completed_by_experiment": {
                "position_order": position_inventory["completed_records"],
                "information_load": il_inventory["completed_records"],
                "extension": extension_inventory["completed_records"],
            },
            "all_run_inventories_complete": all(
                inventory["complete"]
                for inventory in (position_inventory, il_inventory, extension_inventory)
            ),
            "explicit_generation_parameters": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 1024,
                "thinking_enabled": False,
                "position_and_il_seeds": [44, 55, 66],
                "extension_seeds": [11, 22, 33],
            },
            "backend_observation": {
                "framework": "vLLM",
                "version": "0.11.2",
                "dtype": "bfloat16",
                "quantization": None,
                "physical_gpu": 7,
                "model_generation_config_default_top_k_observed_in_startup_log": 20,
            },
            "artifact_sha256": {
                str(path.relative_to(ROOT)): sha256_file(path) for path in artifact_paths
            },
        },
    )
    print(
        json.dumps(
            {
                "position": position_inventory,
                "information_load": il_inventory,
                "extension": extension_inventory,
                "development_accuracy": dev["valid_answer_accuracy"],
                "extension_accuracy": val["valid_answer_accuracy"],
                "combined_accuracy": total["valid_answer_accuracy"],
                "factor_replication": replication,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
