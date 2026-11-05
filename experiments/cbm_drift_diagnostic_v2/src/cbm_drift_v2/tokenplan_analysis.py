"""Descriptive analysis and matched comparisons for configured TokenPlan Judges."""

from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
import re
from statistics import mean, median
from typing import Any

from cbm_drift_v2.common import read_json, read_jsonl, write_json, write_jsonl
from cbm_drift_v2.tokenplan_judge import atomic_write_json, results_directory, utc_now


def _ratio(numerator: int, denominator: int) -> float | None:
    return None if denominator == 0 else numerator / denominator


def _usage_total(rows: list[dict[str, Any]], *keys: str) -> int:
    total = 0
    for row in rows:
        value: Any = row.get("usage") or {}
        for key in keys:
            value = value.get(key, {}) if isinstance(value, dict) else {}
        if isinstance(value, (int, float)):
            total += int(value)
    return total


def _prediction_events(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    events = []
    for row in rows:
        prediction = row.get("prediction") or {}
        if not row.get("schema_valid") or not prediction.get("has_diagnostic_event"):
            continue
        claims = prediction.get("claims") or []
        events.append({
            "event_id": "tokenplan:" + row["judge_request_id"],
            "label_source": re.sub(r"[^a-z0-9]+", "_", row.get("requested_model", "deepseek-v4-pro").split("/")[-1].lower()) + "_model_preannotation",
            "judge_model": row.get("requested_model"),
            "judge_protocol": row["judge_protocol"],
            "message_id": row["message_id"],
            "base_item_id": row["base_item_id"],
            "variant_id": row["variant_id"],
            "trajectory_id": row["trajectory_id"],
            "evidence_stage": row["evidence_stage"],
            "round": row["round"],
            "agent_id": row["agent_id"],
            "temporal_status": prediction["temporal_status"],
            "content_labels": prediction["content_labels"],
            "answer_effect": prediction["answer_effect"],
            "target_entity_ids": sorted({value for claim in claims for value in claim.get("target_entity_ids", [])}),
            "violated_fact_ids": sorted({value for claim in claims for value in claim.get("violated_fact_ids", [])}),
            "violated_rule_ids": sorted({value for claim in claims for value in claim.get("violated_rule_ids", [])}),
            "current_quotes": [
                {
                    "quote": claim.get("quote"), "start": claim.get("start"), "end": claim.get("end"),
                    "stance": claim.get("stance"),
                }
                for claim in claims
            ],
            "related_peer_message_ids": prediction.get("related_peer_message_ids") or [],
            "uncertainty_reason": prediction.get("uncertainty_reason"),
            "quote_and_id_validation_passed": True,
            "experiment_fingerprint": row["experiment_fingerprint"],
        })
    return events


def _performance(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize observed resource use, without assuming a provider credit conversion."""
    successful = [row for row in rows if row.get("api_success")]
    latencies = [row["latency_seconds"] for row in successful if isinstance(row.get("latency_seconds"), (int, float))]
    with_usage = [row for row in successful if row.get("usage") is not None]
    result = {
        "api_successful_records": len(successful),
        "latency_records": len(latencies),
        "mean_latency_seconds": mean(latencies) if latencies else None,
        "median_latency_seconds": median(latencies) if latencies else None,
        "records_with_usage": len(with_usage),
    }
    for name, keys in (
        ("prompt_tokens", ("prompt_tokens",)),
        ("completion_tokens", ("completion_tokens",)),
        ("reasoning_tokens", ("completion_tokens_details", "reasoning_tokens")),
    ):
        observed = []
        for row in with_usage:
            value = row["usage"]
            for key in keys:
                value = value.get(key) if isinstance(value, dict) else None
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                observed.append(value)
        result[f"{name}_records"] = len(observed)
        result[f"mean_{name}"] = mean(observed) if observed else None
    return result


def compare_judge_models(root: Path, results: Path, rows: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    """Compare identical requests only; agreement is not diagnostic accuracy."""
    comparison = config.get("comparison_results_dir")
    if not comparison:
        return {"status": "not_configured"}
    baseline = results_directory(root, {"results_dir": comparison})
    if baseline == results:
        raise ValueError("comparison_results_dir must differ from results_dir")
    manifest_path = baseline / "experiment_manifest.json"
    outputs_path = baseline / "judge_outputs.jsonl"
    if not manifest_path.exists() or not outputs_path.exists():
        return {"status": "baseline_not_available"}
    old_manifest = read_json(manifest_path)
    current_manifest = read_json(results / "experiment_manifest.json")
    if old_manifest["data"] != current_manifest["data"] or old_manifest["prompts"] != current_manifest["prompts"]:
        raise ValueError("Comparison requires identical data and prompts")
    old_rows = read_jsonl(outputs_path)
    if len({row["judge_request_id"] for row in old_rows}) != len(old_rows):
        raise ValueError("Duplicate baseline Judge outputs")
    if any(row.get("experiment_fingerprint") != old_manifest["experiment_fingerprint"] for row in old_rows):
        raise ValueError("Baseline output fingerprint mismatch")
    old_by_id = {row["judge_request_id"]: row for row in old_rows}
    pairs = []
    for row in rows:
        old = old_by_id.get(row["judge_request_id"])
        if old is None:
            continue
        if old["input_sha256"] != row["input_sha256"]:
            raise ValueError("Matched request input fingerprint mismatch")
        pairs.append((old, row))
    valid = [(old, new) for old, new in pairs if old.get("schema_valid") and new.get("schema_valid")]
    api_pairs = [(old, new) for old, new in pairs if old.get("api_success") and new.get("api_success")]
    usage_pairs = [
        (old, new) for old, new in api_pairs
        if all(isinstance((row.get("usage") or {}).get("completion_tokens"), (int, float)) for row in (old, new))
    ]
    comparisons = [{
        "judge_request_id": new["judge_request_id"],
        "judge_protocol": new["judge_protocol"],
        "event_presence_agrees": old["prediction"]["has_diagnostic_event"] == new["prediction"]["has_diagnostic_event"],
        "content_label_set_agrees": set(old["prediction"]["content_labels"]) == set(new["prediction"]["content_labels"]),
        "temporal_status_agrees": old["prediction"]["temporal_status"] == new["prediction"]["temporal_status"],
        "answer_effect_agrees": old["prediction"]["answer_effect"] == new["prediction"]["answer_effect"],
    } for old, new in valid]
    write_jsonl(results / "matched_model_comparison.jsonl", comparisons)
    return {
        "status": "observed_matched_requests" if pairs else "awaiting_current_responses",
        "baseline_directory": comparison,
        "baseline_model": old_manifest["config"]["model_name"],
        "current_model": config["model_name"],
        "baseline_completed_records": len(old_rows),
        "matched_records": len(pairs),
        "both_api_successful": len(api_pairs),
        "both_schema_valid": len(valid),
        "baseline_performance_on_matched_api_successes": _performance([old for old, _ in api_pairs]),
        "current_performance_on_matched_api_successes": _performance([new for _, new in api_pairs]),
        "both_reported_usage_pairs": len(usage_pairs),
        "mean_completion_token_difference_current_minus_baseline": mean(
            new["usage"].get("completion_tokens", 0) - old["usage"].get("completion_tokens", 0)
            for old, new in usage_pairs
        ) if usage_pairs else None,
        "agreement": {
            key: {"numerator": sum(row[key] for row in comparisons), "denominator": len(comparisons),
                  "rate": _ratio(sum(row[key] for row in comparisons), len(comparisons))}
            for key in ("event_presence_agrees", "content_label_set_agrees", "temporal_status_agrees", "answer_effect_agrees")
        },
        "by_protocol": {
            protocol: {
                "matched_records": sum(new["judge_protocol"] == protocol for _, new in pairs),
                "both_schema_valid": sum(row["judge_protocol"] == protocol for row in comparisons),
            }
            for protocol in ("direct", "structured_assistance")
        },
        "interpretation": "Matched observed requests only; agreement is not accuracy. Latency includes transport/retries and may differ across service periods.",
    }


def analyze_tokenplan_judge(root: Path, config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Analyze all currently completed records without treating predictions as Gold."""
    results = results_directory(root, config)
    manifest = read_json(results / "experiment_manifest.json")
    queue = read_jsonl(results / "request_queue.jsonl")
    outputs_path = results / "judge_outputs.jsonl"
    rows = read_jsonl(outputs_path) if outputs_path.exists() else []
    queue_ids = {row["judge_request_id"] for row in queue}
    output_ids = [row["judge_request_id"] for row in rows]
    if len(output_ids) != len(set(output_ids)):
        raise ValueError("Duplicate TokenPlan Judge outputs")
    if set(output_ids) - queue_ids:
        raise ValueError("Unknown TokenPlan Judge output IDs")
    if any(row.get("experiment_fingerprint") != manifest["experiment_fingerprint"] for row in rows):
        raise ValueError("TokenPlan Judge output fingerprint mismatch")

    by_protocol: dict[str, dict[str, Any]] = {}
    for protocol in ("direct", "structured_assistance"):
        protocol_rows = [row for row in rows if row["judge_protocol"] == protocol]
        valid = [row for row in protocol_rows if row.get("schema_valid")]
        predictions = [row["prediction"] for row in valid]
        by_protocol[protocol] = {
            "expected": sum(row["judge_protocol"] == protocol for row in queue),
            "completed": len(protocol_rows),
            "api_success": sum(row.get("api_success", False) for row in protocol_rows),
            "parse_success": sum(row.get("parse_success", False) for row in protocol_rows),
            "schema_valid": len(valid),
            "truncated": sum(row.get("finish_reason") == "length" for row in protocol_rows),
            "diagnostic_event_yes": sum(prediction.get("has_diagnostic_event") is True for prediction in predictions),
            "diagnostic_event_no": sum(prediction.get("has_diagnostic_event") is False for prediction in predictions),
            "content_labels": dict(sorted(Counter(
                label for prediction in predictions for label in prediction.get("content_labels", [])
            ).items())),
            "temporal_status": dict(sorted(Counter(
                prediction.get("temporal_status") for prediction in predictions
            ).items())),
            "answer_effect": dict(sorted(Counter(
                prediction.get("answer_effect") for prediction in predictions
            ).items())),
            "with_uncertainty_reason": sum(bool(prediction.get("uncertainty_reason")) for prediction in predictions),
            "performance": _performance(protocol_rows),
        }

    by_message: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        if row.get("schema_valid") and row.get("is_paired_sample"):
            by_message[row["message_id"]][row["judge_protocol"]] = row
    paired = []
    for message_id, values in sorted(by_message.items()):
        if set(values) != {"direct", "structured_assistance"}:
            continue
        direct = values["direct"]["prediction"]
        structured = values["structured_assistance"]["prediction"]
        paired.append({
            "message_id": message_id,
            "base_item_id": values["direct"]["base_item_id"],
            "variant_id": values["direct"]["variant_id"],
            "evidence_stage": values["direct"]["evidence_stage"],
            "round": values["direct"]["round"],
            "agent_id": values["direct"]["agent_id"],
            "event_presence_agrees": direct.get("has_diagnostic_event") == structured.get("has_diagnostic_event"),
            "content_label_set_agrees": set(direct.get("content_labels", [])) == set(structured.get("content_labels", [])),
            "temporal_status_agrees": direct.get("temporal_status") == structured.get("temporal_status"),
            "answer_effect_agrees": direct.get("answer_effect") == structured.get("answer_effect"),
            "direct_prediction": direct,
            "structured_prediction": structured,
        })

    events = _prediction_events(rows)
    write_jsonl(results / "predicted_events.jsonl", events)
    write_jsonl(results / "paired_protocol_comparison.jsonl", paired)
    parse_audit = [
        {
            "judge_request_id": row["judge_request_id"],
            "message_id": row["message_id"],
            "judge_protocol": row["judge_protocol"],
            "api_success": row["api_success"],
            "terminal_reason": row.get("terminal_reason"),
            "parse_source": row.get("parse_source"),
            "parse_success": row.get("parse_success"),
            "schema_valid": row.get("schema_valid"),
            "validation_errors": row.get("validation_errors"),
            "normalization_actions": row.get("normalization_actions"),
            "finish_reason": row.get("finish_reason"),
            "raw_response": row.get("raw_response"),
        }
        for row in rows
        if not row.get("api_success") or not row.get("parse_success") or not row.get("schema_valid")
        or row.get("finish_reason") == "length" or row.get("normalization_actions")
    ]
    write_jsonl(results / "parse_and_quote_audit.jsonl", parse_audit)
    state_path = results / "scheduler_state.json"
    state = read_json(state_path) if state_path.exists() else {"status": "not_started"}
    summary = {
        "analysis_timestamp": utc_now(),
        "evaluation_status": "not_evaluated_without_independent_reference_labels",
        "coverage": {
            "expected": len(queue), "completed": len(rows), "remaining": len(queue) - len(rows),
            "unique_completed": len(set(output_ids)),
        },
        "by_protocol": by_protocol,
        "paired_comparison": {
            "expected_pairs": 180,
            "complete_schema_valid_pairs": len(paired),
            "event_presence_agreement": sum(row["event_presence_agrees"] for row in paired),
            "event_presence_agreement_rate": _ratio(sum(row["event_presence_agrees"] for row in paired), len(paired)),
            "content_label_set_agreement": sum(row["content_label_set_agrees"] for row in paired),
            "content_label_set_agreement_rate": _ratio(sum(row["content_label_set_agrees"] for row in paired), len(paired)),
            "temporal_status_agreement": sum(row["temporal_status_agrees"] for row in paired),
            "temporal_status_agreement_rate": _ratio(sum(row["temporal_status_agrees"] for row in paired), len(paired)),
            "answer_effect_agreement": sum(row["answer_effect_agrees"] for row in paired),
            "answer_effect_agreement_rate": _ratio(sum(row["answer_effect_agrees"] for row in paired), len(paired)),
            "interpretation": "agreement is protocol consistency, not classification accuracy",
        },
        "prediction_events": len(events),
        "parse_and_quote_audit_records": len(parse_audit),
        "usage": {
            "prompt_tokens": _usage_total(rows, "prompt_tokens"),
            "completion_tokens": _usage_total(rows, "completion_tokens"),
            "total_tokens": _usage_total(rows, "total_tokens"),
            "reasoning_tokens": _usage_total(rows, "completion_tokens_details", "reasoning_tokens"),
            "known_platform_credit_cost": None,
            "cost_note": "No undocumented conversion from tokens to plan credits is applied.",
        },
        "scheduler": state,
    }
    summary["model_comparison"] = compare_judge_models(root, results, rows, manifest["config"])
    atomic_write_json(results / "analysis_summary.json", summary)
    return summary


def build_chinese_report(root: Path, config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a dynamic Chinese report for complete or interrupted Judge progress."""
    results = results_directory(root, config)
    summary = analyze_tokenplan_judge(root, config)
    manifest = read_json(results / "experiment_manifest.json")
    judge_config = manifest["config"]
    resume = read_json(root / "manifests/resume_audit.json")
    program = read_json(root / "results/program/summary.json")
    diagnostics = read_jsonl(root / "results/program/message_diagnostics.jsonl")
    lines = [
        f"# CBM MAD 漂移诊断：{judge_config['model_name']} Judge 报告", "",
        "## 实验状态", "",
        f"- Qwen 静态协议检查复用：{resume['qwen_protocol']['records']}/108。",
        f"- Qwen MAD 公开发言复用：{resume['qwen_mad']['records']}/1620。",
        f"- 程序状态诊断复用：{program['messages']} 条消息、{program['events']} 个候选级连续错误事件。",
        f"- 本轮 Judge：已完成 {summary['coverage']['completed']}/{summary['coverage']['expected']}，剩余 {summary['coverage']['remaining']}。",
        f"- API 成功 {sum(value['api_success'] for value in summary['by_protocol'].values())}，"
        f"未成功 {summary['coverage']['completed'] - sum(value['api_success'] for value in summary['by_protocol'].values())}；"
        f"解析成功 {sum(value['parse_success'] for value in summary['by_protocol'].values())}，"
        f"schema/引文/对象校验通过 {sum(value['schema_valid'] for value in summary['by_protocol'].values())}。",
        f"- 当前调度状态：`{summary['scheduler'].get('status', 'unknown')}`。",
        ("- 本报告是当前进度的阶段性总结，不代表 1800 次 Judge 已全部完成。"
         if summary["coverage"]["remaining"] else "- 预期 Judge 记录均已落盘；是否成功还须查看 API、解析和引文校验结果。"),
        "- 独立人工参考标签尚未产生，因此检测与内容分类准确率为：**尚未评估**。", "",
        "## Judge 配置", "",
        f"固定使用 Command Code TokenPlan 的 `{judge_config['model_name']}`，"
        f"thinking {judge_config['thinking']['type']}、reasoning effort {judge_config['reasoning_effort']}、"
        f"max_tokens {judge_config['max_tokens']}。未发送 temperature、top_p、惩罚参数或工具；"
        "每条目标发言独立判断。凭证仅从环境变量读取。", "",
        "结构化辅助模式覆盖全部 1620 条有效发言；直接模式仅覆盖预先冻结的 180 条配对样本。配对抽样按 12 个基础题 × 3 个证据版本 × 5 个阶段各取一条，不依据 Qwen 正误或 Judge 输出。", "",
        "## Qwen 与程序诊断", "",
        f"程序结果状态为：{program['outcomes']}。过程状态为：{program['temporal_status']}。这些是答案集合的确定性比较，不是事实/规则/推导内容类别。", "",
        "按证据条件的 Qwen 发言正确率：",
    ]
    service_path = results / "service_check.json"
    if service_path.exists():
        service = read_json(service_path)
        lines[2:2] = [
            "## 服务检查", "",
            f"- 模型目录 HTTP 状态：{service['registry_http_status']}；模型存在：{service['model_in_catalog']}。",
            f"- 检查时运行环境已载入凭证：{service['credential_present']}；认证推理已验证：{service['authenticated_inference_verified']}。",
            "- 模型目录可用不等于额度充足或推理调用成功，须以预检响应为准。", "",
        ]
    for variant in ("clean_stay", "evidence_update", "irrelevant_noise"):
        rows = [row for row in diagnostics if row["variant_type"] == variant]
        correct = sum(row["outcome"] == "valid_correct" for row in rows)
        lines.append(f"- `{variant}`：{correct}/{len(rows)}（{correct / len(rows):.2%}）。")
    lines.extend(["", "## Judge 覆盖与预标注", ""])
    for protocol in ("structured_assistance", "direct"):
        stats = summary["by_protocol"][protocol]
        lines.append(
            f"- `{protocol}`：{stats['completed']}/{stats['expected']}；API 成功 {stats['api_success']}，"
            f"解析成功 {stats['parse_success']}，schema/引文/对象校验通过 {stats['schema_valid']}，截断 {stats['truncated']}。"
        )
        lines.append(f"  内容标签计数：{stats['content_labels']}；过程标签计数：{stats['temporal_status']}。")
        lines.append(f"  成功请求资源统计：{stats['performance']}。")
    paired = summary["paired_comparison"]
    comparison = summary["model_comparison"]
    if comparison["status"] != "not_configured":
        lines.extend([
            "", "## 与既有 Pro 结果的同请求比较", "",
            f"比较状态：`{comparison['status']}`。只匹配相同输入和协议，保留 Pro 的未完成覆盖范围。",
            "```json", json.dumps(comparison, ensure_ascii=False, indent=2), "```",
            "一致率不是准确率；历史 Pro 和本轮 Flash 的服务时间不同，耗时差异不能完全归因于模型。",
        ])
    lines.extend([
        "", "## 配对协议比较", "",
        f"当前有 {paired['complete_schema_valid_pairs']}/180 个可比较的双模式配对。",
        f"事件存在性一致 {paired['event_presence_agreement']}/{paired['complete_schema_valid_pairs']}；"
        f"内容标签集合一致 {paired['content_label_set_agreement']}/{paired['complete_schema_valid_pairs']}；"
        f"过程状态一致 {paired['temporal_status_agreement']}/{paired['complete_schema_valid_pairs']}。",
        "这些数值只描述同一模型在两种输入协议下的一致性，不能称为准确率。", "",
        "## 引文、对象与用量", "",
        f"需要人工审查的解析、引文修复、schema 无效或截断记录共 {summary['parse_and_quote_audit_records']} 条，见 `parse_and_quote_audit.jsonl`。",
        f"平台报告 prompt tokens {summary['usage']['prompt_tokens']}、completion tokens {summary['usage']['completion_tokens']}，其中 reasoning tokens {summary['usage']['reasoning_tokens']}。",
        "平台计划额度的机器可读余额和扣费倍率未由公开 API 提供，因此不将 token 数换算成积分或费用。", "",
        "## 可支持与不可支持的结论", "",
        "程序能够确认当前标准集合、错误加入/排除、违反的事实与规则，以及前后答案状态。Judge 结果仅是模型预测或预标注；没有独立人工标签时，不能报告检测、定位或分类准确率。",
        "同伴消息的可见性、引用和答案趋同可以记录，但不能据此证明从众、遗忘或因果影响。正式证据更正导致的合理答案变化不属于 drift。", "",
        "## 人工标注", "",
        "两名标注者应在不查看 Judge 预测的情况下，分别使用 `annotation/trajectories.html` 和 annotator 模板完成首轮标注，再进入 adjudication。Judge 预测文件必须与盲标材料分开保存。", "",
    ])
    report_path = results / "CBM_DRIFT_DIAGNOSTIC_REPORT_ZH.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return {"report": str(report_path.relative_to(root)), "summary": summary}
