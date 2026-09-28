#!/usr/bin/env python3
"""Audit the interrupted experiment without modifying frozen model outputs."""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cbm_drift_v2.common import read_json, read_jsonl, sha256_file, write_json
from cbm_drift_v2.runner import audit_outputs
from cbm_drift_v2.validation import validate_dataset


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


def main() -> None:
    config = read_json(ROOT / "config/experiment_config.json")
    sequences = read_jsonl(ROOT / "data/evidence_sequences.jsonl")
    protocol_plan = read_jsonl(ROOT / "data/protocol_request_plan.jsonl")
    mad_plan = read_jsonl(ROOT / "data/mad_request_plan.jsonl")
    data_validation = validate_dataset(config, sequences, protocol_plan, mad_plan)
    protocol_audit = audit_outputs(ROOT, "protocol")
    mad_audit = audit_outputs(ROOT, "mad")
    diagnostics = read_jsonl(ROOT / "results/program/message_diagnostics.jsonl")
    program_events = read_jsonl(ROOT / "results/program/program_events.jsonl")
    old_judge = read_jsonl(ROOT / "results/judge/judge_outputs.jsonl")
    old_summary = read_json(ROOT / "results/judge/summary.json")
    annotation = read_json(ROOT / "annotation/manifest.json")

    running = subprocess.run(
        ["bash", "-lc", "ps -ef | rg 'run_judge|cbm_drift_v2|vllm.*811[15]' | rg -v 'rg ' || true"],
        text=True, capture_output=True, check=True,
    ).stdout.strip().splitlines()
    old_ids = [row["judge_request_id"] for row in old_judge]
    audit = {
        "audit_version": "cbm_drift_v2.resume_audit.1",
        "repository": {
            "branch": git("branch", "--show-current"),
            "head": git("rev-parse", "HEAD"),
            "remote": git("remote", "get-url", "origin"),
            "working_tree_status": git("status", "--porcelain=v1").splitlines(),
        },
        "frozen_data": {
            "validated": data_validation["passed"],
            "validation_errors": data_validation["errors"],
            "base_items": data_validation["base_items"],
            "sequences": len(sequences),
            "protocol_requests": len(protocol_plan),
            "mad_requests": len(mad_plan),
            "evidence_sequences_sha256": sha256_file(ROOT / "data/evidence_sequences.jsonl"),
        },
        "qwen_protocol": {
            **{key: value for key, value in protocol_audit.items() if key not in {"missing", "unknown", "duplicates"}},
            "missing": len(protocol_audit["missing"]),
            "unknown": len(protocol_audit["unknown"]),
            "duplicates": len(protocol_audit["duplicates"]),
        },
        "qwen_mad": {
            **{key: value for key, value in mad_audit.items() if key not in {"missing", "unknown", "duplicates"}},
            "missing": len(mad_audit["missing"]),
            "unknown": len(mad_audit["unknown"]),
            "duplicates": len(mad_audit["duplicates"]),
        },
        "program_diagnostics": {
            "messages": len(diagnostics),
            "unique_messages": len({row["message_id"] for row in diagnostics}),
            "events": len(program_events),
            "outcomes": dict(sorted(Counter(row["outcome"] for row in diagnostics).items())),
        },
        "legacy_judge": {
            "directory": "results/judge",
            "records": len(old_judge),
            "unique_requests": len(set(old_ids)),
            "unique_messages": len({row["message_id"] for row in old_judge}),
            "protocols": dict(sorted(Counter(row["judge_protocol"] for row in old_judge).items())),
            "api_failures": sum(not row["api_success"] for row in old_judge),
            "parse_failures": sum(not row["parse_success"] for row in old_judge),
            "schema_invalid": sum(not row["schema_valid"] for row in old_judge),
            "truncated": sum(row.get("finish_reason") == "length" for row in old_judge),
            "stored_summary_is_stale": old_summary.get("completed") != len(old_judge),
            "reuse_decision": "preserved_as_incompatible_exploratory_results",
            "incompatibilities": [
                "legacy provider endpoint was api.deepseek.com rather than Command Code TokenPlan",
                "legacy thinking mode was disabled",
                "legacy max_tokens was 2048 rather than the new preflight value 4096",
                "legacy direct protocol targeted all messages rather than the frozen paired subset",
            ],
        },
        "annotation_package": {
            "trajectories": annotation["trajectories"],
            "judge_predictions_included": annotation["judge_predictions_included"],
            "status": "complete_unlabeled_templates",
        },
        "running_legacy_processes": running,
        "last_interruption": {
            "known_cause": "DeepSeek API quota exhaustion followed by a remote disconnect",
            "legacy_completed_judge_records": len(old_judge),
            "legacy_remaining_under_old_3240_plan": 3240 - len(old_judge),
        },
        "resume_decision": {
            "reuse_qwen_protocol": True,
            "reuse_qwen_mad": True,
            "reuse_program_diagnostics": True,
            "reuse_legacy_judge_as_formal_tokenplan_results": False,
            "new_results_directory": "results/judge_deepseek_v4_pro_v1",
        },
    }
    write_json(ROOT / "manifests/resume_audit.json", audit)
    lines = [
        "# 中断恢复审计", "",
        f"- 分支：`{audit['repository']['branch']}`；起始 HEAD：`{audit['repository']['head']}`。",
        f"- 工作区：整个 `experiments/cbm_drift_diagnostic_v2/` 尚未提交；保留全部现有文件。",
        f"- 冻结数据：{audit['frozen_data']['base_items']} 个基础题、{audit['frozen_data']['sequences']} 条证据序列，验证 {'通过' if audit['frozen_data']['validated'] else '失败'}。",
        f"- Qwen 静态协议：{audit['qwen_protocol']['records']}/108；缺失 {audit['qwen_protocol']['missing']}，重复 {audit['qwen_protocol']['duplicates']}。",
        f"- Qwen MAD：{audit['qwen_mad']['records']}/1620；缺失 {audit['qwen_mad']['missing']}，重复 {audit['qwen_mad']['duplicates']}。",
        f"- 程序诊断：{audit['program_diagnostics']['messages']} 条消息、{audit['program_diagnostics']['events']} 个候选级连续错误事件。",
        f"- 旧 Judge：{audit['legacy_judge']['records']}/3240 条，覆盖 {audit['legacy_judge']['unique_messages']} 条消息；API 失败 {audit['legacy_judge']['api_failures']}，解析失败 {audit['legacy_judge']['parse_failures']}，schema 无效 {audit['legacy_judge']['schema_invalid']}。",
        "- 旧 `summary.json` 只记录 1 条预检，与实际 1,434 条 JSONL 不一致，已标记为陈旧，未作为完成统计使用。",
        "- 旧 Judge 使用不同供应商端点、关闭 thinking、不同输出预算及不同抽样范围，因此保留为探索材料，不混入本轮正式结果。",
        f"- 人工标注包：{audit['annotation_package']['trajectories']} 条完整轨迹，默认隐藏 Judge 预测；尚无独立人工参考标签。",
        f"- 旧运行进程：{'无' if not running else '检测到 ' + str(len(running)) + ' 个'}。",
        "- 上次停止原因：额度耗尽后连接断开；没有发现仍占用队列的调度器。", "",
        "## 恢复范围", "",
        "复用冻结数据、108 条静态协议输出、1620 条 MAD 输出和全部程序诊断。新建 `results/judge_deepseek_v4_pro_v1/`，按本轮 TokenPlan DeepSeek-V4-Pro 协议重新执行 Judge，不覆盖旧结果。",
    ]
    (ROOT / "results/RESUME_AUDIT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
