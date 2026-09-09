# v4.1 单智能体难度校准报告

## 实验状态

- 实验标识：`v4_1_single_agent_calibration_20260909_v2`
- 正式预期记录：1080；实际记录：1080；唯一记录：1080。
- 缺失：0；重复：0；未知键：0；指纹不一致：0。
- 预检记录：108；覆盖组合：18/18；截断：0。
- 流程完成：是。这与难度设计是否得到支持是两个独立判断。

## 模型总体结果

| 模型 | 有效答案/记录 | JSON 合规 | 正确/有效答案 | 有效答案准确率 | API 失败 | 不可识别 | 截断 |
|---|---:|---:|---:|---:|---:|---:|---:|
| qwen | 540/540 | 540/540 | 509/540 | 0.943 | 0 | 0 | 0 |
| llama | 522/540 | 518/540 | 395/522 | 0.757 | 0 | 18 | 2 |

三次采样只表示本轮观测；“三次全对”不等于证明题目始终容易。

## 模型内部稳定性

- `qwen`：完整观测 180 题；至少两个有效答案 1 题；正确与有效错误共存 1 题；三次全对 169 题；三次均有效且全错 10 题。
- `llama`：完整观测 171 题；至少两个有效答案 18 题；正确与有效错误共存 14 题；三次全对 122 题；三次均有效且全错 35 题。

## 36 个模型-组合结果

主要分歧率仅以三次均得到有效答案的题目为分母；不完整题目单独报告。

| 模型 | 组合 | 正确/有效 | 有效准确率 | 95% 聚类 bootstrap CI | 分歧题/完整题 | 正误共存/完整题 | 不完整题 |
|---|---|---:|---:|---|---:|---:|---:|
| qwen | CL1__DS1_far__IL1_low | 30/30 | 1.000 | [1.000, 1.000] | 0/10 | 0/10 | 0 |
| qwen | CL1__DS1_far__IL2_high | 30/30 | 1.000 | [1.000, 1.000] | 0/10 | 0/10 | 0 |
| qwen | CL1__DS2_medium__IL1_low | 30/30 | 1.000 | [1.000, 1.000] | 0/10 | 0/10 | 0 |
| qwen | CL1__DS2_medium__IL2_high | 30/30 | 1.000 | [1.000, 1.000] | 0/10 | 0/10 | 0 |
| qwen | CL1__DS3_near__IL1_low | 29/30 | 0.967 | [0.900, 1.000] | 1/10 | 1/10 | 0 |
| qwen | CL1__DS3_near__IL2_high | 30/30 | 1.000 | [1.000, 1.000] | 0/10 | 0/10 | 0 |
| qwen | CL2__DS1_far__IL1_low | 30/30 | 1.000 | [1.000, 1.000] | 0/10 | 0/10 | 0 |
| qwen | CL2__DS1_far__IL2_high | 30/30 | 1.000 | [1.000, 1.000] | 0/10 | 0/10 | 0 |
| qwen | CL2__DS2_medium__IL1_low | 24/30 | 0.800 | [0.500, 1.000] | 0/10 | 0/10 | 0 |
| qwen | CL2__DS2_medium__IL2_high | 30/30 | 1.000 | [1.000, 1.000] | 0/10 | 0/10 | 0 |
| qwen | CL2__DS3_near__IL1_low | 30/30 | 1.000 | [1.000, 1.000] | 0/10 | 0/10 | 0 |
| qwen | CL2__DS3_near__IL2_high | 27/30 | 0.900 | [0.700, 1.000] | 0/10 | 0/10 | 0 |
| qwen | CL3__DS1_far__IL1_low | 30/30 | 1.000 | [1.000, 1.000] | 0/10 | 0/10 | 0 |
| qwen | CL3__DS1_far__IL2_high | 30/30 | 1.000 | [1.000, 1.000] | 0/10 | 0/10 | 0 |
| qwen | CL3__DS2_medium__IL1_low | 27/30 | 0.900 | [0.700, 1.000] | 0/10 | 0/10 | 0 |
| qwen | CL3__DS2_medium__IL2_high | 24/30 | 0.800 | [0.500, 1.000] | 0/10 | 0/10 | 0 |
| qwen | CL3__DS3_near__IL1_low | 24/30 | 0.800 | [0.500, 1.000] | 0/10 | 0/10 | 0 |
| qwen | CL3__DS3_near__IL2_high | 24/30 | 0.800 | [0.500, 1.000] | 0/10 | 0/10 | 0 |
| llama | CL1__DS1_far__IL1_low | 30/30 | 1.000 | [1.000, 1.000] | 0/10 | 0/10 | 0 |
| llama | CL1__DS1_far__IL2_high | 30/30 | 1.000 | [1.000, 1.000] | 0/10 | 0/10 | 0 |
| llama | CL1__DS2_medium__IL1_low | 30/30 | 1.000 | [1.000, 1.000] | 0/10 | 0/10 | 0 |
| llama | CL1__DS2_medium__IL2_high | 26/30 | 0.867 | [0.667, 1.000] | 1/10 | 1/10 | 0 |
| llama | CL1__DS3_near__IL1_low | 21/30 | 0.700 | [0.400, 1.000] | 0/10 | 0/10 | 0 |
| llama | CL1__DS3_near__IL2_high | 20/30 | 0.667 | [0.400, 0.933] | 2/10 | 2/10 | 0 |
| llama | CL2__DS1_far__IL1_low | 27/30 | 0.900 | [0.700, 1.000] | 0/10 | 0/10 | 0 |
| llama | CL2__DS1_far__IL2_high | 27/30 | 0.900 | [0.700, 1.000] | 0/10 | 0/10 | 0 |
| llama | CL2__DS2_medium__IL1_low | 19/30 | 0.633 | [0.333, 0.900] | 1/10 | 1/10 | 0 |
| llama | CL2__DS2_medium__IL2_high | 20/30 | 0.667 | [0.367, 0.933] | 2/10 | 1/10 | 0 |
| llama | CL2__DS3_near__IL1_low | 21/27 | 0.778 | [0.500, 1.000] | 0/9 | 0/9 | 1 |
| llama | CL2__DS3_near__IL2_high | 13/28 | 0.464 | [0.200, 0.769] | 3/9 | 2/9 | 1 |
| llama | CL3__DS1_far__IL1_low | 30/30 | 1.000 | [1.000, 1.000] | 0/10 | 0/10 | 0 |
| llama | CL3__DS1_far__IL2_high | 20/29 | 0.690 | [0.379, 1.000] | 1/9 | 0/9 | 1 |
| llama | CL3__DS2_medium__IL1_low | 14/27 | 0.519 | [0.185, 0.815] | 2/9 | 1/9 | 1 |
| llama | CL3__DS2_medium__IL2_high | 21/27 | 0.778 | [0.533, 1.000] | 2/9 | 2/9 | 1 |
| llama | CL3__DS3_near__IL1_low | 16/30 | 0.533 | [0.233, 0.833] | 2/10 | 2/10 | 0 |
| llama | CL3__DS3_near__IL2_high | 10/24 | 0.417 | [0.143, 0.680] | 2/6 | 2/6 | 4 |

