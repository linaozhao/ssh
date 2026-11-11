"""Status-first report; never turn missing calls or software mocks into findings."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import atomic_text, read_json, read_jsonl, write_json
from .judge import credential_gate


def build_report(root: Path, config: dict[str, Any], judge_config: dict[str, Any], *, judge_results_subdir: str | None = None) -> dict[str, Any]:
    """Report A/B/C independently with explicit missing denominators."""
    result = root / "results" / config["run_id"]
    data_dir = root / config.get("data_subdir", "data")
    judge_dir = result / (judge_results_subdir or judge_config.get("results_subdir", "controlled_judge"))
    def optional(path: Path, default: Any) -> Any:
        return read_json(path) if path.exists() else default
    data = optional(data_dir / "validation_report.json", {"status": "pending"})
    reference = optional(root / "data/controlled/reference_validation.json", {"status": "pending", "built": 0, "verified": 0})
    tests = optional(result / "software_validation.json", {"status": "not_run"})
    runtime = optional(result / "runtime_manifest.json", {"status": "not_checked"})
    shutdown = optional(result / "service_shutdown.json", {"status": "not_recorded"})
    mad = optional(result / "mad/status.json", {"status": "not_run", "planned": 1188, "attempted": 0, "api_success": 0, "parsed": 0, "failed": 0, "blocked": 0})
    protocol = optional(result / "protocol/status.json", {"status": "not_run", "planned": 108, "api_success": 0})
    for stage, saved in (("mad", mad), ("protocol", protocol)):
        rows = [read_json(p) for p in (result / stage / "records").glob("*.json")]
        if len(rows) > saved.get("api_success", 0) + saved.get("failed", 0):
            attempts_path = result / stage / "attempts.jsonl"
            attempts = read_jsonl(attempts_path) if attempts_path.exists() else []
            saved.update(status="partial", api_success=sum(r.get("api_success", False) for r in rows),
                         attempted=len({r["request_id"] for r in attempts}),
                         parsed=sum(r.get("parsed", {}).get("recognized", False) for r in rows),
                         failed=sum(not r.get("api_success", False) for r in rows),
                         status_note="Persisted records; process liveness is not inferred.")
    if mad.get("status") == "completed" and mad.get("planned", 0) < 1188:
        mad.update(status="partial", status_note="Only the 198-request preflight subset has completed.")
    judge = optional(judge_dir / "status.json", optional(judge_dir / "credential_gate.json", credential_gate(judge_config, enabled=False)))
    judge_rows = read_jsonl(judge_dir / "outputs.jsonl") if (judge_dir / "outputs.jsonl").exists() else []
    if len(judge_rows) > judge.get("terminal_requests", 0):
        attempts_file = judge_dir / "attempts.jsonl"
        judge.update(status="partial", terminal_requests=len(judge_rows),
                     successful_outputs=sum(r.get("status") == "success" for r in judge_rows),
                     formal_attempts=len(read_jsonl(attempts_file)) if attempts_file.exists() else 0)
    evaluation = optional(judge_dir / "evaluation.json", {"status": "not_evaluated"})
    annotation = optional(root / config.get("annotation_subdir", "annotation/deferred_real") / "status.json", {"status": "pending", "available_messages": 0})
    source = optional(result / "source_preservation_validation.json", {"status": "pending"})
    queue_path = judge_dir / "request_queue.jsonl"
    queue_count = len(read_jsonl(queue_path)) if queue_path.exists() else 0
    states = {"run_id": config["run_id"], "software_validation": tests,
              "data_validation": data, "source_preservation": source,
              "controlled_reference_validation": reference, "controlled_judge": judge,
              "controlled_evaluation": evaluation, "mad_generation": mad, "protocol_generation": protocol,
              "runtime": runtime, "service_shutdown": shutdown, "real_annotation": {"status": "deferred", "materials": annotation},
              "real_diagnostic_evaluation": {"status": "not_evaluated"}}
    write_json(result / "run_status.json", states)
    def metric(value: Any) -> str:
        return "尚未评估/不适用" if value is None else f"{value:.4f}"
    scores = "尚未评估。"
    if evaluation.get("splits"):
        score_lines = ["| 分组 | 协议 | 已收/应收 | 检测F1 | 消息分类macro-F1 | 严格claim定位F1 | 时间分类正确/适用 |",
                       "| --- | --- | --- | --- | --- | --- | --- |"]
        for split in ("dev", "holdout"):
            for mode in ("direct", "structured"):
                s = evaluation["splits"][split][mode]
                score_lines.append(f"| {split} | {mode} | {s['coverage']['outputs_received']}/{s['reference_count']} | "
                                   f"{metric(s['current_deviation']['f1'])} | {metric(s['classification_message']['macro_f1'])} | "
                                   f"{metric(s['claim_events']['strict_localization']['f1'])} | "
                                   f"{s['temporal']['correct']}/{s['temporal']['support']} |")
        scores = "\n".join(score_lines)
    program = optional(result / "program/summary.json", {"status": "not_evaluated"})
    program_counts = program.get("answer_status_counts", {})
    context = optional(result / "context_validation.json", {"status": "not_evaluated"})
    technical_valid = sum(all(r.get(k) for k in ("api_success", "schema_valid", "quote_valid", "object_valid"))
                          and r.get("finish_reason") != "length" for r in judge_rows)
    token_total = sum((r.get("usage") or {}).get("total_tokens", 0) for r in judge_rows) if judge_rows else None
    next_steps = ("本轮MAD和受控Judge均已完整收齐，不再追加推理。完成后的run只读保留；"
                  "源代码兼容修复已改变指纹，后续模型实验使用新run_id。\n\n"
                  "下一阶段仍需132条真实消息的独立双人标注与仲裁，之后才考虑真实诊断评估。"
                  "优先复核严格claim定位的低分来自哪些对象/跨度/证据不一致，不据已查看的留出结果改写本轮评分标准。"
                  if mad.get("api_success") == 1188 and judge.get("terminal_requests") == 144 else
                  "未完成的MAD仅在本轮授权GPU与冻结执行源码下续跑；先108静态预检、198新MAD预检，再其余990。\n\n"
                  "未完成的受控Judge由隐藏输入注入新凭证，预检12计入144，先dev再holdout。"
                  "认证/额度失败停止；配置变化需新冻结版本。真实标注和正式真实Judge继续暂缓。")
    text = f"""# MAD 漂移诊断 v3 R2 本轮运行总结

