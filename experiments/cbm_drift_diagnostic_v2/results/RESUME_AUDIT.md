# 中断恢复审计

- 分支：`feature/cbm-drift-diagnostic-v2`；起始 HEAD：`9daeca644351d047cda2ddc448bff3e15a9b5ea5`。
- 工作区：整个 `experiments/cbm_drift_diagnostic_v2/` 尚未提交；保留全部现有文件。
- 冻结数据：12 个基础题、36 条证据序列，验证 通过。
- Qwen 静态协议：108/108；缺失 0，重复 0。
- Qwen MAD：1620/1620；缺失 0，重复 0。
- 程序诊断：1620 条消息、272 个候选级连续错误事件。
- 旧 Judge：1434/3240 条，覆盖 717 条消息；API 失败 0，解析失败 0，schema 无效 2。
- 旧 `summary.json` 只记录 1 条预检，与实际 1,434 条 JSONL 不一致，已标记为陈旧，未作为完成统计使用。
- 旧 Judge 使用不同供应商端点、关闭 thinking、不同输出预算及不同抽样范围，因此保留为探索材料，不混入本轮正式结果。
- 人工标注包：36 条完整轨迹，默认隐藏 Judge 预测；尚无独立人工参考标签。
- 旧运行进程：无。
- 上次停止原因：额度耗尽后连接断开；没有发现仍占用队列的调度器。

## 恢复范围

复用冻结数据、108 条静态协议输出、1620 条 MAD 输出和全部程序诊断。新建 `results/judge_deepseek_v4_pro_v1/`，按本轮 TokenPlan DeepSeek-V4-Pro 协议重新执行 Judge，不覆盖旧结果。