## 因素校准

### qwen

- `constraint_load` 边际准确率：CL1=0.994 (179/180), CL2=0.950 (171/180), CL3=0.883 (159/180)。
- `constraint_load` 固定其余因素后的趋势计数：{'flat': 2, 'higher_level_harder_or_equal': 2, 'nonmonotonic': 2}。
- `distractor_similarity` 边际准确率：DS1_far=1.000 (180/180), DS2_medium=0.917 (165/180), DS3_near=0.911 (164/180)。
- `distractor_similarity` 固定其余因素后的趋势计数：{'flat': 1, 'higher_level_harder_or_equal': 4, 'nonmonotonic': 1}。
- `information_load` 边际准确率：IL1_low=0.941 (254/270), IL2_high=0.944 (255/270)。
- `information_load` 固定其余因素后的趋势计数：{'flat': 5, 'higher_level_easier_or_equal': 2, 'higher_level_harder_or_equal': 2}。
- 本轮最易三格：CL1__DS1_far__IL1_low, CL1__DS1_far__IL2_high, CL1__DS2_medium__IL1_low；最难三格：CL3__DS2_medium__IL2_high, CL3__DS3_near__IL1_low, CL3__DS3_near__IL2_high。

### llama

- `constraint_load` 边际准确率：CL1=0.872 (157/180), CL2=0.726 (127/175), CL3=0.665 (111/167)。
- `constraint_load` 固定其余因素后的趋势计数：{'higher_level_harder_or_equal': 3, 'nonmonotonic': 3}。
- `distractor_similarity` 边际准确率：DS1_far=0.916 (164/179), DS2_medium=0.747 (130/174), DS3_near=0.598 (101/169)。
- `distractor_similarity` 固定其余因素后的趋势计数：{'higher_level_harder_or_equal': 3, 'nonmonotonic': 3}。
- `information_load` 边际准确率：IL1_low=0.788 (208/264), IL2_high=0.725 (187/258)。
- `information_load` 固定其余因素后的趋势计数：{'flat': 2, 'higher_level_easier_or_equal': 2, 'higher_level_harder_or_equal': 5}。
- 本轮最易三格：CL1__DS1_far__IL1_low, CL1__DS1_far__IL2_high, CL1__DS2_medium__IL1_low；最难三格：CL3__DS2_medium__IL1_low, CL2__DS3_near__IL2_high, CL3__DS3_near__IL2_high。

