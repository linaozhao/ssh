"""Deterministic paired analysis and Chinese reporting for CBM-Attr v1."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from cbm_attr_v1.common import read_json, read_jsonl, sha256_json, write_json, write_jsonl


def _rate(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 6) if denominator else None


def _metric_row(section: str, group: str, metric: str, numerator: int, denominator: int) -> dict[str, Any]:
    return {"section": section, "group": group, "metric": metric, "numerator": numerator, "denominator": denominator, "value": _rate(numerator, denominator)}


def build_turn_metrics(outputs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach set-level omission, excess, overlap, and protocol diagnostics."""
    rows: list[dict[str, Any]] = []
    for output in outputs:
        oracle = set(output["oracle"])
        predicted = set(output["predicted_candidates"] or []) if output.get("recognized_answer") else None
        if predicted is None:
            omissions = excess = None
            jaccard = None
        else:
            omissions = sorted(oracle - predicted)
            excess = sorted(predicted - oracle)
            union = oracle | predicted
            jaccard = round(len(oracle & predicted) / len(union), 6) if union else 1.0
        rows.append(
            {
                "request_id": output["request_id"],
                "base_item_id": output["base_item_id"],
                "unit_id": output["unit_id"],
                "run_id": output["run_id"],
                "seed": output["seed"],
                "condition": output["condition"],
                "snapshot_condition": output.get("snapshot_condition"),
                "round_id": output["round_id"],
                "difficulty_cell": output["difficulty_cell"],
                "difficulty_factors": output["difficulty_factors"],
                "scenario": output["scenario"],
                "oracle": sorted(oracle),
                "predicted_candidates": sorted(predicted) if predicted is not None else None,
                "api_success": output.get("api_success", False),
                "blocked": output.get("blocked", False),
                "recognized_answer": output.get("recognized_answer", False),
                "strict_json": output.get("parse", {}).get("strict_json", False),
                "strict_schema": output.get("parse", {}).get("strict_schema", False),
                "parse_source": output.get("parse", {}).get("parse_source"),
                "correct": output.get("correct", False),
                "omitted_oracle_members": omissions,
                "excess_non_oracle_members": excess,
                "jaccard": jaccard,
                "finish_reason": output.get("finish_reason"),
            }
        )
    return rows