计划：controlled-first-r2。run_id：`{config['run_id']}`。
实际分支：`feature/cbm-drift-shared-prefix-v3`。只读基线：`{config['source_sha']}`。
本报告由本轮产物生成；文件存在、程序测试通过不代表在线实验完成。

## A. 本轮必须完成事项

| 事项 | 实际状态 / 数量 |
| --- | --- |
| 原有题目、选题记录、旧代码和旧结果字节保护 | {source['status']} |
| 四条件证据、状态、共享请求图 | {data['status']}；48序列 / 1188唯一请求 / 2160引用 |
| 软件验证 | {tests['status']}；通过 {tests.get('passed', '尚未统计')} 项；详见 software_validation.json |
| 受控样例 | 已构造 {reference['built']}；程序核验 {reference['verified']}；人工核验 0 |
| 静态协议预检 | {protocol['status']}；API成功 {protocol.get('api_success', 0)}/108 |
| 新MAD生成 | {mad['status']}；尝试 {mad.get('attempted', 0)}/1188；API成功 {mad.get('api_success', 0)}；可解析 {mad.get('parsed', 0)} |
| MAD失败 / 阻塞 | {mad.get('failed', 0)} / {mad.get('blocked', 0)}；未尝试不是请求失败 |
| 受控Judge队列 | 已准备 {queue_count}/144，未混入真实轨迹队列 |
| 真实待标注材料 | 计划132目标；已有真实文本 {annotation.get('available_messages', 0)}；不足部分明确标未生成 |

本轮GPU政策：物理编号{config['gpu']['physical_gpu_index']}、UUID `{config['gpu']['expected_uuid']}`；
共用授权：{config['gpu'].get('allow_shared_gpu', False)}，保留其他用户进程与显存安全余量。
启动时核验状态：`{runtime['status']}`；当前本实验服务关闭状态：`{shutdown['status']}`。
不换卡、不停止其他用户进程、不使用旧MAD补齐1188。本次没有GPU成功运行时，MAD部分仍是阻塞，A不能整体宣称完成。

程序实现包括：证据重放；unknown/known_satisfied/known_violated；候选多选集合评分；
把上一答案按新状态重评分；对象级变化代理；共享前史和四分支隔离；严格输入指纹；
合法原始格式错误可继续进入后续历史，但不重采样到正确。执行器当前逐请求串行，
低于最多3并发的授权上限，不影响依赖语义。

