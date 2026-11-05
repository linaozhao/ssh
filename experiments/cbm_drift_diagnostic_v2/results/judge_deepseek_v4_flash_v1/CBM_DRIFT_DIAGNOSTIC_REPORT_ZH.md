# CBM MAD 漂移诊断：deepseek/deepseek-v4-flash Judge 报告

## 服务检查

- 模型目录 HTTP 状态：200；模型存在：True。
- 检查时运行环境已载入凭证：False；认证推理已验证：False。
- 模型目录可用不等于额度充足或推理调用成功，须以预检响应为准。

## 实验状态

- Qwen 静态协议检查复用：108/108。
- Qwen MAD 公开发言复用：1620/1620。
- 程序状态诊断复用：1620 条消息、272 个候选级连续错误事件。
- 本轮 Judge：已完成 1800/1800，剩余 0。
- API 成功 1790，未成功 10；解析成功 1790，schema/引文/对象校验通过 1764。
- 当前调度状态：`ready`。
- 预期 Judge 记录均已落盘；是否成功还须查看 API、解析和引文校验结果。
- 独立人工参考标签尚未产生，因此检测与内容分类准确率为：**尚未评估**。

## Judge 配置

固定使用 Command Code TokenPlan 的 `deepseek/deepseek-v4-flash`，thinking enabled、reasoning effort low、max_tokens 16384。未发送 temperature、top_p、惩罚参数或工具；每条目标发言独立判断。凭证仅从环境变量读取。

结构化辅助模式覆盖全部 1620 条有效发言；直接模式仅覆盖预先冻结的 180 条配对样本。配对抽样按 12 个基础题 × 3 个证据版本 × 5 个阶段各取一条，不依据 Qwen 正误或 Judge 输出。

## Qwen 与程序诊断

程序结果状态为：{'valid_correct': 616, 'valid_wrong': 1004}。过程状态为：{'correct_maintenance': 533, 'corrected': 50, 'initial_error': 49, 'newly_introduced': 65, 'persistent': 864, 'reasonable_update': 33, 'recurrence': 26}。这些是答案集合的确定性比较，不是事实/规则/推导内容类别。

按证据条件的 Qwen 发言正确率：
- `clean_stay`：188/540（34.81%）。
- `evidence_update`：213/540（39.44%）。
- `irrelevant_noise`：215/540（39.81%）。

## Judge 覆盖与预标注

- `structured_assistance`：1620/1620；API 成功 1611，解析成功 1611，schema/引文/对象校验通过 1587，截断 0。
  内容标签计数：{'factual_deviation': 785, 'inference_application_error': 180, 'rule_deviation': 992, 'unresolved': 2}；过程标签计数：{'correct_maintenance': 525, 'corrected': 49, 'initial_error': 47, 'newly_introduced': 64, 'persistent': 843, 'reasonable_update': 33, 'recurrence': 26}。
  成功请求资源统计：{'api_successful_records': 1611, 'latency_records': 1611, 'mean_latency_seconds': 24.438047175667286, 'median_latency_seconds': 22.8878, 'records_with_usage': 1611, 'prompt_tokens_records': 1611, 'mean_prompt_tokens': 9015.901303538176, 'completion_tokens_records': 1611, 'mean_completion_tokens': 3255.39044072005, 'reasoning_tokens_records': 1611, 'mean_reasoning_tokens': 3007.2849162011175}。
- `direct`：180/180；API 成功 179，解析成功 179，schema/引文/对象校验通过 177，截断 0。
  内容标签计数：{'factual_deviation': 100, 'inference_application_error': 45, 'rule_deviation': 117, 'unresolved': 1}；过程标签计数：{'correct_maintenance': 39, 'corrected': 4, 'initial_error': 8, 'newly_introduced': 15, 'persistent': 98, 'reasonable_update': 4, 'recurrence': 9}。
  成功请求资源统计：{'api_successful_records': 179, 'latency_records': 179, 'mean_latency_seconds': 41.28351508379888, 'median_latency_seconds': 39.1557, 'records_with_usage': 179, 'prompt_tokens_records': 179, 'mean_prompt_tokens': 5263.329608938548, 'completion_tokens_records': 179, 'mean_completion_tokens': 5707.692737430168, 'reasoning_tokens_records': 179, 'mean_reasoning_tokens': 5394.217877094972}。

