# CBM MAD 漂移诊断：DeepSeek-V4-Pro Judge 报告

## 实验状态

- Qwen 静态协议检查复用：108/108。
- Qwen MAD 公开发言复用：1620/1620。
- 程序状态诊断复用：1620 条消息、272 个候选级连续错误事件。
- 本轮 Judge：已完成 44/1800，剩余 1756。
- 当前调度状态：`waiting_for_unknown_quota_window`。
- 独立人工参考标签尚未产生，因此检测与内容分类准确率为：**尚未评估**。

## Judge 配置

固定使用 Command Code TokenPlan 的 `deepseek/deepseek-v4-pro`，thinking enabled、reasoning effort low、max_tokens 4096。未发送 temperature、top_p、惩罚参数或工具；每条目标发言独立判断。凭证仅从环境变量读取。

结构化辅助模式覆盖全部 1620 条有效发言；直接模式仅覆盖预先冻结的 180 条配对样本。配对抽样按 12 个基础题 × 3 个证据版本 × 5 个阶段各取一条，不依据 Qwen 正误或 Judge 输出。

## Qwen 与程序诊断

程序结果状态为：{'valid_correct': 616, 'valid_wrong': 1004}。过程状态为：{'correct_maintenance': 533, 'corrected': 50, 'initial_error': 49, 'newly_introduced': 65, 'persistent': 864, 'reasonable_update': 33, 'recurrence': 26}。这些是答案集合的确定性比较，不是事实/规则/推导内容类别。

按证据条件的 Qwen 发言正确率：
- `clean_stay`：188/540（34.81%）。
- `evidence_update`：213/540（39.44%）。
- `irrelevant_noise`：215/540（39.81%）。

## Judge 覆盖与预标注

- `structured_assistance`：32/1620；API 成功 32，解析成功 32，schema/引文/对象校验通过 32，截断 0。
  内容标签计数：{'factual_deviation': 18, 'inference_application_error': 16, 'rule_deviation': 10}；过程标签计数：{'correct_maintenance': 11, 'corrected': 1, 'initial_error': 1, 'newly_introduced': 3, 'persistent': 14, 'reasonable_update': 1, 'recurrence': 1}。
- `direct`：12/180；API 成功 12，解析成功 12，schema/引文/对象校验通过 12，截断 0。
  内容标签计数：{'factual_deviation': 3, 'inference_application_error': 6, 'rule_deviation': 1}；过程标签计数：{'correct_maintenance': 4, 'initial_error': 1, 'persistent': 5, 'reasonable_update': 2}。

## 配对协议比较

当前有 12/180 个可比较的双模式配对。
事件存在性一致 10/12；内容标签集合一致 8/12；过程状态一致 8/12。
这些数值只描述同一模型在两种输入协议下的一致性，不能称为准确率。

## 引文、对象与用量

需要人工审查的解析、引文修复、schema 无效或截断记录共 29 条，见 `parse_and_quote_audit.jsonl`。
平台报告 prompt tokens 370528、completion tokens 244269，其中 reasoning tokens 232521。
平台计划额度的机器可读余额和扣费倍率未由公开 API 提供，因此不将 token 数换算成积分或费用。

## 可支持与不可支持的结论

程序能够确认当前标准集合、错误加入/排除、违反的事实与规则，以及前后答案状态。Judge 结果仅是模型预测或预标注；没有独立人工标签时，不能报告检测、定位或分类准确率。
同伴消息的可见性、引用和答案趋同可以记录，但不能据此证明从众、遗忘或因果影响。正式证据更正导致的合理答案变化不属于 drift。

## 人工标注

两名标注者应在不查看 Judge 预测的情况下，分别使用 `annotation/trajectories.html` 和 annotator 模板完成首轮标注，再进入 adjudication。Judge 预测文件必须与盲标材料分开保存。