- 两模型 18 格准确率排序的 Spearman 相关：0.695。
- 受控切片的 CL、DS、IL 逐格结果保存在 `factor_analysis.json`。不得预设单调性；本原型各格不是同题改写，因此只能作组间初步校准。
- `constraint_load` 结论：两模型的边际结果均显示高水平更难，但受控切片并非全部单调；高减低准确率差为 {'qwen': -0.111111, 'llama': -0.207551}。
- `distractor_similarity` 结论：两模型的边际结果均显示高水平更难，但受控切片并非全部单调；高减低准确率差为 {'qwen': -0.088889, 'llama': -0.318568}。
- `information_load` 结论：仅部分模型显示明确下降，模型间证据不一致；高减低准确率差为 {'qwen': 0.003703, 'llama': -0.063073}。
- 同时显示基本解题能力与自然分歧的组合：llama:CL1__DS2_medium__IL2_high(acc=0.867, disagreement=1/10)；llama:CL1__DS3_near__IL2_high(acc=0.667, disagreement=2/10)；llama:CL2__DS2_medium__IL1_low(acc=0.633, disagreement=1/10)；llama:CL2__DS2_medium__IL2_high(acc=0.667, disagreement=2/10)；llama:CL2__DS3_near__IL2_high(acc=0.464, disagreement=3/9)；llama:CL3__DS1_far__IL2_high(acc=0.690, disagreement=1/9)；llama:CL3__DS2_medium__IL1_low(acc=0.519, disagreement=2/9)；llama:CL3__DS2_medium__IL2_high(acc=0.778, disagreement=2/9)；llama:CL3__DS3_near__IL1_low(acc=0.533, disagreement=2/10)；llama:CL3__DS3_near__IL2_high(acc=0.417, disagreement=2/6)。

## 稳定错误案例

- `qwen`：共 10 题；示例：attr_v4_1_000081_original(CL2__DS2_medium__IL1_low, wrong={'D': ['C2']})；attr_v4_1_000083_original(CL2__DS2_medium__IL1_low, wrong={'D': ['C4']})；attr_v4_1_000112_original(CL2__DS3_near__IL2_high, wrong={'C': ['C5']})；attr_v4_1_000149_original(CL3__DS2_medium__IL1_low, wrong={'B': ['C7']})；attr_v4_1_000153_original(CL3__DS2_medium__IL2_high, wrong={'D': ['C1']})。
- `llama`：共 35 题；示例：attr_v4_1_000037_original(CL1__DS2_medium__IL2_high, wrong={'D': ['C3']})；attr_v4_1_000045_original(CL1__DS3_near__IL1_low, wrong={'C': ['C3']})；attr_v4_1_000049_original(CL1__DS3_near__IL1_low, wrong={'B': ['C3']})；attr_v4_1_000050_original(CL1__DS3_near__IL1_low, wrong={'D': ['C2']})；attr_v4_1_000059_original(CL1__DS3_near__IL2_high, wrong={'B': ['C3']})。

## 约束违反诊断

- 有效错误答案共 158 个；其中单约束违反比例 0.85443。
- 归一化分母为：属性在题目中出现，且至少一个错误选项可违反该属性时的有效运行次数。
- `has_management_experience`：被选中违反 10 次；可违反暴露 72；归一化率 0.138889。
- `has_public_speaking_experience`：被选中违反 9 次；可违反暴露 77；归一化率 0.116883。
- `has_project_experience`：被选中违反 13 次；可违反暴露 114；归一化率 0.114035。
- `available_next_month`：被选中违反 27 次；可违反暴露 257；归一化率 0.105058。
- `available_afternoon`：被选中违反 25 次；可违反暴露 294；归一化率 0.085034。
- `can_work_remote`：被选中违反 12 次；可违反暴露 150；归一化率 0.08。
- `can_work_onsite`：被选中违反 13 次；可违反暴露 165；归一化率 0.078788。
- `has_security_clearance`：被选中违反 5 次；可违反暴露 66；归一化率 0.075758。
- DS3 的错误选项按设计均只违反一个约束；DS3 中单约束错误占比高不能单独解释为模型新行为。

## 解析与输出审计

- 解析器版本：`v4.1-answer-parser-2`；所有变化仅重解析已保存原文，没有追加模型调用。
- 需要人工审查的格式、备用解析、截断或请求异常记录：22。
- 按模型：{'llama': 22}；按解析来源：{'malformed_json_answer_field': 4, 'none': 18}；其中截断 2 条。
- 明确答案和完整 JSON 合规分别统计；缺少 confidence 但答案明确时仍保留答案。
- 备用解析只接受裸 A/B/C/D 或明确 final-answer 声明；解释中普通的 Option/Candidate 提及不会被当作答案，冲突声明标为不可确定。

## 不确定性与限制

- 每格只有 10 道题，置信区间按题目聚类重采样，同题三次响应整体保留。
- 组合之间不是逐题配对版本，因素差异可能仍包含属性、场景和模板构成差异。
- 后端接收 seed，但不能据此宣称采样在所有软硬件状态下完全可复现。
- 本轮没有任何辩论轨迹，因此错误选项的约束违反不是“辩论引起的漂移”。

## 扩充建议

**REFINE BEFORE EXPANSION**

不建议按当前比例直接均匀扩充到 540 题。先保留已有区分信号的 CL/DS 设计，增强或重构对模型影响不稳定的 IL2，并人工复核两模型三次稳定答错的题目；完成一轮小样本复核后再扩充。

若后续扩充，应使用与 `attr_v4_1_*` 不冲突的新 ID 区间，并保存规范化题目内容哈希去重；每格新增 20 题作为独立验证集，不用新增题回填或优化本轮统计。

Qwen 接近全对：是。本轮兼具基本能力和自然分歧的模型-组合行数为 10/36。