## 与既有 Pro 结果的同请求比较

比较状态：`observed_matched_requests`。只匹配相同输入和协议，保留 Pro 的未完成覆盖范围。
```json
{
  "status": "observed_matched_requests",
  "baseline_directory": "results/judge_deepseek_v4_pro_v3",
  "baseline_model": "deepseek/deepseek-v4-pro",
  "current_model": "deepseek/deepseek-v4-flash",
  "baseline_completed_records": 509,
  "matched_records": 509,
  "both_api_successful": 502,
  "both_schema_valid": 491,
  "baseline_performance_on_matched_api_successes": {
    "api_successful_records": 502,
    "latency_records": 502,
    "mean_latency_seconds": 51.91230398406375,
    "median_latency_seconds": 46.283,
    "records_with_usage": 500,
    "prompt_tokens_records": 500,
    "mean_prompt_tokens": 8067.634,
    "completion_tokens_records": 500,
    "mean_completion_tokens": 4772.788,
    "reasoning_tokens_records": 500,
    "mean_reasoning_tokens": 4523.194
  },
  "current_performance_on_matched_api_successes": {
    "api_successful_records": 502,
    "latency_records": 502,
    "mean_latency_seconds": 22.852863147410357,
    "median_latency_seconds": 20.60305,
    "records_with_usage": 502,
    "prompt_tokens_records": 502,
    "mean_prompt_tokens": 8011.252988047809,
    "completion_tokens_records": 502,
    "mean_completion_tokens": 3160.2131474103585,
    "reasoning_tokens_records": 502,
    "mean_reasoning_tokens": 2930.4123505976095
  },
  "both_reported_usage_pairs": 500,
  "mean_completion_token_difference_current_minus_baseline": -1623.644,
  "agreement": {
    "event_presence_agrees": {
      "numerator": 466,
      "denominator": 491,
      "rate": 0.9490835030549898
    },
    "content_label_set_agrees": {
      "numerator": 307,
      "denominator": 491,
      "rate": 0.6252545824847251
    },
    "temporal_status_agrees": {
      "numerator": 479,
      "denominator": 491,
      "rate": 0.9755600814663951
    },
    "answer_effect_agrees": {
      "numerator": 488,
      "denominator": 491,
      "rate": 0.9938900203665988
    }
  },
  "by_protocol": {
    "direct": {
      "matched_records": 51,
      "both_schema_valid": 51
    },
    "structured_assistance": {
      "matched_records": 458,
      "both_schema_valid": 440
    }
  },
  "interpretation": "Matched observed requests only; agreement is not accuracy. Latency includes transport/retries and may differ across service periods."
}
```
一致率不是准确率；历史 Pro 和本轮 Flash 的服务时间不同，耗时差异不能完全归因于模型。

## 配对协议比较

当前有 174/180 个可比较的双模式配对。
事件存在性一致 160/174；内容标签集合一致 112/174；过程状态一致 142/174。
这些数值只描述同一模型在两种输入协议下的一致性，不能称为准确率。

## 引文、对象与用量

需要人工审查的解析、引文修复、schema 无效或截断记录共 1239 条，见 `parse_and_quote_audit.jsonl`。
平台报告 prompt tokens 15466753、completion tokens 6266111，其中 reasoning tokens 5810301。
平台计划额度的机器可读余额和扣费倍率未由公开 API 提供，因此不将 token 数换算成积分或费用。

## 可支持与不可支持的结论

程序能够确认当前标准集合、错误加入/排除、违反的事实与规则，以及前后答案状态。Judge 结果仅是模型预测或预标注；没有独立人工标签时，不能报告检测、定位或分类准确率。
同伴消息的可见性、引用和答案趋同可以记录，但不能据此证明从众、遗忘或因果影响。正式证据更正导致的合理答案变化不属于 drift。

## 人工标注

两名标注者应在不查看 Judge 预测的情况下，分别使用 `annotation/trajectories.html` 和 annotator 模板完成首轮标注，再进入 adjudication。Judge 预测文件必须与盲标材料分开保存。
