# CBM Drift Diagnostic v2

## Flash Judge 独立实验

新增 `config/tokenplan_deepseek_v4_flash.json`，输出目录为
`results/judge_deepseek_v4_flash_v1/`。通过服务模型目录确认模型标识为
`deepseek/deepseek-v4-flash`。本轮复用已有 MAD 轨迹，不重新生成智能体发言。

Flash 与 Pro 使用相同数据、提示词、配对样本和预检样本，保留 thinking enabled、
reasoning effort low、max_tokens 16384。上限不等于实际生成量；本轮先只改变 Judge
模型，比较真实耗时和 token。Flash 配置显式直连服务，避开当前不可用的环境代理，
原有 Pro 配置不变。

以下命令在本目录执行；`TOKENPLAN_API_KEY` 应由本地运行环境安全注入。

```bash
python scripts/check_tokenplan_service.py --config config/tokenplan_deepseek_v4_flash.json
python scripts/prepare_tokenplan_judge.py --config config/tokenplan_deepseek_v4_flash.json
python scripts/run_tokenplan_judge.py --config config/tokenplan_deepseek_v4_flash.json --phase preflight --validate-preflight
python scripts/run_tokenplan_judge.py --config config/tokenplan_deepseek_v4_flash.json --phase formal
python scripts/analyze_tokenplan_judge.py --config config/tokenplan_deepseek_v4_flash.json
python scripts/validate_tokenplan_experiment.py --config config/tokenplan_deepseek_v4_flash.json
```

需要跨额度窗口续跑时，在同一凭证环境运行：

```bash
python scripts/run_tokenplan_scheduler.py --config config/tokenplan_deepseek_v4_flash.json
```

先完成同样的 12 条消息 × 2 种协议，共 24 次预检；通过后才允许正式队列。
全量仍为结构化辅助 1620 次和直接模式 180 次，共 1800 次，预检计入总量。
结果、锁、停止文件和额度窗口与 Pro 分离；平台实际额度仍由账号共享。
在 Flash 结果目录创建 `STOP` 可要求调度器在当前请求返回后停止。

分析额外输出 `matched_model_comparison.jsonl`，仅比较两模型已有且输入一致的请求，
同时统计耗时、token、内容标签和时间标签的一致性。Pro 未完成部分不补造结果，
一致性不作为准确率。详细状态见 `FLASH_EXPERIMENT_SETUP_ZH.md`。

## TokenPlan DeepSeek-V4-Pro 恢复实验

本轮恢复实验保留旧 `results/judge/` 作为不兼容的探索性结果，新的正式结果写入
`results/judge_deepseek_v4_pro_v3/`。配置固定为 Command Code TokenPlan 的
`deepseek/deepseek-v4-pro`、thinking enabled、reasoning effort low，密钥只从
`TOKENPLAN_API_KEY` 环境变量读取。

```bash
python scripts/build_resume_audit.py
python scripts/prepare_tokenplan_judge.py

export TOKENPLAN_API_KEY='在本地安全输入，不要写入仓库'
python scripts/run_tokenplan_judge.py --phase preflight --validate-preflight
python scripts/run_tokenplan_judge.py --phase formal
python scripts/analyze_tokenplan_judge.py
```

跨窗口后台调度可使用：

```bash
export TOKENPLAN_API_KEY='在本地安全输入，不要写入仓库'
nohup python scripts/run_tokenplan_scheduler.py \
  > results/judge_deepseek_v4_pro_v3/scheduler.log 2>&1 &

# 安全停止：调度器会在当前请求返回后退出
touch results/judge_deepseek_v4_pro_v3/STOP
```

直接模式只覆盖预先冻结的 180 条配对消息；结构化辅助模式覆盖全部 1620 条消息。
额度余额没有公开、可信的机器接口时，调度器每个五小时窗口最多启动 100 次请求，
逐请求原子落盘并通过 `(experiment_fingerprint, judge_request_id)` 断点续跑。

This experiment builds a 12-family development prototype for diagnosing observable deviations in synchronized Qwen3-8B MAD trajectories. It preserves all v1 and earlier MAD artifacts.

## Scope

- 12 source families selected without model outcomes.
- Three paired five-stage variants per family: clean stay, evidence update, and non-target noise.
- Independent evidence replay plus exact candidate-set solving.
- 108 independent protocol-check calls.
- 1,620 MAD calls: 36 trajectories × 5 stages × 3 agents × R0/R1/R2.
- Programmatic state diagnostics, Judge input packages, annotation materials, and a reference-label evaluation entry point.

No self-consistency voting, post-MAD self-revision, mitigation, RL, or model fine-tuning is run. Judge predictions are pre-annotations, never human Gold.

## Commands

```bash
python experiments/cbm_drift_diagnostic_v2/scripts/prepare_data.py
python experiments/cbm_drift_diagnostic_v2/scripts/validate_data.py
pytest -q experiments/cbm_drift_diagnostic_v2/tests

bash experiments/cbm_drift_diagnostic_v2/scripts/launch_qwen_service.sh 1 8111
bash experiments/cbm_drift_diagnostic_v2/scripts/launch_qwen_service.sh 5 8115
python experiments/cbm_drift_diagnostic_v2/scripts/run_protocol_check.py --resume
python experiments/cbm_drift_diagnostic_v2/scripts/run_mad.py --preflight-only --resume
python experiments/cbm_drift_diagnostic_v2/scripts/build_preflight_manifest.py
python experiments/cbm_drift_diagnostic_v2/scripts/run_mad.py --resume
python experiments/cbm_drift_diagnostic_v2/scripts/analyze_program.py

# Set this only in the process environment; never put the key in project files.
export DEEPSEEK_API_KEY='...'
python experiments/cbm_drift_diagnostic_v2/scripts/run_judge.py

python experiments/cbm_drift_diagnostic_v2/scripts/build_annotation_package.py
python experiments/cbm_drift_diagnostic_v2/scripts/evaluate_detector.py
python experiments/cbm_drift_diagnostic_v2/scripts/build_report.py
```

The test-split entry point is intentionally separate and is not run in this stage:

```bash
python experiments/cbm_drift_diagnostic_v2/scripts/prepare_data.py \
  --split test \
  --output-dir /path/to/frozen_test_data \
  --exclude-manifest experiments/cbm_drift_diagnostic_v2/data/selection_manifest.jsonl
```

## Interpretation

Program outputs establish answer correctness, extra/omitted candidates, formal violations, and adjacent state changes. Content labels require semantic review. Without independent reference labels, detector precision/recall/F1 remain **not evaluated**.

The Judge configuration stores only the environment-variable name. Credentials, weights, and service logs are excluded from commits. The direct and reference-structure-assisted outputs are model pre-annotations, not human Gold.

## Method context

This is a CBM-inspired adaptation for Boolean attribute filtering, not a complete reproduction of the source task. Method context: [CBM](https://arxiv.org/abs/2605.30219), [Stay Focused](https://aclanthology.org/2026.findings-eacl.268/), and [MAST](https://arxiv.org/abs/2503.13657).