def _condition_statistics(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in metrics:
        if row["condition"] == "P_snapshot":
            key = f"P_snapshot:{row['snapshot_condition']}:r{row['round_id']}"
        elif row["condition"] in {"C_clean", "E_noise", "D_update"}:
            key = f"{row['condition']}:r{row['round_id']}"
        else:
            key = row["condition"]
        grouped[key].append(row)
    results: list[dict[str, Any]] = []
    for key, rows in sorted(grouped.items()):
        results.extend(
            [
                _metric_row("condition", key, "overall_exact_accuracy", sum(row["correct"] for row in rows), len(rows)),
                _metric_row("condition", key, "api_success_rate", sum(row["api_success"] for row in rows), len(rows)),
                _metric_row("condition", key, "recognizable_rate", sum(row["recognized_answer"] for row in rows), len(rows)),
                _metric_row("condition", key, "strict_schema_rate", sum(row["strict_schema"] for row in rows), len(rows)),
            ]
        )
        valid = [row for row in rows if row["recognized_answer"]]
        results.append(_metric_row("condition", key, "valid_answer_exact_accuracy", sum(row["correct"] for row in valid), len(valid)))
    return results


def _retention_statistics(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_path: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in metrics:
        if row["condition"] in {"C_clean", "E_noise", "D_update"}:
            by_path[(row["unit_id"], row["condition"])].append(row)
    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for rows in by_path.values():
        rows.sort(key=lambda row: row["round_id"])
        for previous, current in zip(rows, rows[1:]):
            if previous["oracle"] == current["oracle"]:
                pairs.append((previous, current))
    complete = [(previous, current) for previous, current in pairs if previous["recognized_answer"] and current["recognized_answer"]]
    prev_correct = [(previous, current) for previous, current in complete if previous["correct"]]
    prev_wrong = [(previous, current) for previous, current in complete if not previous["correct"]]
    return [
        _metric_row("retention", "all_unchanged_oracle_transitions", "current_error_rate", sum(not current["correct"] for _, current in complete), len(complete)),
        _metric_row("retention", "previous_correct", "correct_to_wrong_rate", sum(not current["correct"] for _, current in prev_correct), len(prev_correct)),
        _metric_row("retention", "previous_wrong", "error_continuation_rate", sum(not current["correct"] for _, current in prev_wrong), len(prev_wrong)),
        _metric_row("retention", "all_unchanged_oracle_transitions", "complete_pair_rate", len(complete), len(pairs)),
    ]


def _noise_statistics(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    index = {(row["unit_id"], row["condition"], row["round_id"]): row for row in metrics}
    pairs = []
    for key, clean in index.items():
        unit, condition, round_id = key
        if condition != "C_clean":
            continue
        noise = index.get((unit, "E_noise", round_id))
        if noise and clean["recognized_answer"] and noise["recognized_answer"]:
            pairs.append((clean, noise))
    results: list[dict[str, Any]] = []
    groups = {"all_round_matched_pairs": pairs}
    groups.update({f"round_{round_id}": [(c, n) for c, n in pairs if c["round_id"] == round_id] for round_id in range(1, 6)})
    for group, group_pairs in groups.items():
        both_correct = sum(clean["correct"] and noise["correct"] for clean, noise in group_pairs)
        clean_only = sum(clean["correct"] and not noise["correct"] for clean, noise in group_pairs)
        noise_only = sum(not clean["correct"] and noise["correct"] for clean, noise in group_pairs)
        both_wrong = sum(not clean["correct"] and not noise["correct"] for clean, noise in group_pairs)
        clean_correct = both_correct + clean_only
        results.extend(
            [
                _metric_row("noise_pair", group, "both_correct", both_correct, len(group_pairs)),
                _metric_row("noise_pair", group, "clean_correct_noise_wrong", clean_only, len(group_pairs)),
                _metric_row("noise_pair", group, "clean_wrong_noise_correct", noise_only, len(group_pairs)),
                _metric_row("noise_pair", group, "both_wrong", both_wrong, len(group_pairs)),
                _metric_row("noise_pair", group, "clean_to_noise_error_conditional", clean_only, clean_correct),
                {"section": "noise_pair", "group": group, "metric": "noise_minus_clean_accuracy", "numerator": sum(noise["correct"] for _, noise in group_pairs) - sum(clean["correct"] for clean, _ in group_pairs), "denominator": len(group_pairs), "value": round(mean([int(noise["correct"]) - int(clean["correct"]) for clean, noise in group_pairs]), 6) if group_pairs else None},
            ]
        )
    return results


def _snapshot_statistics(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    dynamic = {
        (row["unit_id"], row["condition"], row["round_id"]): row
        for row in metrics
        if row["condition"] in {"C_clean", "E_noise", "D_update"}
    }
    snapshots = [row for row in metrics if row["condition"] == "P_snapshot"]
    grouped: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = defaultdict(list)
    for snapshot in snapshots:
        counterpart = dynamic.get((snapshot["unit_id"], snapshot["snapshot_condition"], snapshot["round_id"]))
        if counterpart and counterpart["recognized_answer"] and snapshot["recognized_answer"]:
            grouped[f"{snapshot['snapshot_condition']}:r{snapshot['round_id']}"] .append((counterpart, snapshot))
            grouped["all_matched_rounds"].append((counterpart, snapshot))
    rows: list[dict[str, Any]] = []
    for group, pairs in sorted(grouped.items()):
        rows.extend(
            [
                _metric_row("dynamic_snapshot", group, "dynamic_accuracy", sum(dynamic_row["correct"] for dynamic_row, _ in pairs), len(pairs)),
                _metric_row("dynamic_snapshot", group, "snapshot_accuracy", sum(snapshot["correct"] for _, snapshot in pairs), len(pairs)),
                _metric_row("dynamic_snapshot", group, "snapshot_correct_dynamic_wrong", sum(snapshot["correct"] and not dynamic_row["correct"] for dynamic_row, snapshot in pairs), len(pairs)),
                _metric_row("dynamic_snapshot", group, "dynamic_correct_snapshot_wrong", sum(dynamic_row["correct"] and not snapshot["correct"] for dynamic_row, snapshot in pairs), len(pairs)),
            ]
        )
    return rows


def _update_statistics(metrics: list[dict[str, Any]], episodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    update_meta = {episode["base_item_id"]: episode["update"] for episode in episodes}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in metrics:
        if row["condition"] == "D_update" and row["recognized_answer"]:
            size = update_meta[row["base_item_id"]]["correction_size"]
            grouped[f"correction_size_{size}:r{row['round_id']}"] .append(row)
            grouped[f"all:r{row['round_id']}"] .append(row)
    results: list[dict[str, Any]] = []
    for group, rows in sorted(grouped.items()):
        restored = 0
        old_set = 0
        gold_excluded = 0
        unrelated_extra = 0
        for row in rows:
            meta = update_meta[row["base_item_id"]]
            prediction = set(row["predicted_candidates"] or [])
            restored += meta["target_candidate"] in prediction
            old_set += prediction == {next(label for label in row["oracle"] if label != meta["target_candidate"])}
            gold = next(label for label in row["oracle"] if label != meta["target_candidate"])
            gold_excluded += gold not in prediction
            unrelated_extra += bool(prediction - set(row["oracle"]))
        results.extend(
            [
                _metric_row("update", group, "exact_accuracy", sum(row["correct"] for row in rows), len(rows)),
                _metric_row("update", group, "target_candidate_restored", restored, len(rows)),
                _metric_row("update", group, "old_set_persistence", old_set, len(rows)),
                _metric_row("update", group, "gold_erroneously_excluded", gold_excluded, len(rows)),
                _metric_row("update", group, "unrelated_candidate_restored", unrelated_extra, len(rows)),
            ]
        )
    return results


def _set_error_statistics(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    valid_sets = [row for row in metrics if row["recognized_answer"] and row["condition"] != "A_original"]
    wrong = [row for row in valid_sets if not row["correct"]]
    omission_errors = sum(bool(row["omitted_oracle_members"]) for row in wrong)
    excess_errors = sum(bool(row["excess_non_oracle_members"]) for row in wrong)
    return [
        _metric_row("set_errors", "valid_incorrect_sets", "contains_omission", omission_errors, len(wrong)),
        _metric_row("set_errors", "valid_incorrect_sets", "contains_excess", excess_errors, len(wrong)),
        {"section": "set_errors", "group": "valid_candidate_sets", "metric": "mean_jaccard", "numerator": None, "denominator": len(valid_sets), "value": round(mean(row["jaccard"] for row in valid_sets), 6) if valid_sets else None},
    ]


def analyze(root: Path) -> dict[str, Any]:
    """Generate all required machine-readable and human-readable analysis outputs."""
    outputs = read_jsonl(root / "results/raw_outputs.jsonl")
    plan = read_jsonl(root / "data/request_plan.jsonl")
    episodes = read_jsonl(root / "data/episodes.jsonl")
    metrics = build_turn_metrics(outputs)
    write_jsonl(root / "results/turn_metrics.jsonl", metrics)
    statistics = (
        _condition_statistics(metrics)
        + _set_error_statistics(metrics)
        + _retention_statistics(metrics)
        + _update_statistics(metrics, episodes)
        + _noise_statistics(metrics)
        + _snapshot_statistics(metrics)
        + _cell_statistics(metrics)
        + _repeat_stability(metrics)
    )
    with (root / "results/paired_statistics.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("section", "group", "metric", "numerator", "denominator", "value"),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(statistics)
    parse_audit = [
        {
            "request_id": row["request_id"],
            "condition": row["condition"],
            "round_id": row["round_id"],
            "api_success": row.get("api_success"),
            "blocked": row.get("blocked"),
            "finish_reason": row.get("finish_reason"),
            "parse": row.get("parse"),
            "raw_response": row.get("raw_response"),
        }
        for row in outputs
        if row.get("finish_reason") == "length"
        or not row.get("recognized_answer")
        or not row.get("parse", {}).get("strict_schema", False)
    ]
    write_jsonl(root / "results/parse_audit.jsonl", parse_audit)
    summary = _summary(outputs, plan, metrics, statistics)
    summary["discarded_protocol_records"] = sum(
        len(read_jsonl(path))
        for directory in (root / "results").glob("protocol_*_discarded")
        for path in directory.glob("*.jsonl")
        if path.name == "raw_outputs.jsonl" or path.name.startswith("interrupted_tail")
    )
    write_json(root / "results/analysis_summary.json", summary)
    runtime_integrity = _runtime_integrity(outputs)
    write_json(root / "results/runtime_integrity.json", runtime_integrity)
    anchor_audit = _format_anchor_audit(metrics)
    write_json(root / "results/format_anchor_audit.json", anchor_audit)
    _write_report(root, summary, statistics, episodes, runtime_integrity, anchor_audit)
    _write_examples(root, episodes)
    return summary


def _runtime_integrity(outputs: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {row["request_id"]: row for row in outputs}
    d4_rows = [row for row in outputs if row["condition"] == "D_update" and row["round_id"] == 4]
    prefix_matches = 0
    missing_parents = 0
    for row in d4_rows:
        parent = by_id.get(f"{row['unit_id']}:C_clean:r3")
        if not parent or not parent.get("api_success"):
            missing_parents += 1
            continue
        expected = list(parent["messages"]) + [{"role": "assistant", "content": parent["raw_response"]}]
        prefix_matches += row.get("messages", [])[:-1] == expected
    banned = (
        "C_clean",
        "E_noise",
        "D_update",
        "source_gold",
        "gold_answer",
        "oracle",
        "violation_signature",
        "option_violation_signature",
        "difficulty_cell",
    )
    leak_counts: Counter[str] = Counter()
    hash_mismatches = 0
    for row in outputs:
        messages = row.get("messages")
        if not messages:
            continue
        if sha256_json(messages) != row.get("messages_sha256"):
            hash_mismatches += 1
        user_input = "\n".join(message["content"] for message in messages if message["role"] != "assistant")
        for token in banned:
            if token in user_input:
                leak_counts[token] += 1
    return {
        "d_update_round4_records": len(d4_rows),
        "actual_shared_prefix_matches": prefix_matches,
        "missing_or_failed_parent_prefixes": missing_parents,
        "message_hash_mismatches": hash_mismatches,
        "banned_input_token_counts": dict(leak_counts),
        "passed": prefix_matches == len(d4_rows) and not missing_parents and not hash_mismatches and not leak_counts,
    }


def _format_anchor_audit(metrics: list[dict[str, Any]]) -> dict[str, Any]:
    """Measure exact reuse of the concrete A/C set shown in the output example."""
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in metrics:
        if row["condition"] == "A_original" or not row["recognized_answer"]:
            continue
        groups[row["condition"]].append(row)
        groups["all_set_protocol"].append(row)
    result: dict[str, Any] = {
        "format_example_set": ["A", "C"],
        "interpretation": "descriptive prompt-anchor diagnostic, not proof of an internal mechanism",
        "groups": {},
    }
    for group, rows in sorted(groups.items()):
        count = sum(row["predicted_candidates"] == ["A", "C"] for row in rows)
        result["groups"][group] = {
            "exact_format_example_predictions": count,
            "recognizable_set_predictions": len(rows),
            "rate": _rate(count, len(rows)),
        }
    return result


def _summary(outputs: list[dict[str, Any]], plan: list[dict[str, Any]], metrics: list[dict[str, Any]], statistics: list[dict[str, Any]]) -> dict[str, Any]:
    output_ids = [row["request_id"] for row in outputs]
    known = {row["request_id"] for row in plan}
    complete_units = Counter(row["unit_id"] for row in outputs)
    complete_base_runs = {unit for unit, count in complete_units.items() if count == 26}
    complete_bases: Counter[str] = Counter(unit.rsplit(":run", 1)[0] for unit in complete_base_runs)
    return {
        "expected_requests": len(plan),
        "actual_records": len(outputs),
        "unique_records": len(set(output_ids)),
        "missing_requests": len(known - set(output_ids)),
        "unknown_requests": len(set(output_ids) - known),
        "duplicate_records": len(output_ids) - len(set(output_ids)),
        "api_failures": sum(not row.get("api_success", False) and not row.get("blocked", False) for row in outputs),
        "blocked": sum(row.get("blocked", False) for row in outputs),
        "recognized_answers": sum(row.get("recognized_answer", False) for row in outputs),
        "strict_schema": sum(row.get("parse", {}).get("strict_schema", False) for row in outputs),
        "truncated": sum(row.get("finish_reason") == "length" for row in outputs),
        "complete_item_runs": sum(count == 26 for count in complete_units.values()),
        "complete_base_items_three_runs": sum(count == 3 for count in complete_bases.values()),
        "expected_item_runs": 72 * 3,
        "http_attempts_including_retries": sum(row.get("request_attempts", 0) for row in outputs),
        "retry_attempts": sum(max(0, row.get("request_attempts", 0) - 1) for row in outputs),
        "preflight_reused_records": sum(row.get("phase_first_executed") == "preflight" for row in outputs),
        "statistics_rows": len(statistics),
    }


def _cell_statistics(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Provide exploratory cell summaries for key comparable states."""
    states = {
        "A_original": lambda row: row["condition"] == "A_original",
        "B_source_set": lambda row: row["condition"] == "B_source_set",
        "C_clean_r3": lambda row: row["condition"] == "C_clean" and row["round_id"] == 3,
        "E_noise_r3": lambda row: row["condition"] == "E_noise" and row["round_id"] == 3,
        "D_update_r4": lambda row: row["condition"] == "D_update" and row["round_id"] == 4,
    }
    results: list[dict[str, Any]] = []
    for state, predicate in states.items():
        by_cell: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in metrics:
            if predicate(row):
                by_cell[row["difficulty_cell"]].append(row)
        for cell, rows in sorted(by_cell.items()):
            results.append(_metric_row("cell_exploratory", f"{state}:{cell}", "overall_exact_accuracy", sum(row["correct"] for row in rows), len(rows)))
    return results


def _repeat_stability(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Summarize three-run observations at the base-item unit."""
    key_states = {
        "A_original": lambda row: row["condition"] == "A_original",
        "B_source_set": lambda row: row["condition"] == "B_source_set",
        **{
            f"{condition}_r{round_id}": (
                lambda row, condition=condition, round_id=round_id: row["condition"] == condition and row["round_id"] == round_id
            )
            for condition, round_ids in (("C_clean", (3, 4, 5)), ("E_noise", (3, 4, 5)), ("D_update", (4, 5)))
            for round_id in round_ids
        },
    }
    results: list[dict[str, Any]] = []
    for state, predicate in key_states.items():
        by_base: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in metrics:
            if predicate(row):
                by_base[row["base_item_id"]].append(row)
        complete = [rows for rows in by_base.values() if len(rows) == 3 and all(row["recognized_answer"] for row in rows)]
        all_correct = sum(all(row["correct"] for row in rows) for rows in complete)
        all_wrong = sum(all(not row["correct"] for row in rows) for rows in complete)
        mixed = sum(any(row["correct"] for row in rows) and not all(row["correct"] for row in rows) for rows in complete)
        results.extend(
            [
                _metric_row("repeat_stability", state, "three_runs_all_correct", all_correct, len(complete)),
                _metric_row("repeat_stability", state, "three_runs_all_wrong", all_wrong, len(complete)),
                _metric_row("repeat_stability", state, "three_runs_mixed", mixed, len(complete)),
                _metric_row("repeat_stability", state, "complete_three_run_items", len(complete), len(by_base)),
            ]
        )
    return results


def _lookup(stats: list[dict[str, Any]], section: str, group: str, metric: str) -> dict[str, Any]:
    return next(row for row in stats if row["section"] == section and row["group"] == group and row["metric"] == metric)


def _pct(row: dict[str, Any]) -> str:
    return "N/A" if row["value"] is None else f"{100 * row['value']:.2f}% ({row['numerator']}/{row['denominator']})"


def _write_report(
    root: Path,
    summary: dict[str, Any],
    stats: list[dict[str, Any]],
    episodes: list[dict[str, Any]],
    runtime_integrity: dict[str, Any],
    anchor_audit: dict[str, Any],
) -> None:
    manifest = read_json(root / "results/experiment_manifest.json")
    config = manifest["config"]
    model = config["model"]
    generation = config["generation"]
    def cond(group: str) -> dict[str, Any]:
        return _lookup(stats, "condition", group, "overall_exact_accuracy")
    retention = _lookup(stats, "retention", "previous_correct", "correct_to_wrong_rate")
    update4 = _lookup(stats, "update", "all:r4", "exact_accuracy")
    update5 = _lookup(stats, "update", "all:r5", "exact_accuracy")
    noise = _lookup(stats, "noise_pair", "all_round_matched_pairs", "noise_minus_clean_accuracy")
    clean_noise = _lookup(stats, "noise_pair", "all_round_matched_pairs", "clean_correct_noise_wrong")
    noise_clean = _lookup(stats, "noise_pair", "all_round_matched_pairs", "clean_wrong_noise_correct")
    noise_conditional = _lookup(stats, "noise_pair", "all_round_matched_pairs", "clean_to_noise_error_conditional")
    omission = _lookup(stats, "set_errors", "valid_incorrect_sets", "contains_omission")
    excess = _lookup(stats, "set_errors", "valid_incorrect_sets", "contains_excess")
    mean_jaccard = _lookup(stats, "set_errors", "valid_candidate_sets", "mean_jaccard")
    restored = _lookup(stats, "update", "all:r4", "target_candidate_restored")
    old_set = _lookup(stats, "update", "all:r4", "old_set_persistence")
    snapshot_dynamic = _lookup(stats, "dynamic_snapshot", "all_matched_rounds", "dynamic_accuracy")
    snapshot_static = _lookup(stats, "dynamic_snapshot", "all_matched_rounds", "snapshot_accuracy")
    snapshot_only = _lookup(stats, "dynamic_snapshot", "all_matched_rounds", "snapshot_correct_dynamic_wrong")
    dynamic_only = _lookup(stats, "dynamic_snapshot", "all_matched_rounds", "dynamic_correct_snapshot_wrong")
    stable_wrong_b = _lookup(stats, "repeat_stability", "B_source_set", "three_runs_all_wrong")
    stable_wrong_c3 = _lookup(stats, "repeat_stability", "C_clean_r3", "three_runs_all_wrong")
    mixed_c3 = _lookup(stats, "repeat_stability", "C_clean_r3", "three_runs_mixed")
    snap_groups = [row for row in stats if row["section"] == "dynamic_snapshot" and row["metric"] in {"dynamic_accuracy", "snapshot_accuracy"}]
    complete = summary["actual_records"] == summary["expected_requests"] and not summary["missing_requests"]
    report = f"""# CBM-Attr v1 Qwen3-8B 配对评测报告

## 实验定位

本实验借鉴 [Contextual Belief Management](https://arxiv.org/abs/2605.30219) 中逐轮正式证据、保持、更新和隔离的测量思想，但任务仍是本项目的布尔属性筛选。它是 **CBM-inspired 属性筛选改造版**，不是 BeliefTrack 规则发现或电路诊断任务的复现，也未运行论文中的 RL、steering 或 probing。

模型每轮输出“按当前有效证据尚未被排除的候选集合”。未观察属性保持 unknown；unknown 既不是 false，也不表示已满足。标准状态由程序只使用当轮 active evidence 计算，并由枚举实现交叉核对。

## 冻结配置

- 模型：`{model['model_name']}`；thinking=`{str(model['thinking_enabled']).lower()}`；temperature={generation['temperature']}；top_p={generation['top_p']}；max_tokens={generation['max_tokens']}；seeds={config['seeds']}。
- 服务：`{model['deployment']['service_framework']} {model['deployment']['service_version']}`；dtype=`{model['deployment']['dtype']}`；quantization=`{model['deployment']['quantization']}`；权重 revision=`{model['deployment']['revision']}`。
- 请求未显式设置 top_k；本轮服务启动日志声明采用模型 generation config 的默认 top_k=20。该值作为后端运行信息报告，不伪装成请求字段。
- 数据、配置、提示词和解析器指纹见 `results/experiment_manifest.json`；原始记录逐条保存实际 messages 和 message hash。
- D_update 实际共享前缀匹配：{runtime_integrity['actual_shared_prefix_matches']}/{runtime_integrity['d_update_round4_records']}；message hash 不匹配：{runtime_integrity['message_hash_mismatches']}；禁用输入标签计数：`{runtime_integrity['banned_input_token_counts']}`。

## 流程完整性

- 计划逻辑请求：{summary['expected_requests']}；落盘记录：{summary['actual_records']}；唯一记录：{summary['unique_records']}。
- 缺失：{summary['missing_requests']}；未知：{summary['unknown_requests']}；重复：{summary['duplicate_records']}。
- API 失败：{summary['api_failures']}；依赖阻塞：{summary['blocked']}；截断：{summary['truncated']}。
- 实际 HTTP 尝试（含重试）：{summary['http_attempts_including_retries']}；额外重试：{summary['retry_attempts']}；正式复用协议一致的预检记录：{summary['preflight_reused_records']}。
- 可识别答案：{summary['recognized_answers']}/{summary['actual_records']}；严格 schema：{summary['strict_schema']}/{summary['actual_records']}。
- 完整 26 请求的题目×重复：{summary['complete_item_runs']}/{summary['expected_item_runs']}。
- 三次重复均完整的基础题：{summary['complete_base_items_three_runs']}/72。
- 数据与流程状态：{'完成' if complete else '未完整完成'}。
- 另有 {summary['discarded_protocol_records']} 条协议审计阶段响应被隔离，不属于 5616 条正式记录，未进入任何效果统计。

## 静态与最终状态

- A_original 单选：{_pct(cond('A_original'))}。
- B_source_set 一次性集合：{_pct(cond('B_source_set'))}。
- C_clean 完整信息 r3：{_pct(cond('C_clean:r3'))}；稳定 r4/r5：{_pct(cond('C_clean:r4'))} / {_pct(cond('C_clean:r5'))}。
- E_noise 完整信息 r3：{_pct(cond('E_noise:r3'))}；稳定 r4/r5：{_pct(cond('E_noise:r4'))} / {_pct(cond('E_noise:r5'))}。
- D_update 更正 r4 / 后续 r5：{_pct(update4)} / {_pct(update5)}。
- 以基础题为单位的三次观测：B_source_set 三次全错 {_pct(stable_wrong_b)}；C_clean r3 三次全错 {_pct(stable_wrong_c3)}、正误混合 {_pct(mixed_c3)}。这里的“三次全错”只描述本配置下的观测，不证明题目永久困难。

## 保持与集合错误

- 在前一轮集合正确且 oracle 不变的有效转移中，下一轮变错：{_pct(retention)}。持续错误另行计数，不把它们称为“从正确状态漂移”。
- 有效错误集合中包含错误省略：{_pct(omission)}；包含错误保留：{_pct(excess)}。二者可同时发生。
- 所有有效集合的平均 Jaccard：{mean_jaccard['value']}（分母 {mean_jaccard['denominator']}）。因此成员级错误可由程序定位；解析失败不进入成员错误分析，但在整体准确率中按未答对保留。

## 非目标信息配对

- 所有同题同轮配对的 E_noise - C_clean 准确率差：{noise['value']}，分母 {noise['denominator']}。
- clean 正确/noise 错误：{_pct(clean_noise)}；clean 错误/noise 正确：{_pct(noise_clean)}；在 clean 正确配对中的条件破坏率：{_pct(noise_conditional)}。
- 这是同一正式证据、同一顺序和同一重述下的配对比较。`source_IL` 仅是原题标签，C/E 的实际噪声条件由本实验版本决定。

## 更正与恢复

- r4 更正把一个错误候选人的全部违反属性替换为满足值，预期集合从 {{Gold}} 扩张为 {{Gold, W}}；r5 只重述当前有效事实。
- r4 正确恢复 W：{_pct(restored)}；仍输出更正前单元素集合：{_pct(old_set)}。
- 本轮只覆盖“撤销排除依据并恢复候选人”的集合扩张，不代表全部更新操作。
- correction_size 分组、旧集合持续、W 恢复、Gold 错误排除及额外候选恢复均见 `paired_statistics.csv`。

## 动态与快照

- 共生成 {len(episodes) * 12} 个独立快照；逐轮动态/快照指标行数为 {len(snap_groups)}。
- 所有可识别配对中，动态准确率 {_pct(snapshot_dynamic)}，快照准确率 {_pct(snapshot_static)}；快照对/动态错 {_pct(snapshot_only)}，动态对/快照错 {_pct(dynamic_only)}。
- 快照不含先前模型回答。动态与快照差异同时包含对话组织、历史响应和信息呈现差异；D_update 还包含处理显式更正记录的负担，不能直接等同于某种内部记忆机制。

## 输出示例锚定审计

- 集合协议的格式示例使用了具体集合 `["A", "C"]`。B_source_set 有 {anchor_audit['groups']['B_source_set']['exact_format_example_predictions']}/{anchor_audit['groups']['B_source_set']['recognizable_set_predictions']} 次原样输出该集合，P_snapshot 有 {anchor_audit['groups']['P_snapshot']['exact_format_example_predictions']}/{anchor_audit['groups']['P_snapshot']['recognizable_set_predictions']} 次。
- C_clean、E_noise、D_update 的对应次数分别为 {anchor_audit['groups']['C_clean']['exact_format_example_predictions']}/{anchor_audit['groups']['C_clean']['recognizable_set_predictions']}、{anchor_audit['groups']['E_noise']['exact_format_example_predictions']}/{anchor_audit['groups']['E_noise']['recognizable_set_predictions']}、{anchor_audit['groups']['D_update']['exact_format_example_predictions']}/{anchor_audit['groups']['D_update']['recognizable_set_predictions']}。
- 这是强烈的描述性 prompt-anchor 信号，但不证明模型内部机制。它尤其污染一次性集合和静态快照，因此不能把 B 或 P 的低准确率、以及动态高于快照的差值直接解释为 CBM 能力差异。

## 结论边界

- 每个 CL×DS×IL cell 仅 4 道基础题，统计是探索性描述，不强行划分 Easy/Medium/Hard。
- 三次采样及多轮响应不是独立题目；推断单位应保持为 72 道基础题。
- 本轮没有多智能体交互，因此任何单智能体集合错误都不称为 MAD drift。
- 是否值得接入 MAD 应同时参考动态相对快照、保持破坏、更新恢复和 noise 配对；若差异很小，也应保留为“当前证据不足”，而不是继续调数据直到模型出错。
- 若集合错误能够由 oracle 的遗漏/额外成员稳定定位，本任务值得作为未来 MAD 前的状态跟踪基线；是否真正接入 MAD 仍应依据本报告的配对差异和更新成功率，而不是只看总体错误率。
- 本轮结论：动态数据结构、oracle 和配对框架值得保留，但当前集合 prompt **不应直接接入 MAD 或继续扩样**。下一步应预注册一个只改变格式示例的协议消融（例如使用抽象占位符或不提供具体标签组合），在同一 72 题上确认 B/P 的 A-C 锚定消失后，再判断真实 stay/update/isolation 难度。不得按题目对错筛选重跑。

## 协议审计

首次预检发现内部条件名进入动态标题，相关响应已完整隔离在 `results/protocol_v0_discarded/`；v1.1 随后因 A_original 未完全沿用旧三字段协议而隔离。两批均未进入上述统计。正式 prompt v1.2 使用统一中性动态标题、保留原始 A 协议，并扫描确认未向模型发送 Gold、oracle、违反集合、难度 cell 或内部条件标签。
"""
    path = root / "reports/CBM_ATTR_V1_REPORT.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report, encoding="utf-8")


def _write_examples(root: Path, episodes: list[dict[str, Any]]) -> None:
    selected: list[dict[str, Any]] = []
    seen_cl: set[str] = set()
    seen_ds: set[str] = set()
    seen_seq: set[str] = set()
    for episode in episodes:
        cl = episode["difficulty_factors"]["constraint_load"]
        ds = episode["difficulty_factors"]["distractor_similarity"]
        seq = "-".join(str(len(row["oracle"])) for row in episode["clean"]["rounds"])
        if cl not in seen_cl or ds not in seen_ds or seq not in seen_seq:
            selected.append(episode)
            seen_cl.add(cl)
            seen_ds.add(ds)
            seen_seq.add(seq)
        if len(selected) >= 6 and len(seen_cl) == 3 and len(seen_ds) == 3:
            break
    lines = ["# CBM-Attr v1 Dataset Examples", "", "Programmatically selected examples; no human annotation is claimed.", ""]
    for episode in selected:
        lines.extend(
            [
                f"## {episode['source_item_id']}",
                "",
                f"- Cell: `{episode['difficulty_cell']}`",
                f"- Scenario: `{episode['scenario']}`",
                f"- Gold: `{episode['source_gold']}`",
                f"- Clean oracle sizes: `{' -> '.join(str(len(row['oracle'])) for row in episode['clean']['rounds'])}`",
                f"- Update target: `{episode['update']['target_candidate']}`; correction size: `{episode['update']['correction_size']}`",
                "",
                "### Requirements",
                "",
                *[f"- {row['natural_language']}" for row in episode["constraints"]],
                "",
                "### Clean rounds",
                "",
            ]
        )
        for row in episode["clean"]["rounds"]:
            lines.append(f"- R{row['round_id']} oracle `{row['oracle']}`: " + " | ".join(event["text"] for event in row["events"]))
        lines.extend(["", "### Correction", ""])
        for event in episode["update"]["rounds"][0]["events"]:
            lines.append(f"- Replace `{event['replaces_evidence_id']}` with: {event['text']}")
        lines.append("")
    (root / "reports/dataset_examples.md").write_text(
        "\n".join(lines).rstrip() + "\n", encoding="utf-8"
    )
