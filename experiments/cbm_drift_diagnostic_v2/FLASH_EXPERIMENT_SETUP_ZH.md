# Flash Judge 实验建立记录

日期：2026-10-15。

## 研究设置

新实验标识为 `cbm_drift_v2_tokenplan_deepseek_v4_flash_v1_16384_programmatic_offsets`，
配置为 `config/tokenplan_deepseek_v4_flash.json`，结果目录为
`results/judge_deepseek_v4_flash_v1/`。使用当前服务目录中实际存在的
`deepseek/deepseek-v4-flash`，不自动替换为 fast、vision 或 v4.1 型号。

复用既有 1620 条 Qwen MAD 发言及其 Judge 输入包、程序诊断和证据轨迹。
结构化辅助覆盖 1620 条；直接模式覆盖固定的 180 条配对消息；合计 1800 次。
首先执行与 Pro 相同的 12 条消息、24 次请求预检，预检通过后纳入全量结果。
预检未通过时不进入正式调用。格式错误和截断保留，不选择性重采样。

## 推理协议与费用假设

保留 Pro 的提示词、标签体系、引文校验、thinking enabled、reasoning effort low、
max_tokens 16384 和单请求调度。这一版的主要实验变化是 Judge 模型。
16384 是输出上限，不是固定消耗；Flash 实际是否节省 token 必须由预检和后续
响应的 usage 确认。暂不同时修改提示词、压缩历史或关闭 thinking，以避免混合解释。

推理结果保留原始内容、reasoning、usage、延迟、请求参数、模型返回名称、错误、
结束原因和引文校验结果。数据、配置、提示词、请求都有指纹；跨实验结果不可续接。
已有 Pro 目录只读用作比较，保留全部原始响应与报告。

## 运行环境检查

服务 `https://api.commandcode.ai/provider/v1/models` 直连返回 HTTP 200，目录确认
存在 `deepseek/deepseek-v4-flash`。当前环境代理连接失败，因此 Flash 单独设为
`trust_env=false`，原有 Pro 配置未改动。

建立快照时尚未载入 `TOKENPLAN_API_KEY`，因此当时没有发起真实 Judge 推理，也没有验证
账号额度、推理授权或 Flash 输出质量。`service_check.json` 记录的是模型目录检查，
不是推理成功记录。未把历史聊天中的凭证写入配置或实验产物。

## 本地验证

`pytest -q -o addopts='' experiments/cbm_drift_diagnostic_v2/tests`：35 passed。
覆盖旧协议回归、新旧目录隔离、样本一致性、冻结指纹、跨实验记录拒绝、断点跳过、
模拟 SSE、预检门禁、配对统计分母和未上报 token 不能视为零。模拟请求仅用于测试，
不计入真实实验结果。环境另有两条既有 pandas 可选依赖版本警告，无测试失败。

建立快照时冻结队列验证通过：1800 个唯一请求，其中预检 24 次；真实完成记录 0，
`experiment_complete=false`。`--allow-partial` 的通过仅表示队列和现有部分记录
完整性通过，不代表模型预检或全量实验完成。

对旧 Pro 配置、结果目录、提示词、证据序列、原始 MAD 发言和输入包共 530 个文件
进行内容哈希前后核对，未发现修改或新增。`git diff --check` 和 Python 编译检查通过。

## 凭证载入后启动

2026-10-15 用户提供新凭证后，已通过隐藏输入将其仅注入后台调度器进程环境，
未写入配置、日志或结果文件。调度器进程启动时 PID 为 1095387。
首条 Flash 真实响应通过认证、JSON 解析及 schema/引文/对象校验，未发生截断。
启动后先完成 24 次预检；全部通过才进入正式队列，按既定额度窗口断点续跑。

`local_verification.json` 是启动前的本地验证快照，不是实时实验进度。
最新进度以 `records/` 原子记录为准；每批结束后更新 `progress_summary.json`、
`preflight_validation.json`、`daemon_status.json` 和动态中文报告。

2026-10-15 09:35（Asia/Shanghai）预检完成并通过：24/24 API 成功、解析成功、
schema/引文/对象校验通过，截断 0。调度器已自动切换到正式阶段。
相同 24 个历史 Pro 请求的平均耗时为 83.75 秒，Flash 为 19.40 秒；平均输出
token 分别为 5437 和 3529.96。不同服务时段可能影响延迟，以上是初步观测。
内容标签集合一致 14/24，事件存在性一致 20/24；一致性不能视作准确率，仍需
独立语义复核。全量实验尚未完成，实时覆盖以正式结果目录为准。

## 比较与解释

`analysis_summary.json` 记录每协议的平均与中位成功请求耗时、平均输入/输出 token，
以及和历史 Pro 的同请求比较。`matched_model_comparison.jsonl` 保存双方均通过
schema/引文校验的事件存在性、内容标签、时间标签和答案影响比较。

比较仅使用相同请求、输入指纹和协议的交集；报告交集数量和分母。模型运行时间
不同，延迟变化可能受到服务负载和网络影响。模型间一致性不是诊断准确率；
独立参考标注仍是评估准确率的必要条件。若预检显示预算或协议需调整，应另建版本，
不修改已冻结配置后混用已有响应。

## 启动

在本实验目录及安全注入 `TOKENPLAN_API_KEY` 的运行环境中：

```bash
python scripts/check_tokenplan_service.py --config config/tokenplan_deepseek_v4_flash.json
python scripts/run_tokenplan_judge.py --config config/tokenplan_deepseek_v4_flash.json --phase preflight --validate-preflight
python scripts/run_tokenplan_scheduler.py --config config/tokenplan_deepseek_v4_flash.json
```

调度器复用断点、有限基础设施重试和五小时额度窗口策略，不会重新执行 MAD。
默认未知额度窗口最多 100 次尝试；这是本地调度上限，不是平台剩余额度。
Flash 与 Pro 虽然使用独立目录，仍共享同一账号的平台限额。