程序分析状态：`{program['status']}`；唯一消息答案状态：`{program_counts}`。
这些只是按当前有效证据计算的集合正确性，不是F/R/I类别或同伴因果诊断。

### 输入长度兼容性审计

当前Transformers 5.12.1默认返回BatchEncoding，冻结执行器的旧`len(...)`计数记录了键数2，
而非token数。原记录不覆盖；以`context_token_recount.jsonl`的显式token-ID重算和provider usage双重核对为准。
审计状态：{context['status']}；已核对 {context.get('audited_responses', 0)}；
provider计数不一致 {context.get('provider_count_mismatches', '尚未评估')}；
上下文超限 {context.get('context_violations', '尚未评估')}；
最大真实输入 {context.get('max_recomputed_input_tokens', '尚未评估')}，输出预算1024，上限16384。
运行时服务端仍执行上下文上限；不能把错误的本地字段当作有效预检证据。
执行源码另存`executed_runner_before_token_fix.py`，后续代码修复不会追溯覆盖本次执行证据。
计数器和退出监控的修复指纹见`post_run_compatibility_fixes.json`；
本轮服务关闭状态见`service_shutdown.json`。旧监督器在主动关闭后产生的启动超时误报
不是MAD请求失败，原服务状态文件保留备查。

## B. 依赖新凭证的受控Judge

要求模型：DeepSeek-v4.1 flash；配置模型ID：`{judge_config.get('model_name')}`；
核验状态：`{judge_config.get('model_verification_status', 'unknown')}`；接口：`{judge_config.get('base_url')}`。
新凭证由隐藏输入注入本进程 `JUDGE_API_KEY_V3_NEW`，不写文件、日志或版本库，不复用旧服务凭证。
当前状态：`{judge['status']}`。受控评估：`{evaluation['status']}`。
在线成功数：{judge.get('successful_outputs', 0)}；终态数：{judge.get('terminal_requests', 0)}/144；
HTTP尝试：{judge.get('formal_attempts', 0)}；调试调用：0；额外抽取：0。
未在线运行时，准确率、F1、误报率、token费用均尚未评估，不填0或mock分数。

API/schema/引文/对象ID及非截断同时通过：{technical_valid}/{len(judge_rows)}条已收响应；
各项校验分别见evaluation.json，不能用JSON成功替代语义分类正确。
当前目录：`{judge_dir.name}`。provider已报告total_tokens：{token_total}；货币费用未核算。
数字版本兼容修订保留原12条响应及旧校验，新目录继承相同请求/尝试；没有额外模型调用，不能将两目录相加。

### 受控程序参考结果

{scores}

未完成请求保留在端到端分母；仅全部收齐后才能将本表当作完整受控结果。
精确claim定位要求预先冻结的对象、引文片段及证据匹配；消息级分类正确不等于精确定位正确。

受控72例为脚本化必要前史，开发/留出各36，基础题family按6/6隔离；12个主层各6例。
每个split分别覆盖首次错误、新引入、持续、纠正、更新后回退、更新失败、缺前史不确定等情形。
参考由受限语言解析器独立核对事实、规则、答案与前史，称为program_verified，不称人工金标。
dev/holdout共享部分句型，留出只代表本pilot中的family隔离，不能推广为自然MAD或模板独立验证。
Judge渲染器不读取expected_labels；结构化模式只增加可计算状态，不提供F/R/I或时间真值。

## C. 后续人工真实评测

状态：deferred / not_evaluated。已准备132个按agent/round平衡的目标清单、两位标注者模板、
仲裁模板、离线盲标页面及nested-to-flat转换。未生成的消息不会用脚本化文本冒充。
真实双模式264请求不在本轮调度队列；未开展独立人工标注和真实诊断指标计算。

## 后续事项

{next_steps}

## 解释边界

受控构造和程序测试不等于强模型诊断有效；不存在人工参考时不报告自然MAD的F/R/I准确率。
没有前史不自动认定initial_error；更新失败不自动当回退；答案错误不自动当规则偏离。
多对象匹配先固定位置与对象，再评分标签；所有适用参考保留在召回分母，失败不当正确拒报。
共享324消息只计一次。将来四条件比较按family成组，只作程序行为描述，不声称同伴因果。
"""
    if not config.get("preserve_root_report"):
        atomic_text(root / "RUN_SUMMARY_ZH.md", text)
    atomic_text(result / "RUN_SUMMARY_ZH.md", text)
    return states
