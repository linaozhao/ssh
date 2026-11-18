# 受控诊断 v4 R2 实验报告

## 状态
192 个任务，576 个方法-任务单元；已收 576，有效检测输出 576。
已记录物理调用 590；API 失败 0。
参考等级：program_verified，独立人工确认 0。真实 MAD 轨迹评测尚未开展。CPU 构造与评分，不启动 GPU。

## 分组结果
|划分|任务|方法|已收/应收|检测 F1|核心精确 F1|核心重叠 F1|完整严格 F1|
|---|---|---|---|---|---|---|---|
|dev|A|M0|36/36|1.000|0.800|0.800|0.533|
|dev|A|M1|36/36|1.000|0.833|0.867|0.567|
|dev|A|M2|36/36|1.000|0.967|1.000|0.933|
|dev|B1|M0|36/36|1.000|1.000|1.000|0.750|
|dev|B1|M1|36/36|1.000|0.941|0.941|0.765|
|dev|B1|M2|36/36|1.000|1.000|1.000|1.000|
|dev|B2|M0|24/24|1.000|0.833|0.833|0.333|
|dev|B2|M1|24/24|1.000|0.778|0.778|0.444|
|dev|B2|M2|24/24|1.000|1.000|1.000|1.000|
|holdout|A|M0|36/36|1.000|0.900|0.900|0.567|
|holdout|A|M1|36/36|1.000|0.867|0.867|0.500|
|holdout|A|M2|36/36|1.000|1.000|1.000|1.000|
|holdout|B1|M0|36/36|1.000|0.930|0.986|0.704|
|holdout|B1|M1|36/36|1.000|0.958|0.986|0.732|
|holdout|B1|M2|36/36|1.000|1.000|1.000|1.000|
|holdout|B2|M0|24/24|1.000|1.000|1.000|0.556|
|holdout|B2|M1|24/24|1.000|1.000|1.000|0.389|
|holdout|B2|M2|24/24|1.000|1.000|1.000|1.000|

## 研究问题
开发集为开发表现，不能与留出合并为测试准确率。下述对比只使用已执行的留出输出。
- M0 同错决定不同依据：A1-A4 全正确 6/6 组。
- M0 立场变化：6/6 组两条均正确；改写且核心定位正确 6/6。
- M0 历史时间及支持：{'correct': 30, 'denominator': 36}；历史不足正确未知 {'correct': 6, 'denominator': 6}。
- M0 B2 自主首次消息定位：{'correct': 24, 'denominator': 24}；过早/滞后/缺失 {'early': 0, 'late': 0, 'first_missing_or_invalid': 0}。
- M1 同错决定不同依据：A1-A4 全正确 6/6 组。
- M1 立场变化：6/6 组两条均正确；改写且核心定位正确 6/6。
- M1 历史时间及支持：{'correct': 30, 'denominator': 36}；历史不足正确未知 {'correct': 6, 'denominator': 6}。
- M1 B2 自主首次消息定位：{'correct': 24, 'denominator': 24}；过早/滞后/缺失 {'early': 0, 'late': 0, 'first_missing_or_invalid': 0}。
- M2 同错决定不同依据：A1-A4 全正确 6/6 组。
- M2 立场变化：6/6 组两条均正确；改写且核心定位正确 6/6。
- M2 历史时间及支持：{'correct': 36, 'denominator': 36}；历史不足正确未知 {'correct': 6, 'denominator': 6}。
- M2 B2 自主首次消息定位：{'correct': 24, 'denominator': 24}；过早/滞后/缺失 {'early': 0, 'late': 0, 'first_missing_or_invalid': 0}。

## 方法比较
各方法增益仅为本次小样本描述；不预设 M2 优于 M0。
- A M1 相对 M0：detection: +0.000；core_exact: -0.033；core_overlap: -0.033；strict_full: -0.067
- A M2 相对 M0：detection: +0.000；core_exact: +0.100；core_overlap: +0.100；strict_full: +0.433
- B1 M1 相对 M0：detection: +0.000；core_exact: +0.028；core_overlap: +0.000；strict_full: +0.028
- B1 M2 相对 M0：detection: +0.000；core_exact: +0.070；core_overlap: +0.014；strict_full: +0.296
- B2 M1 相对 M0：detection: +0.000；core_exact: +0.000；core_overlap: +0.000；strict_full: -0.167
- B2 M2 相对 M0：detection: +0.000；core_exact: +0.000；core_overlap: +0.000；strict_full: +0.444

## 局限与解释边界
- 沿用 12 道旧基础题，6/6 family 隔离；不是全新基础题泛化。开发/留出使用不同事实措辞及规则/决定句式，但仍是受控有限语言。
- A/B2 采用原证据的声明发布前缀，以隔离一个决定性冲突；不修改原事实或规则，不把未发布事实当 false。
- B1 前五类使用原 T4 状态重放得到的权威快照，窗口内无更正过程；仅第六类展示原始属性更正事件。只比较同一智能体、同一对象的明确可见前史。
- 旧 v4 开发版发现稳定状态/更新状态背景重叠后停止，原响应与勘误保留；R2 没有复用旧响应。旧版留出调用为零。
- 程序参考由独立文本识别器重读输出，并以穷举补全复核状态；正式关系判定与 M2 共享部分代码，因此不能当作独立人工金标准。
- B2 为三个同步智能体、三轮的短片段；错误前消息正确且首次错误唯一。已给目标的 A/B1 不计为自主定位成绩。
- 原文精确匹配与跨度 IoU>=0.5 分开；核心定位不要求规则列表完全一致，多余证据仍影响依据与完整指标。
- 引文唯一时程序修复字符下标并记录 offset_repaired，原输出保留；不能把修复后定位当作纯模型字符下标成绩。
- 原实验与评分不覆盖；受控结果不证明真实 MAD 诊断有效或同伴影响因果关系。
- 零执行组标为尚未评估；失败保留在端到端分母。不因错误、格式或截断重复采样。

## 成本
```json
{
  "M0": {
    "physical_calls": 192,
    "reported_total_tokens": 887815,
    "reported_prompt_tokens": 540220,
    "reported_completion_tokens": 347595,
    "unknown_usage_calls": 0,
    "total_latency_seconds": 1923.6152477217838
  },
  "M1": {
    "physical_calls": 192,
    "reported_total_tokens": 1143445,
    "reported_prompt_tokens": 808926,
    "reported_completion_tokens": 334519,
    "unknown_usage_calls": 0,
    "total_latency_seconds": 1857.5704786134884
  },
  "M2": {
    "physical_calls": 206,
    "reported_total_tokens": 1114773,
    "reported_prompt_tokens": 564540,
    "reported_completion_tokens": 550233,
    "unknown_usage_calls": 0,
    "total_latency_seconds": 2573.980271889828
  }
}
```
