# Pilot English v3 Chinese View

说明：这是 `pilot_en_v3.jsonl` 的中文阅读版，只用于人工查看。Gold、约束 ID、矩阵和 violation signature 均来自英文原始数据。

## 1. attr_en_000001_zh_view

- source: `attr_en_000001_original`
- scenario: `project_assignment`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `B`

项目团队需要为一项专门任务分配一名成员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要周二可以参与工作。
2. 候选人需要具备团队协作经验。
3. 候选人需要周一可以参与工作。
4. 候选人需要有研究项目经验。

候选人：
A. Briar 周一可以参与工作，Briar 缺少团队协作经验。另外，Briar 参与过研究项目，Briar 周二可以参与工作。
B. Jamie 周一可以参与工作，Jamie 有团队协作经验。另外，Jamie 周二可以参与工作，Jamie 参与过研究项目。
C. Devon 周二无法参与工作，Devon 周一可以参与工作。另外，Devon 有团队协作经验，Devon 没有研究项目经历。
D. Lane 参与过研究项目，Lane 有团队协作经验。另外，Lane 周一无法参与工作，Lane 周二可以参与工作。

哪位候选人适合承担这项任务？

约束与 violation signature：

- `C1` `available_tuesday=True`：候选人需要周二可以参与工作。
- `C2` `has_teamwork_experience=True`：候选人需要具备团队协作经验。
- `C3` `available_monday=True`：候选人需要周一可以参与工作。
- `C4` `has_research_experience=True`：候选人需要有研究项目经验。

- `A` violation: `['C2']`
- `B` violation: `[]`
- `C` violation: `['C1', 'C4']`
- `D` violation: `['C3']`

## 2. attr_en_000002_zh_view

- source: `attr_en_000002_original`
- scenario: `expert_recruitment`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `A`

某研究实验室正在为一个新项目选择一名研究人员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要具备数据分析经验。
2. 候选人需要能够使用英语进行工作沟通。
3. 候选人需要周二可以参与工作。
4. 候选人需要具备质量保证经验。

候选人：
A. Reese 周二可以参与工作，Reese 能够用英语进行工作沟通。另外，Reese 做过数据分析工作，Reese 有质量保证经验。
B. Jordan 没有实际数据分析经历，Jordan 有质量保证经验。另外，Jordan 能够用英语进行工作沟通，Jordan 周二可以参与工作。
C. Robin 没有质量保证经验，Robin 能够用英语进行工作沟通。另外，Robin 周二可以参与工作，Robin 做过数据分析工作。
D. Kris 不能用英语进行工作沟通，Kris 周二无法参与工作。另外，Kris 有质量保证经验，Kris 做过数据分析工作。

哪位候选人满足所有要求？

约束与 violation signature：

- `C1` `has_data_analysis_experience=True`：候选人需要具备数据分析经验。
- `C2` `speaks_english=True`：候选人需要能够使用英语进行工作沟通。
- `C3` `available_tuesday=True`：候选人需要周二可以参与工作。
- `C4` `has_quality_assurance_experience=True`：候选人需要具备质量保证经验。

- `A` violation: `[]`
- `B` violation: `['C1']`
- `C` violation: `['C4']`
- `D` violation: `['C2', 'C3']`

## 3. attr_en_000003_zh_view

- source: `attr_en_000003_original`
- scenario: `expert_recruitment`
- option_closeness: `medium`
- structural_complexity: `low`
- gold: `B`

某研究实验室正在为一个新项目选择一名研究人员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要下个月可以加入项目。
2. 候选人不能存在与项目相关的利益冲突。
3. 候选人需要具备编程经验。

候选人：
A. Kris 没有处理过编程任务。另外，Kris 不存在项目相关的利益冲突，Kris 下个月可以加入项目。
B. Tatum 不存在项目相关的利益冲突。另外，Tatum 有实际编程经验，Tatum 下个月可以加入项目。
C. Quinn 下个月可以加入项目。另外，Quinn 有实际编程经验，Quinn 与项目存在利益冲突。
D. Morgan 下个月无法加入项目。另外，Morgan 有实际编程经验，Morgan 与项目存在利益冲突。

哪位候选人满足所有要求？

约束与 violation signature：

- `C1` `available_next_month=True`：候选人需要下个月可以加入项目。
- `C2` `has_conflict=False`：候选人不能存在与项目相关的利益冲突。
- `C3` `has_programming_experience=True`：候选人需要具备编程经验。

- `A` violation: `['C3']`
- `B` violation: `[]`
- `C` violation: `['C2']`
- `D` violation: `['C1', 'C2']`

## 4. attr_en_000004_zh_view

- source: `attr_en_000004_original`
- scenario: `expert_recruitment`
- option_closeness: `hard`
- structural_complexity: `low`
- gold: `A`

某研究实验室正在为一个新项目选择一名研究人员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要具备数据分析经验。
2. 候选人需要具备安全许可。
3. 候选人需要周二可以参与工作。

候选人：
A. Hayden 具备安全许可。另外，Hayden 周二可以参与工作，Hayden 做过数据分析工作。
B. Payton 具备安全许可。另外，Payton 周二可以参与工作，Payton 没有实际数据分析经历。
C. Tatum 不具备安全许可。另外，Tatum 周二可以参与工作，Tatum 做过数据分析工作。
D. Devon 周二无法参与工作。另外，Devon 做过数据分析工作，Devon 具备安全许可。

哪位候选人满足所有要求？

约束与 violation signature：

- `C1` `has_data_analysis_experience=True`：候选人需要具备数据分析经验。
- `C2` `has_security_clearance=True`：候选人需要具备安全许可。
- `C3` `available_tuesday=True`：候选人需要周二可以参与工作。

- `A` violation: `[]`
- `B` violation: `['C1']`
- `C` violation: `['C2']`
- `D` violation: `['C3']`

## 5. attr_en_000005_zh_view

- source: `attr_en_000005_original`
- scenario: `project_assignment`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `D`

项目团队需要为一项专门任务分配一名成员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要有研究项目经验。
2. 候选人需要周二可以参与工作。
3. 候选人需要能够独立工作。
4. 候选人需要具有本地工作许可。

候选人：
A. Gray 周二可以参与工作，Gray 没有研究项目经历。另外，Gray 能够独立工作，Gray 具有本地工作许可。
B. Avery 参与过研究项目，Avery 不能独立完成工作。另外，Avery 周二可以参与工作，Avery 没有本地工作许可。
C. Blair 具有本地工作许可，Blair 周二无法参与工作。另外，Blair 能够独立工作，Blair 参与过研究项目。
D. Hayden 周二可以参与工作，Hayden 参与过研究项目。另外，Hayden 能够独立工作，Hayden 具有本地工作许可。

哪位候选人适合承担这项任务？

约束与 violation signature：

- `C1` `has_research_experience=True`：候选人需要有研究项目经验。
- `C2` `available_tuesday=True`：候选人需要周二可以参与工作。
- `C3` `can_work_independently=True`：候选人需要能够独立工作。
- `C4` `has_local_work_permit=True`：候选人需要具有本地工作许可。

- `A` violation: `['C1']`
- `B` violation: `['C3', 'C4']`
- `C` violation: `['C2']`
- `D` violation: `[]`

## 6. attr_en_000006_zh_view

- source: `attr_en_000006_original`
- scenario: `expert_recruitment`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `D`

某研究实验室正在为一个新项目选择一名研究人员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要有管理或协调经验。
2. 候选人需要完成过相关培训。
3. 候选人需要了解相关项目领域。
4. 候选人不能存在日程冲突。

候选人：
A. Rowan 完成过相关培训，Rowan 不熟悉相关项目领域。另外，Rowan 不存在日程冲突，Rowan 曾经负责过项目或团队协调。
B. Payton 熟悉相关项目领域，Payton 完成过相关培训。另外，Payton 存在与项目安排冲突的日程，Payton 没有管理或协调项目的经历。
C. Drew 曾经负责过项目或团队协调，Drew 熟悉相关项目领域。另外，Drew 不存在日程冲突，Drew 没有完成相关培训。
D. Tatum 熟悉相关项目领域，Tatum 完成过相关培训。另外，Tatum 不存在日程冲突，Tatum 曾经负责过项目或团队协调。

哪位候选人满足所有要求？

约束与 violation signature：

- `C1` `has_management_experience=True`：候选人需要有管理或协调经验。
- `C2` `has_prior_training=True`：候选人需要完成过相关培训。
- `C3` `has_domain_knowledge=True`：候选人需要了解相关项目领域。
- `C4` `has_schedule_conflict=False`：候选人不能存在日程冲突。

- `A` violation: `['C3']`
- `B` violation: `['C1', 'C4']`
- `C` violation: `['C2']`
- `D` violation: `[]`

## 7. attr_en_000007_zh_view

- source: `attr_en_000007_original`
- scenario: `expert_recruitment`
- option_closeness: `hard`
- structural_complexity: `low`
- gold: `A`

某研究实验室正在为一个新项目选择一名研究人员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人不能存在日程冲突。
2. 候选人需要能够在不需要额外监督的情况下工作。
3. 候选人需要具备质量保证经验。

候选人：
A. Elliot 不需要额外监督也能完成工作。另外，Elliot 有质量保证经验，Elliot 不存在日程冲突。
B. Emerson 有质量保证经验。另外，Emerson 需要额外监督才能完成工作，Emerson 不存在日程冲突。
C. Payton 不需要额外监督也能完成工作。另外，Payton 不存在日程冲突，Payton 没有质量保证经验。
D. Kris 有质量保证经验。另外，Kris 不需要额外监督也能完成工作，Kris 存在与项目安排冲突的日程。

哪位候选人满足所有要求？

约束与 violation signature：

- `C1` `has_schedule_conflict=False`：候选人不能存在日程冲突。
- `C2` `needs_supervision=False`：候选人需要能够在不需要额外监督的情况下工作。
- `C3` `has_quality_assurance_experience=True`：候选人需要具备质量保证经验。

- `A` violation: `[]`
- `B` violation: `['C2']`
- `C` violation: `['C3']`
- `D` violation: `['C1']`

## 8. attr_en_000008_zh_view

- source: `attr_en_000008_original`
- scenario: `project_assignment`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `D`

项目团队需要为一项专门任务分配一名成员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人不能需要额外专用设备支持。
2. 候选人需要具备客户沟通经验。
3. 候选人需要周二可以参与工作。
4. 候选人需要参与过项目执行工作。

候选人：
A. Skyler 周二可以参与工作，Skyler 参与过项目执行。另外，Skyler 没有客户沟通经验，Skyler 不需要额外专用设备支持。
B. Marley 周二可以参与工作，Marley 参与过项目执行。另外，Marley 有客户沟通经验，Marley 需要额外专用设备支持。
C. Ellis 没有参与过项目执行，Ellis 有客户沟通经验。另外，Ellis 周二无法参与工作，Ellis 不需要额外专用设备支持。
D. Devon 不需要额外专用设备支持，Devon 周二可以参与工作。另外，Devon 参与过项目执行，Devon 有客户沟通经验。

哪位候选人适合承担这项任务？

约束与 violation signature：

- `C1` `requires_extra_equipment=False`：候选人不能需要额外专用设备支持。
- `C2` `has_client_communication_experience=True`：候选人需要具备客户沟通经验。
- `C3` `available_tuesday=True`：候选人需要周二可以参与工作。
- `C4` `has_project_experience=True`：候选人需要参与过项目执行工作。

- `A` violation: `['C2']`
- `B` violation: `['C1']`
- `C` violation: `['C3', 'C4']`
- `D` violation: `[]`

## 9. attr_en_000009_zh_view

- source: `attr_en_000009_original`
- scenario: `expert_recruitment`
- option_closeness: `hard`
- structural_complexity: `low`
- gold: `A`

某研究实验室正在为一个新项目选择一名研究人员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要能够独立工作。
2. 候选人需要参与过项目执行工作。
3. 候选人不能存在与项目相关的利益冲突。

候选人：
A. Emerson 参与过项目执行。另外，Emerson 能够独立工作，Emerson 不存在项目相关的利益冲突。
B. Logan 参与过项目执行。另外，Logan 能够独立工作，Logan 与项目存在利益冲突。
C. Jules 不存在项目相关的利益冲突。另外，Jules 没有参与过项目执行，Jules 能够独立工作。
D. Elliot 参与过项目执行。另外，Elliot 不能独立完成工作，Elliot 不存在项目相关的利益冲突。

哪位候选人满足所有要求？

约束与 violation signature：

- `C1` `can_work_independently=True`：候选人需要能够独立工作。
- `C2` `has_project_experience=True`：候选人需要参与过项目执行工作。
- `C3` `has_conflict=False`：候选人不能存在与项目相关的利益冲突。

- `A` violation: `[]`
- `B` violation: `['C3']`
- `C` violation: `['C2']`
- `D` violation: `['C1']`

## 10. attr_en_000010_zh_view

- source: `attr_en_000010_original`
- scenario: `project_assignment`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `A`

项目团队需要为一项专门任务分配一名成员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要能够现场参与工作。
2. 候选人需要上午可以参与工作。
3. 候选人需要具备安全许可。
4. 候选人需要有管理或协调经验。

候选人：
A. Blair 具备安全许可，Blair 曾经负责过项目或团队协调。另外，Blair 能够现场参与工作，Blair 上午可以参与工作。
B. Parker 不能现场参与工作，Parker 曾经负责过项目或团队协调。另外，Parker 上午可以参与工作，Parker 不具备安全许可。
C. Robin 曾经负责过项目或团队协调，Robin 能够现场参与工作。另外，Robin 具备安全许可，Robin 上午无法参与工作。
D. Devon 具备安全许可，Devon 能够现场参与工作。另外，Devon 上午可以参与工作，Devon 没有管理或协调项目的经历。

哪位候选人适合承担这项任务？

约束与 violation signature：

- `C1` `can_work_onsite=True`：候选人需要能够现场参与工作。
- `C2` `available_morning=True`：候选人需要上午可以参与工作。
- `C3` `has_security_clearance=True`：候选人需要具备安全许可。
- `C4` `has_management_experience=True`：候选人需要有管理或协调经验。

- `A` violation: `[]`
- `B` violation: `['C1', 'C3']`
- `C` violation: `['C2']`
- `D` violation: `['C4']`

## 11. attr_en_000011_zh_view

- source: `attr_en_000011_original`
- scenario: `availability_selection`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `B`

协调人需要从四名候选人中找出唯一符合日程和参与要求的人。
被选中的人必须满足以下全部要求：

要求：
1. 候选人不能存在日程冲突。
2. 候选人需要下个月可以加入项目。
3. 候选人需要能够远程工作。
4. 候选人需要能够现场参与工作。

候选人：
A. Gray 不能远程工作，Gray 下个月可以加入项目。另外，Gray 存在与项目安排冲突的日程，Gray 能够现场参与工作。
B. Morgan 下个月可以加入项目，Morgan 不存在日程冲突。另外，Morgan 能够现场参与工作，Morgan 能够远程工作。
C. Kris 能够现场参与工作，Kris 不存在日程冲突。另外，Kris 能够远程工作，Kris 下个月无法加入项目。
D. Riley 能够远程工作，Riley 下个月可以加入项目。另外，Riley 不存在日程冲突，Riley 不能现场参与工作。

哪位候选人符合全部要求？

约束与 violation signature：

- `C1` `has_schedule_conflict=False`：候选人不能存在日程冲突。
- `C2` `available_next_month=True`：候选人需要下个月可以加入项目。
- `C3` `can_work_remote=True`：候选人需要能够远程工作。
- `C4` `can_work_onsite=True`：候选人需要能够现场参与工作。

- `A` violation: `['C1', 'C3']`
- `B` violation: `[]`
- `C` violation: `['C2']`
- `D` violation: `['C4']`

## 12. attr_en_000012_zh_view

- source: `attr_en_000012_original`
- scenario: `availability_selection`
- option_closeness: `hard`
- structural_complexity: `low`
- gold: `B`

协调人需要从四名候选人中找出唯一符合日程和参与要求的人。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要能够现场参与工作。
2. 候选人需要周一可以参与工作。
3. 候选人需要接受灵活工时安排。

候选人：
A. Robin 周一可以参与工作。另外，Robin 不能现场参与工作，Robin 接受灵活工时安排。
B. Emerson 周一可以参与工作。另外，Emerson 接受灵活工时安排，Emerson 能够现场参与工作。
C. Sage 接受灵活工时安排。另外，Sage 能够现场参与工作，Sage 周一无法参与工作。
D. Elliot 周一可以参与工作。另外，Elliot 不接受灵活工时安排，Elliot 能够现场参与工作。

哪位候选人符合全部要求？

约束与 violation signature：

- `C1` `can_work_onsite=True`：候选人需要能够现场参与工作。
- `C2` `available_monday=True`：候选人需要周一可以参与工作。
- `C3` `accepts_flexible_hours=True`：候选人需要接受灵活工时安排。

- `A` violation: `['C1']`
- `B` violation: `[]`
- `C` violation: `['C2']`
- `D` violation: `['C3']`

## 13. attr_en_000013_zh_view

- source: `attr_en_000013_original`
- scenario: `availability_selection`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `C`

协调人需要从四名候选人中找出唯一符合日程和参与要求的人。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要下午可以参与工作。
2. 候选人需要周一可以参与工作。
3. 候选人需要能够现场参与工作。
4. 候选人需要下个月可以加入项目。

候选人：
A. Emerson 周一可以参与工作，Emerson 能够现场参与工作。另外，Emerson 下个月可以加入项目，Emerson 下午无法参与工作。
B. Kris 能够现场参与工作，Kris 下个月无法加入项目。另外，Kris 下午可以参与工作，Kris 周一可以参与工作。
C. Devon 下午可以参与工作，Devon 能够现场参与工作。另外，Devon 周一可以参与工作，Devon 下个月可以加入项目。
D. Taylor 下个月可以加入项目，Taylor 不能现场参与工作。另外，Taylor 下午可以参与工作，Taylor 周一无法参与工作。

哪位候选人符合全部要求？

约束与 violation signature：

- `C1` `available_afternoon=True`：候选人需要下午可以参与工作。
- `C2` `available_monday=True`：候选人需要周一可以参与工作。
- `C3` `can_work_onsite=True`：候选人需要能够现场参与工作。
- `C4` `available_next_month=True`：候选人需要下个月可以加入项目。

- `A` violation: `['C1']`
- `B` violation: `['C4']`
- `C` violation: `[]`
- `D` violation: `['C2', 'C3']`

## 14. attr_en_000014_zh_view

- source: `attr_en_000014_original`
- scenario: `project_assignment`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `C`

项目团队需要为一项专门任务分配一名成员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要周末可以参与工作。
2. 候选人需要具备机器学习经验。
3. 候选人需要上午可以参与工作。
4. 候选人需要能够远程工作。

候选人：
A. Kris 周末无法参与工作，Kris 能够远程工作。另外，Kris 有机器学习项目经验，Kris 上午可以参与工作。
B. Milan 没有机器学习方面的实践经验，Milan 上午可以参与工作。另外，Milan 能够远程工作，Milan 周末可以参与工作。
C. Finley 能够远程工作，Finley 有机器学习项目经验。另外，Finley 上午可以参与工作，Finley 周末可以参与工作。
D. Casey 有机器学习项目经验，Casey 周末可以参与工作。另外，Casey 不能远程工作，Casey 上午无法参与工作。

哪位候选人适合承担这项任务？

约束与 violation signature：

- `C1` `available_weekend=True`：候选人需要周末可以参与工作。
- `C2` `has_ml_experience=True`：候选人需要具备机器学习经验。
- `C3` `available_morning=True`：候选人需要上午可以参与工作。
- `C4` `can_work_remote=True`：候选人需要能够远程工作。

- `A` violation: `['C1']`
- `B` violation: `['C2']`
- `C` violation: `[]`
- `D` violation: `['C3', 'C4']`

## 15. attr_en_000015_zh_view

- source: `attr_en_000015_original`
- scenario: `project_assignment`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `A`

项目团队需要为一项专门任务分配一名成员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要上午可以参与工作。
2. 候选人需要能够独立工作。
3. 候选人需要周二可以参与工作。
4. 候选人需要具备客户沟通经验。

候选人：
A. Emerson 有客户沟通经验，Emerson 能够独立工作。另外，Emerson 上午可以参与工作，Emerson 周二可以参与工作。
B. Briar 周二可以参与工作，Briar 没有客户沟通经验。另外，Briar 上午可以参与工作，Briar 能够独立工作。
C. Riley 有客户沟通经验，Riley 不能独立完成工作。另外，Riley 上午无法参与工作，Riley 周二可以参与工作。
D. Jordan 有客户沟通经验，Jordan 周二无法参与工作。另外，Jordan 上午可以参与工作，Jordan 能够独立工作。

哪位候选人适合承担这项任务？

约束与 violation signature：

- `C1` `available_morning=True`：候选人需要上午可以参与工作。
- `C2` `can_work_independently=True`：候选人需要能够独立工作。
- `C3` `available_tuesday=True`：候选人需要周二可以参与工作。
- `C4` `has_client_communication_experience=True`：候选人需要具备客户沟通经验。

- `A` violation: `[]`
- `B` violation: `['C4']`
- `C` violation: `['C1', 'C2']`
- `D` violation: `['C3']`

## 16. attr_en_000016_zh_view

- source: `attr_en_000016_original`
- scenario: `expert_recruitment`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `C`

某研究实验室正在为一个新项目选择一名研究人员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要具备团队协作经验。
2. 候选人需要上午可以参与工作。
3. 候选人需要具备安全许可。
4. 候选人需要具备质量保证经验。

候选人：
A. Casey 上午可以参与工作，Casey 具备安全许可。另外，Casey 没有质量保证经验，Casey 有团队协作经验。
B. Rowan 缺少团队协作经验，Rowan 不具备安全许可。另外，Rowan 上午可以参与工作，Rowan 有质量保证经验。
C. Blair 有团队协作经验，Blair 具备安全许可。另外，Blair 上午可以参与工作，Blair 有质量保证经验。
D. Ellis 具备安全许可，Ellis 有质量保证经验。另外，Ellis 上午无法参与工作，Ellis 有团队协作经验。

哪位候选人满足所有要求？

约束与 violation signature：

- `C1` `has_teamwork_experience=True`：候选人需要具备团队协作经验。
- `C2` `available_morning=True`：候选人需要上午可以参与工作。
- `C3` `has_security_clearance=True`：候选人需要具备安全许可。
- `C4` `has_quality_assurance_experience=True`：候选人需要具备质量保证经验。

- `A` violation: `['C4']`
- `B` violation: `['C1', 'C3']`
- `C` violation: `[]`
- `D` violation: `['C2']`

## 17. attr_en_000017_zh_view

- source: `attr_en_000017_original`
- scenario: `availability_selection`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `A`

协调人需要从四名候选人中找出唯一符合日程和参与要求的人。
被选中的人必须满足以下全部要求：

要求：
1. 候选人不能需要额外专用设备支持。
2. 候选人需要接受灵活工时安排。
3. 候选人不能存在日程冲突。
4. 候选人需要下午可以参与工作。

候选人：
A. Rowan 下午可以参与工作，Rowan 接受灵活工时安排。另外，Rowan 不需要额外专用设备支持，Rowan 不存在日程冲突。
B. Logan 下午无法参与工作，Logan 不接受灵活工时安排。另外，Logan 不需要额外专用设备支持，Logan 不存在日程冲突。
C. Blair 接受灵活工时安排，Blair 不需要额外专用设备支持。另外，Blair 存在与项目安排冲突的日程，Blair 下午可以参与工作。
D. Briar 不存在日程冲突，Briar 需要额外专用设备支持。另外，Briar 接受灵活工时安排，Briar 下午可以参与工作。

哪位候选人符合全部要求？

约束与 violation signature：

- `C1` `requires_extra_equipment=False`：候选人不能需要额外专用设备支持。
- `C2` `accepts_flexible_hours=True`：候选人需要接受灵活工时安排。
- `C3` `has_schedule_conflict=False`：候选人不能存在日程冲突。
- `C4` `available_afternoon=True`：候选人需要下午可以参与工作。

- `A` violation: `[]`
- `B` violation: `['C2', 'C4']`
- `C` violation: `['C3']`
- `D` violation: `['C1']`

## 18. attr_en_000018_zh_view

- source: `attr_en_000018_original`
- scenario: `availability_selection`
- option_closeness: `medium`
- structural_complexity: `low`
- gold: `B`

协调人需要从四名候选人中找出唯一符合日程和参与要求的人。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要能够现场参与工作。
2. 候选人需要能够远程工作。
3. 候选人需要周末可以参与工作。

候选人：
A. Jamie 周末可以参与工作。另外，Jamie 能够现场参与工作，Jamie 不能远程工作。
B. Emerson 能够远程工作。另外，Emerson 能够现场参与工作，Emerson 周末可以参与工作。
C. Ellis 不能远程工作。另外，Ellis 不能现场参与工作，Ellis 周末可以参与工作。
D. Elliot 能够现场参与工作。另外，Elliot 周末无法参与工作，Elliot 能够远程工作。

哪位候选人符合全部要求？

约束与 violation signature：

- `C1` `can_work_onsite=True`：候选人需要能够现场参与工作。
- `C2` `can_work_remote=True`：候选人需要能够远程工作。
- `C3` `available_weekend=True`：候选人需要周末可以参与工作。

- `A` violation: `['C2']`
- `B` violation: `[]`
- `C` violation: `['C1', 'C2']`
- `D` violation: `['C3']`

## 19. attr_en_000019_zh_view

- source: `attr_en_000019_original`
- scenario: `expert_recruitment`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `C`

某研究实验室正在为一个新项目选择一名研究人员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要有研究项目经验。
2. 候选人需要持有相关证书。
3. 候选人需要能够独立工作。
4. 候选人需要具备团队协作经验。

候选人：
A. Milan 没有相关专业证书，Milan 参与过研究项目。另外，Milan 能够独立工作，Milan 有团队协作经验。
B. Rowan 能够独立工作，Rowan 缺少团队协作经验。另外，Rowan 持有相关专业证书，Rowan 没有研究项目经历。
C. Kris 能够独立工作，Kris 持有相关专业证书。另外，Kris 参与过研究项目，Kris 有团队协作经验。
D. Gray 持有相关专业证书，Gray 有团队协作经验。另外，Gray 参与过研究项目，Gray 不能独立完成工作。

哪位候选人满足所有要求？

约束与 violation signature：

- `C1` `has_research_experience=True`：候选人需要有研究项目经验。
- `C2` `has_certificate=True`：候选人需要持有相关证书。
- `C3` `can_work_independently=True`：候选人需要能够独立工作。
- `C4` `has_teamwork_experience=True`：候选人需要具备团队协作经验。

- `A` violation: `['C2']`
- `B` violation: `['C1', 'C4']`
- `C` violation: `[]`
- `D` violation: `['C3']`

## 20. attr_en_000020_zh_view

- source: `attr_en_000020_original`
- scenario: `expert_recruitment`
- option_closeness: `easy`
- structural_complexity: `high`
- gold: `D`

某研究实验室正在为一个新项目选择一名研究人员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要周一可以参与工作。
2. 候选人需要具备质量保证经验。
3. 候选人需要有管理或协调经验。
4. 候选人需要完成过相关培训。
5. 候选人需要具备编程经验。

候选人：
A. Wren 周一无法参与工作，Wren 没有管理或协调项目的经历。另外，Wren 没有处理过编程任务，Wren 完成过相关培训，Wren 没有质量保证经验。
B. Quinn 周一无法参与工作，Quinn 有实际编程经验。另外，Quinn 曾经负责过项目或团队协调，Quinn 没有质量保证经验，Quinn 完成过相关培训。
C. Blair 周一可以参与工作，Blair 没有管理或协调项目的经历。另外，Blair 有质量保证经验，Blair 有实际编程经验，Blair 没有完成相关培训。
D. Jules 有质量保证经验，Jules 曾经负责过项目或团队协调。另外，Jules 有实际编程经验，Jules 周一可以参与工作，Jules 完成过相关培训。

哪位候选人满足所有要求？

约束与 violation signature：

- `C1` `available_monday=True`：候选人需要周一可以参与工作。
- `C2` `has_quality_assurance_experience=True`：候选人需要具备质量保证经验。
- `C3` `has_management_experience=True`：候选人需要有管理或协调经验。
- `C4` `has_prior_training=True`：候选人需要完成过相关培训。
- `C5` `has_programming_experience=True`：候选人需要具备编程经验。

- `A` violation: `['C1', 'C2', 'C3', 'C5']`
- `B` violation: `['C1', 'C2']`
- `C` violation: `['C3', 'C4']`
- `D` violation: `[]`

## 21. attr_en_000021_zh_view

- source: `attr_en_000021_original`
- scenario: `project_assignment`
- option_closeness: `easy`
- structural_complexity: `high`
- gold: `A`

项目团队需要为一项专门任务分配一名成员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人不能存在日程冲突。
2. 候选人需要下个月可以加入项目。
3. 候选人需要具备团队协作经验。
4. 候选人需要了解相关项目领域。
5. 候选人需要具有本地工作许可。

候选人：
A. Ellis 具有本地工作许可，Ellis 有团队协作经验。另外，Ellis 熟悉相关项目领域，Ellis 不存在日程冲突，Ellis 下个月可以加入项目。
B. Taylor 缺少团队协作经验，Taylor 下个月可以加入项目。另外，Taylor 熟悉相关项目领域，Taylor 存在与项目安排冲突的日程，Taylor 具有本地工作许可。
C. Parker 没有本地工作许可，Parker 缺少团队协作经验。另外，Parker 不存在日程冲突，Parker 熟悉相关项目领域，Parker 下个月可以加入项目。
D. Finley 不熟悉相关项目领域，Finley 有团队协作经验。另外，Finley 不存在日程冲突，Finley 没有本地工作许可，Finley 下个月无法加入项目。

哪位候选人适合承担这项任务？

约束与 violation signature：

- `C1` `has_schedule_conflict=False`：候选人不能存在日程冲突。
- `C2` `available_next_month=True`：候选人需要下个月可以加入项目。
- `C3` `has_teamwork_experience=True`：候选人需要具备团队协作经验。
- `C4` `has_domain_knowledge=True`：候选人需要了解相关项目领域。
- `C5` `has_local_work_permit=True`：候选人需要具有本地工作许可。

- `A` violation: `[]`
- `B` violation: `['C1', 'C3']`
- `C` violation: `['C3', 'C5']`
- `D` violation: `['C2', 'C4', 'C5']`

## 22. attr_en_000022_zh_view

- source: `attr_en_000022_original`
- scenario: `availability_selection`
- option_closeness: `easy`
- structural_complexity: `high`
- gold: `C`

协调人需要从四名候选人中找出唯一符合日程和参与要求的人。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要周一可以参与工作。
2. 候选人需要能够远程工作。
3. 候选人需要能够现场参与工作。
4. 候选人需要周二可以参与工作。
5. 候选人需要接受灵活工时安排。

候选人：
A. Hayden 不能远程工作，Hayden 周二可以参与工作。另外，Hayden 周一可以参与工作，Hayden 能够现场参与工作，Hayden 不接受灵活工时安排。
B. Skyler 周一无法参与工作，Skyler 不接受灵活工时安排。另外，Skyler 不能远程工作，Skyler 周二无法参与工作，Skyler 不能现场参与工作。
C. Sage 周二可以参与工作，Sage 能够现场参与工作。另外，Sage 周一可以参与工作，Sage 接受灵活工时安排，Sage 能够远程工作。
D. Arden 周二无法参与工作，Arden 能够远程工作。另外，Arden 接受灵活工时安排，Arden 周一可以参与工作，Arden 不能现场参与工作。

哪位候选人符合全部要求？

约束与 violation signature：

- `C1` `available_monday=True`：候选人需要周一可以参与工作。
- `C2` `can_work_remote=True`：候选人需要能够远程工作。
- `C3` `can_work_onsite=True`：候选人需要能够现场参与工作。
- `C4` `available_tuesday=True`：候选人需要周二可以参与工作。
- `C5` `accepts_flexible_hours=True`：候选人需要接受灵活工时安排。

- `A` violation: `['C2', 'C5']`
- `B` violation: `['C1', 'C2', 'C3', 'C4', 'C5']`
- `C` violation: `[]`
- `D` violation: `['C3', 'C4']`

## 23. attr_en_000023_zh_view

- source: `attr_en_000023_original`
- scenario: `expert_recruitment`
- option_closeness: `easy`
- structural_complexity: `high`
- gold: `C`

某研究实验室正在为一个新项目选择一名研究人员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要周二可以参与工作。
2. 候选人需要持有相关证书。
3. 候选人需要下个月可以加入项目。
4. 候选人需要有研究项目经验。
5. 候选人需要参与过项目执行工作。

候选人：
A. Cameron 没有相关专业证书，Cameron 下个月无法加入项目。另外，Cameron 周二可以参与工作，Cameron 参与过研究项目，Cameron 参与过项目执行。
B. Ellis 周二无法参与工作，Ellis 下个月可以加入项目。另外，Ellis 没有相关专业证书，Ellis 参与过项目执行，Ellis 参与过研究项目。
C. Blair 参与过研究项目，Blair 下个月可以加入项目。另外，Blair 持有相关专业证书，Blair 周二可以参与工作，Blair 参与过项目执行。
D. Taylor 周二无法参与工作，Taylor 没有参与过项目执行。另外，Taylor 下个月无法加入项目，Taylor 没有研究项目经历，Taylor 没有相关专业证书。

哪位候选人满足所有要求？

约束与 violation signature：

- `C1` `available_tuesday=True`：候选人需要周二可以参与工作。
- `C2` `has_certificate=True`：候选人需要持有相关证书。
- `C3` `available_next_month=True`：候选人需要下个月可以加入项目。
- `C4` `has_research_experience=True`：候选人需要有研究项目经验。
- `C5` `has_project_experience=True`：候选人需要参与过项目执行工作。

- `A` violation: `['C2', 'C3']`
- `B` violation: `['C1', 'C2']`
- `C` violation: `[]`
- `D` violation: `['C1', 'C2', 'C3', 'C4', 'C5']`

## 24. attr_en_000024_zh_view

- source: `attr_en_000024_original`
- scenario: `project_assignment`
- option_closeness: `medium`
- structural_complexity: `low`
- gold: `D`

项目团队需要为一项专门任务分配一名成员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要能够独立工作。
2. 候选人需要具备安全许可。
3. 候选人需要能够远程工作。

候选人：
A. Hayden 具备安全许可。另外，Hayden 不能远程工作，Hayden 能够独立工作。
B. Jordan 能够远程工作。另外，Jordan 不能独立完成工作，Jordan 具备安全许可。
C. Riley 能够远程工作。另外，Riley 不具备安全许可，Riley 不能独立完成工作。
D. Sawyer 具备安全许可。另外，Sawyer 能够远程工作，Sawyer 能够独立工作。

哪位候选人适合承担这项任务？

约束与 violation signature：

- `C1` `can_work_independently=True`：候选人需要能够独立工作。
- `C2` `has_security_clearance=True`：候选人需要具备安全许可。
- `C3` `can_work_remote=True`：候选人需要能够远程工作。

- `A` violation: `['C3']`
- `B` violation: `['C1']`
- `C` violation: `['C1', 'C2']`
- `D` violation: `[]`

## 25. attr_en_000025_zh_view

- source: `attr_en_000025_original`
- scenario: `availability_selection`
- option_closeness: `medium`
- structural_complexity: `low`
- gold: `B`

协调人需要从四名候选人中找出唯一符合日程和参与要求的人。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要周一可以参与工作。
2. 候选人需要上午可以参与工作。
3. 候选人需要下个月可以加入项目。

候选人：
A. Harper 上午可以参与工作。另外，Harper 下个月无法加入项目，Harper 周一可以参与工作。
B. Casey 上午可以参与工作。另外，Casey 周一可以参与工作，Casey 下个月可以加入项目。
C. Devon 周一无法参与工作。另外，Devon 下个月可以加入项目，Devon 上午无法参与工作。
D. Marley 下个月可以加入项目。另外，Marley 周一可以参与工作，Marley 上午无法参与工作。

哪位候选人符合全部要求？

约束与 violation signature：

- `C1` `available_monday=True`：候选人需要周一可以参与工作。
- `C2` `available_morning=True`：候选人需要上午可以参与工作。
- `C3` `available_next_month=True`：候选人需要下个月可以加入项目。

- `A` violation: `['C3']`
- `B` violation: `[]`
- `C` violation: `['C1', 'C2']`
- `D` violation: `['C2']`

## 26. attr_en_000026_zh_view

- source: `attr_en_000026_original`
- scenario: `availability_selection`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `A`

协调人需要从四名候选人中找出唯一符合日程和参与要求的人。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要周末可以参与工作。
2. 候选人需要周二可以参与工作。
3. 候选人需要能够现场参与工作。
4. 候选人需要周一可以参与工作。

候选人：
A. Marley 能够现场参与工作，Marley 周末可以参与工作。另外，Marley 周二可以参与工作，Marley 周一可以参与工作。
B. Arden 周一可以参与工作，Arden 周二无法参与工作。另外，Arden 能够现场参与工作，Arden 周末无法参与工作。
C. Tatum 周末可以参与工作，Tatum 周一可以参与工作。另外，Tatum 周二可以参与工作，Tatum 不能现场参与工作。
D. Drew 周一无法参与工作，Drew 周末可以参与工作。另外，Drew 能够现场参与工作，Drew 周二可以参与工作。

哪位候选人符合全部要求？

约束与 violation signature：

- `C1` `available_weekend=True`：候选人需要周末可以参与工作。
- `C2` `available_tuesday=True`：候选人需要周二可以参与工作。
- `C3` `can_work_onsite=True`：候选人需要能够现场参与工作。
- `C4` `available_monday=True`：候选人需要周一可以参与工作。

- `A` violation: `[]`
- `B` violation: `['C1', 'C2']`
- `C` violation: `['C3']`
- `D` violation: `['C4']`

## 27. attr_en_000027_zh_view

- source: `attr_en_000027_original`
- scenario: `expert_recruitment`
- option_closeness: `medium`
- structural_complexity: `low`
- gold: `C`

某研究实验室正在为一个新项目选择一名研究人员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要熟悉统计方法。
2. 候选人需要持有相关证书。
3. 候选人需要下午可以参与工作。

候选人：
A. Gray 熟悉统计方法。另外，Gray 下午无法参与工作，Gray 持有相关专业证书。
B. Skyler 下午可以参与工作。另外，Skyler 持有相关专业证书，Skyler 不熟悉统计方法。
C. Sawyer 持有相关专业证书。另外，Sawyer 下午可以参与工作，Sawyer 熟悉统计方法。
D. Noel 下午无法参与工作。另外，Noel 熟悉统计方法，Noel 没有相关专业证书。

哪位候选人满足所有要求？

约束与 violation signature：

- `C1` `familiar_with_statistics=True`：候选人需要熟悉统计方法。
- `C2` `has_certificate=True`：候选人需要持有相关证书。
- `C3` `available_afternoon=True`：候选人需要下午可以参与工作。

- `A` violation: `['C3']`
- `B` violation: `['C1']`
- `C` violation: `[]`
- `D` violation: `['C2', 'C3']`

## 28. attr_en_000028_zh_view

- source: `attr_en_000028_original`
- scenario: `availability_selection`
- option_closeness: `easy`
- structural_complexity: `high`
- gold: `D`

协调人需要从四名候选人中找出唯一符合日程和参与要求的人。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要能够远程工作。
2. 候选人需要上午可以参与工作。
3. 候选人需要周二可以参与工作。
4. 候选人需要下午可以参与工作。
5. 候选人需要周末可以参与工作。

候选人：
A. Indigo 周二无法参与工作，Indigo 下午无法参与工作。另外，Indigo 上午无法参与工作，Indigo 能够远程工作，Indigo 周末无法参与工作。
B. Devon 上午可以参与工作，Devon 不能远程工作。另外，Devon 周末可以参与工作，Devon 周二无法参与工作，Devon 下午可以参与工作。
C. Tatum 上午无法参与工作，Tatum 下午可以参与工作。另外，Tatum 不能远程工作，Tatum 周二可以参与工作，Tatum 周末可以参与工作。
D. Sage 上午可以参与工作，Sage 能够远程工作。另外，Sage 下午可以参与工作，Sage 周末可以参与工作，Sage 周二可以参与工作。

哪位候选人符合全部要求？

约束与 violation signature：

- `C1` `can_work_remote=True`：候选人需要能够远程工作。
- `C2` `available_morning=True`：候选人需要上午可以参与工作。
- `C3` `available_tuesday=True`：候选人需要周二可以参与工作。
- `C4` `available_afternoon=True`：候选人需要下午可以参与工作。
- `C5` `available_weekend=True`：候选人需要周末可以参与工作。

- `A` violation: `['C2', 'C3', 'C4', 'C5']`
- `B` violation: `['C1', 'C3']`
- `C` violation: `['C1', 'C2']`
- `D` violation: `[]`

## 29. attr_en_000029_zh_view

- source: `attr_en_000029_original`
- scenario: `expert_recruitment`
- option_closeness: `medium`
- structural_complexity: `low`
- gold: `D`

某研究实验室正在为一个新项目选择一名研究人员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要具备安全许可。
2. 候选人需要具备客户沟通经验。
3. 候选人需要具备编程经验。

候选人：
A. Arden 没有客户沟通经验。另外，Arden 有实际编程经验，Arden 具备安全许可。
B. Drew 有实际编程经验。另外，Drew 不具备安全许可，Drew 没有客户沟通经验。
C. Robin 有客户沟通经验。另外，Robin 具备安全许可，Robin 没有处理过编程任务。
D. Tatum 有实际编程经验。另外，Tatum 具备安全许可，Tatum 有客户沟通经验。

哪位候选人满足所有要求？

约束与 violation signature：

- `C1` `has_security_clearance=True`：候选人需要具备安全许可。
- `C2` `has_client_communication_experience=True`：候选人需要具备客户沟通经验。
- `C3` `has_programming_experience=True`：候选人需要具备编程经验。

- `A` violation: `['C2']`
- `B` violation: `['C1', 'C2']`
- `C` violation: `['C3']`
- `D` violation: `[]`

## 30. attr_en_000030_zh_view

- source: `attr_en_000030_original`
- scenario: `project_assignment`
- option_closeness: `easy`
- structural_complexity: `high`
- gold: `C`

项目团队需要为一项专门任务分配一名成员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要能够独立工作。
2. 候选人需要具有本地工作许可。
3. 候选人需要有公开表达或演讲经验。
4. 候选人需要能够现场参与工作。
5. 候选人需要参与过项目执行工作。

候选人：
A. Quinn 没有本地工作许可，Quinn 能够独立工作。另外，Quinn 参与过项目执行，Quinn 不能现场参与工作，Quinn 有公开表达或演讲经验。
B. Tatum 没有公开表达或演讲经验，Tatum 没有本地工作许可。另外，Tatum 没有参与过项目执行，Tatum 能够现场参与工作，Tatum 不能独立完成工作。
C. Jamie 参与过项目执行，Jamie 能够现场参与工作。另外，Jamie 具有本地工作许可，Jamie 有公开表达或演讲经验，Jamie 能够独立工作。
D. Casey 参与过项目执行，Casey 没有公开表达或演讲经验。另外，Casey 能够独立工作，Casey 没有本地工作许可，Casey 能够现场参与工作。

哪位候选人适合承担这项任务？

约束与 violation signature：

- `C1` `can_work_independently=True`：候选人需要能够独立工作。
- `C2` `has_local_work_permit=True`：候选人需要具有本地工作许可。
- `C3` `has_public_speaking_experience=True`：候选人需要有公开表达或演讲经验。
- `C4` `can_work_onsite=True`：候选人需要能够现场参与工作。
- `C5` `has_project_experience=True`：候选人需要参与过项目执行工作。

- `A` violation: `['C2', 'C4']`
- `B` violation: `['C1', 'C2', 'C3', 'C5']`
- `C` violation: `[]`
- `D` violation: `['C2', 'C3']`

## 31. attr_en_000031_zh_view

- source: `attr_en_000031_original`
- scenario: `project_assignment`
- option_closeness: `hard`
- structural_complexity: `low`
- gold: `B`

项目团队需要为一项专门任务分配一名成员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要具备质量保证经验。
2. 候选人需要愿意出差。
3. 候选人需要能够使用英语进行工作沟通。

候选人：
A. Indigo 不愿意出差。另外，Indigo 有质量保证经验，Indigo 能够用英语进行工作沟通。
B. Harper 能够用英语进行工作沟通。另外，Harper 愿意出差，Harper 有质量保证经验。
C. Gray 不能用英语进行工作沟通。另外，Gray 愿意出差，Gray 有质量保证经验。
D. Taylor 能够用英语进行工作沟通。另外，Taylor 没有质量保证经验，Taylor 愿意出差。

哪位候选人适合承担这项任务？

约束与 violation signature：

- `C1` `has_quality_assurance_experience=True`：候选人需要具备质量保证经验。
- `C2` `willing_to_travel=True`：候选人需要愿意出差。
- `C3` `speaks_english=True`：候选人需要能够使用英语进行工作沟通。

- `A` violation: `['C2']`
- `B` violation: `[]`
- `C` violation: `['C3']`
- `D` violation: `['C1']`

## 32. attr_en_000032_zh_view

- source: `attr_en_000032_original`
- scenario: `project_assignment`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `A`

项目团队需要为一项专门任务分配一名成员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要能够在不需要额外监督的情况下工作。
2. 候选人需要了解相关项目领域。
3. 候选人需要有管理或协调经验。
4. 候选人不能存在日程冲突。

候选人：
A. Robin 曾经负责过项目或团队协调，Robin 不需要额外监督也能完成工作。另外，Robin 熟悉相关项目领域，Robin 不存在日程冲突。
B. Elliot 不熟悉相关项目领域，Elliot 曾经负责过项目或团队协调。另外，Elliot 不需要额外监督也能完成工作，Elliot 不存在日程冲突。
C. Casey 不需要额外监督也能完成工作，Casey 存在与项目安排冲突的日程。另外，Casey 熟悉相关项目领域，Casey 曾经负责过项目或团队协调。
D. Skyler 熟悉相关项目领域，Skyler 没有管理或协调项目的经历。另外，Skyler 不存在日程冲突，Skyler 需要额外监督才能完成工作。

哪位候选人适合承担这项任务？

约束与 violation signature：

- `C1` `needs_supervision=False`：候选人需要能够在不需要额外监督的情况下工作。
- `C2` `has_domain_knowledge=True`：候选人需要了解相关项目领域。
- `C3` `has_management_experience=True`：候选人需要有管理或协调经验。
- `C4` `has_schedule_conflict=False`：候选人不能存在日程冲突。

- `A` violation: `[]`
- `B` violation: `['C2']`
- `C` violation: `['C4']`
- `D` violation: `['C1', 'C3']`

## 33. attr_en_000033_zh_view

- source: `attr_en_000033_original`
- scenario: `project_assignment`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `D`

项目团队需要为一项专门任务分配一名成员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要熟悉统计方法。
2. 候选人需要周一可以参与工作。
3. 候选人需要能够在不需要额外监督的情况下工作。
4. 候选人不能需要额外专用设备支持。

候选人：
A. Milan 不需要额外监督也能完成工作，Milan 周一可以参与工作。另外，Milan 不熟悉统计方法，Milan 不需要额外专用设备支持。
B. Parker 需要额外专用设备支持，Parker 周一可以参与工作。另外，Parker 需要额外监督才能完成工作，Parker 熟悉统计方法。
C. Jules 不需要额外专用设备支持，Jules 熟悉统计方法。另外，Jules 周一无法参与工作，Jules 不需要额外监督也能完成工作。
D. Skyler 熟悉统计方法，Skyler 不需要额外专用设备支持。另外，Skyler 不需要额外监督也能完成工作，Skyler 周一可以参与工作。

哪位候选人适合承担这项任务？

约束与 violation signature：

- `C1` `familiar_with_statistics=True`：候选人需要熟悉统计方法。
- `C2` `available_monday=True`：候选人需要周一可以参与工作。
- `C3` `needs_supervision=False`：候选人需要能够在不需要额外监督的情况下工作。
- `C4` `requires_extra_equipment=False`：候选人不能需要额外专用设备支持。

- `A` violation: `['C1']`
- `B` violation: `['C3', 'C4']`
- `C` violation: `['C2']`
- `D` violation: `[]`

## 34. attr_en_000034_zh_view

- source: `attr_en_000034_original`
- scenario: `expert_recruitment`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `C`

某研究实验室正在为一个新项目选择一名研究人员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要有研究项目经验。
2. 候选人需要下午可以参与工作。
3. 候选人需要上午可以参与工作。
4. 候选人需要参与过项目执行工作。

候选人：
A. Harper 下午可以参与工作，Harper 参与过研究项目。另外，Harper 没有参与过项目执行，Harper 上午可以参与工作。
B. Drew 没有研究项目经历，Drew 下午可以参与工作。另外，Drew 参与过项目执行，Drew 上午可以参与工作。
C. Robin 参与过项目执行，Robin 上午可以参与工作。另外，Robin 下午可以参与工作，Robin 参与过研究项目。
D. Sawyer 上午无法参与工作，Sawyer 参与过项目执行。另外，Sawyer 下午无法参与工作，Sawyer 参与过研究项目。

哪位候选人满足所有要求？

约束与 violation signature：

- `C1` `has_research_experience=True`：候选人需要有研究项目经验。
- `C2` `available_afternoon=True`：候选人需要下午可以参与工作。
- `C3` `available_morning=True`：候选人需要上午可以参与工作。
- `C4` `has_project_experience=True`：候选人需要参与过项目执行工作。

- `A` violation: `['C4']`
- `B` violation: `['C1']`
- `C` violation: `[]`
- `D` violation: `['C2', 'C3']`

## 35. attr_en_000035_zh_view

- source: `attr_en_000035_original`
- scenario: `expert_recruitment`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `B`

某研究实验室正在为一个新项目选择一名研究人员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要具备安全许可。
2. 候选人需要上午可以参与工作。
3. 候选人需要能够在不需要额外监督的情况下工作。
4. 候选人需要下个月可以加入项目。

候选人：
A. Wren 上午无法参与工作，Wren 具备安全许可。另外，Wren 不需要额外监督也能完成工作，Wren 下个月可以加入项目。
B. Tatum 不需要额外监督也能完成工作，Tatum 上午可以参与工作。另外，Tatum 具备安全许可，Tatum 下个月可以加入项目。
C. Jules 需要额外监督才能完成工作，Jules 下个月可以加入项目。另外，Jules 不具备安全许可，Jules 上午可以参与工作。
D. Morgan 具备安全许可，Morgan 不需要额外监督也能完成工作。另外，Morgan 下个月无法加入项目，Morgan 上午可以参与工作。

哪位候选人满足所有要求？

约束与 violation signature：

- `C1` `has_security_clearance=True`：候选人需要具备安全许可。
- `C2` `available_morning=True`：候选人需要上午可以参与工作。
- `C3` `needs_supervision=False`：候选人需要能够在不需要额外监督的情况下工作。
- `C4` `available_next_month=True`：候选人需要下个月可以加入项目。

- `A` violation: `['C2']`
- `B` violation: `[]`
- `C` violation: `['C1', 'C3']`
- `D` violation: `['C4']`

## 36. attr_en_000036_zh_view

- source: `attr_en_000036_original`
- scenario: `expert_recruitment`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `D`

某研究实验室正在为一个新项目选择一名研究人员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要熟悉统计方法。
2. 候选人需要具备团队协作经验。
3. 候选人需要参与过项目执行工作。
4. 候选人需要能够在不需要额外监督的情况下工作。

候选人：
A. Drew 不需要额外监督也能完成工作，Drew 不熟悉统计方法。另外，Drew 有团队协作经验，Drew 参与过项目执行。
B. Kris 熟悉统计方法，Kris 不需要额外监督也能完成工作。另外，Kris 没有参与过项目执行，Kris 缺少团队协作经验。
C. Sawyer 有团队协作经验，Sawyer 参与过项目执行。另外，Sawyer 需要额外监督才能完成工作，Sawyer 熟悉统计方法。
D. Parker 不需要额外监督也能完成工作，Parker 熟悉统计方法。另外，Parker 有团队协作经验，Parker 参与过项目执行。

哪位候选人满足所有要求？

约束与 violation signature：

- `C1` `familiar_with_statistics=True`：候选人需要熟悉统计方法。
- `C2` `has_teamwork_experience=True`：候选人需要具备团队协作经验。
- `C3` `has_project_experience=True`：候选人需要参与过项目执行工作。
- `C4` `needs_supervision=False`：候选人需要能够在不需要额外监督的情况下工作。

- `A` violation: `['C1']`
- `B` violation: `['C2', 'C3']`
- `C` violation: `['C4']`
- `D` violation: `[]`

## 37. attr_en_000037_zh_view

- source: `attr_en_000037_original`
- scenario: `project_assignment`
- option_closeness: `medium`
- structural_complexity: `low`
- gold: `B`

项目团队需要为一项专门任务分配一名成员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要具备机器学习经验。
2. 候选人需要接受灵活工时安排。
3. 候选人需要具备团队协作经验。

候选人：
A. Gray 缺少团队协作经验。另外，Gray 不接受灵活工时安排，Gray 有机器学习项目经验。
B. Arden 接受灵活工时安排。另外，Arden 有机器学习项目经验，Arden 有团队协作经验。
C. Robin 不接受灵活工时安排。另外，Robin 有团队协作经验，Robin 有机器学习项目经验。
D. Jamie 有团队协作经验。另外，Jamie 接受灵活工时安排，Jamie 没有机器学习方面的实践经验。

哪位候选人适合承担这项任务？

约束与 violation signature：

- `C1` `has_ml_experience=True`：候选人需要具备机器学习经验。
- `C2` `accepts_flexible_hours=True`：候选人需要接受灵活工时安排。
- `C3` `has_teamwork_experience=True`：候选人需要具备团队协作经验。

- `A` violation: `['C2', 'C3']`
- `B` violation: `[]`
- `C` violation: `['C2']`
- `D` violation: `['C1']`

## 38. attr_en_000038_zh_view

- source: `attr_en_000038_original`
- scenario: `availability_selection`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `D`

协调人需要从四名候选人中找出唯一符合日程和参与要求的人。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要接受灵活工时安排。
2. 候选人不能需要额外专用设备支持。
3. 候选人需要上午可以参与工作。
4. 候选人不能存在日程冲突。

候选人：
A. Logan 接受灵活工时安排，Logan 上午可以参与工作。另外，Logan 需要额外专用设备支持，Logan 不存在日程冲突。
B. Jamie 不接受灵活工时安排，Jamie 上午可以参与工作。另外，Jamie 不存在日程冲突，Jamie 不需要额外专用设备支持。
C. Gray 上午无法参与工作，Gray 接受灵活工时安排。另外，Gray 不需要额外专用设备支持，Gray 存在与项目安排冲突的日程。
D. Sawyer 不需要额外专用设备支持，Sawyer 接受灵活工时安排。另外，Sawyer 上午可以参与工作，Sawyer 不存在日程冲突。

哪位候选人符合全部要求？

约束与 violation signature：

- `C1` `accepts_flexible_hours=True`：候选人需要接受灵活工时安排。
- `C2` `requires_extra_equipment=False`：候选人不能需要额外专用设备支持。
- `C3` `available_morning=True`：候选人需要上午可以参与工作。
- `C4` `has_schedule_conflict=False`：候选人不能存在日程冲突。

- `A` violation: `['C2']`
- `B` violation: `['C1']`
- `C` violation: `['C3', 'C4']`
- `D` violation: `[]`

## 39. attr_en_000039_zh_view

- source: `attr_en_000039_original`
- scenario: `availability_selection`
- option_closeness: `medium`
- structural_complexity: `low`
- gold: `B`

协调人需要从四名候选人中找出唯一符合日程和参与要求的人。
被选中的人必须满足以下全部要求：

要求：
1. 候选人不能存在日程冲突。
2. 候选人不能需要额外专用设备支持。
3. 候选人需要下个月可以加入项目。

候选人：
A. Quinn 不需要额外专用设备支持。另外，Quinn 存在与项目安排冲突的日程，Quinn 下个月无法加入项目。
B. Harper 下个月可以加入项目。另外，Harper 不需要额外专用设备支持，Harper 不存在日程冲突。
C. Sawyer 不需要额外专用设备支持。另外，Sawyer 下个月无法加入项目，Sawyer 不存在日程冲突。
D. Jordan 需要额外专用设备支持。另外，Jordan 下个月可以加入项目，Jordan 不存在日程冲突。

哪位候选人符合全部要求？

约束与 violation signature：

- `C1` `has_schedule_conflict=False`：候选人不能存在日程冲突。
- `C2` `requires_extra_equipment=False`：候选人不能需要额外专用设备支持。
- `C3` `available_next_month=True`：候选人需要下个月可以加入项目。

- `A` violation: `['C1', 'C3']`
- `B` violation: `[]`
- `C` violation: `['C3']`
- `D` violation: `['C2']`

## 40. attr_en_000040_zh_view

- source: `attr_en_000040_original`
- scenario: `availability_selection`
- option_closeness: `hard`
- structural_complexity: `low`
- gold: `C`

协调人需要从四名候选人中找出唯一符合日程和参与要求的人。
被选中的人必须满足以下全部要求：

要求：
1. 候选人不能存在日程冲突。
2. 候选人需要周末可以参与工作。
3. 候选人需要能够现场参与工作。

候选人：
A. Sage 周末可以参与工作。另外，Sage 存在与项目安排冲突的日程，Sage 能够现场参与工作。
B. Logan 周末可以参与工作。另外，Logan 不能现场参与工作，Logan 不存在日程冲突。
C. Indigo 能够现场参与工作。另外，Indigo 不存在日程冲突，Indigo 周末可以参与工作。
D. Taylor 周末无法参与工作。另外，Taylor 不存在日程冲突，Taylor 能够现场参与工作。

哪位候选人符合全部要求？

约束与 violation signature：

- `C1` `has_schedule_conflict=False`：候选人不能存在日程冲突。
- `C2` `available_weekend=True`：候选人需要周末可以参与工作。
- `C3` `can_work_onsite=True`：候选人需要能够现场参与工作。

- `A` violation: `['C1']`
- `B` violation: `['C3']`
- `C` violation: `[]`
- `D` violation: `['C2']`

## 41. attr_en_000041_zh_view

- source: `attr_en_000041_original`
- scenario: `availability_selection`
- option_closeness: `easy`
- structural_complexity: `high`
- gold: `A`

协调人需要从四名候选人中找出唯一符合日程和参与要求的人。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要周一可以参与工作。
2. 候选人需要周二可以参与工作。
3. 候选人需要能够远程工作。
4. 候选人需要下个月可以加入项目。
5. 候选人不能需要额外专用设备支持。

候选人：
A. Kris 周二可以参与工作，Kris 能够远程工作。另外，Kris 下个月可以加入项目，Kris 不需要额外专用设备支持，Kris 周一可以参与工作。
B. Harper 下个月可以加入项目，Harper 周二无法参与工作。另外，Harper 不需要额外专用设备支持，Harper 周一无法参与工作，Harper 不能远程工作。
C. Skyler 周一可以参与工作，Skyler 需要额外专用设备支持。另外，Skyler 下个月无法加入项目，Skyler 周二可以参与工作，Skyler 能够远程工作。
D. Robin 周二可以参与工作，Robin 不能远程工作。另外，Robin 周一无法参与工作，Robin 下个月可以加入项目，Robin 不需要额外专用设备支持。

哪位候选人符合全部要求？

约束与 violation signature：

- `C1` `available_monday=True`：候选人需要周一可以参与工作。
- `C2` `available_tuesday=True`：候选人需要周二可以参与工作。
- `C3` `can_work_remote=True`：候选人需要能够远程工作。
- `C4` `available_next_month=True`：候选人需要下个月可以加入项目。
- `C5` `requires_extra_equipment=False`：候选人不能需要额外专用设备支持。

- `A` violation: `[]`
- `B` violation: `['C1', 'C2', 'C3']`
- `C` violation: `['C4', 'C5']`
- `D` violation: `['C1', 'C3']`

## 42. attr_en_000042_zh_view

- source: `attr_en_000042_original`
- scenario: `availability_selection`
- option_closeness: `easy`
- structural_complexity: `high`
- gold: `A`

协调人需要从四名候选人中找出唯一符合日程和参与要求的人。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要周末可以参与工作。
2. 候选人需要下午可以参与工作。
3. 候选人不能存在日程冲突。
4. 候选人需要接受灵活工时安排。
5. 候选人需要能够远程工作。

候选人：
A. Noel 下午可以参与工作，Noel 不存在日程冲突。另外，Noel 周末可以参与工作，Noel 能够远程工作，Noel 接受灵活工时安排。
B. Arden 存在与项目安排冲突的日程，Arden 周末无法参与工作。另外，Arden 能够远程工作，Arden 下午无法参与工作，Arden 不接受灵活工时安排。
C. Indigo 能够远程工作，Indigo 不接受灵活工时安排。另外，Indigo 周末无法参与工作，Indigo 下午可以参与工作，Indigo 不存在日程冲突。
D. Sawyer 周末可以参与工作，Sawyer 下午可以参与工作。另外，Sawyer 不能远程工作，Sawyer 存在与项目安排冲突的日程，Sawyer 接受灵活工时安排。

哪位候选人符合全部要求？

约束与 violation signature：

- `C1` `available_weekend=True`：候选人需要周末可以参与工作。
- `C2` `available_afternoon=True`：候选人需要下午可以参与工作。
- `C3` `has_schedule_conflict=False`：候选人不能存在日程冲突。
- `C4` `accepts_flexible_hours=True`：候选人需要接受灵活工时安排。
- `C5` `can_work_remote=True`：候选人需要能够远程工作。

- `A` violation: `[]`
- `B` violation: `['C1', 'C2', 'C3', 'C4']`
- `C` violation: `['C1', 'C4']`
- `D` violation: `['C3', 'C5']`

## 43. attr_en_000043_zh_view

- source: `attr_en_000043_original`
- scenario: `expert_recruitment`
- option_closeness: `easy`
- structural_complexity: `high`
- gold: `D`

某研究实验室正在为一个新项目选择一名研究人员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要具备机器学习经验。
2. 候选人需要了解相关项目领域。
3. 候选人需要上午可以参与工作。
4. 候选人需要具有本地工作许可。
5. 候选人需要具备编程经验。

候选人：
A. Blair 没有处理过编程任务，Blair 上午无法参与工作。另外，Blair 没有本地工作许可，Blair 没有机器学习方面的实践经验，Blair 不熟悉相关项目领域。
B. Lane 没有机器学习方面的实践经验，Lane 不熟悉相关项目领域。另外，Lane 具有本地工作许可，Lane 上午可以参与工作，Lane 有实际编程经验。
C. Riley 有实际编程经验，Riley 不熟悉相关项目领域。另外，Riley 上午无法参与工作，Riley 具有本地工作许可，Riley 有机器学习项目经验。
D. Parker 具有本地工作许可，Parker 上午可以参与工作。另外，Parker 有实际编程经验，Parker 有机器学习项目经验，Parker 熟悉相关项目领域。

哪位候选人满足所有要求？

约束与 violation signature：

- `C1` `has_ml_experience=True`：候选人需要具备机器学习经验。
- `C2` `has_domain_knowledge=True`：候选人需要了解相关项目领域。
- `C3` `available_morning=True`：候选人需要上午可以参与工作。
- `C4` `has_local_work_permit=True`：候选人需要具有本地工作许可。
- `C5` `has_programming_experience=True`：候选人需要具备编程经验。

- `A` violation: `['C1', 'C2', 'C3', 'C4', 'C5']`
- `B` violation: `['C1', 'C2']`
- `C` violation: `['C2', 'C3']`
- `D` violation: `[]`

## 44. attr_en_000044_zh_view

- source: `attr_en_000044_original`
- scenario: `project_assignment`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `D`

项目团队需要为一项专门任务分配一名成员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要具有本地工作许可。
2. 候选人需要周二可以参与工作。
3. 候选人需要能够远程工作。
4. 候选人需要能够现场参与工作。

候选人：
A. Sawyer 不能远程工作，Sawyer 能够现场参与工作。另外，Sawyer 具有本地工作许可，Sawyer 周二可以参与工作。
B. Milan 周二无法参与工作，Milan 具有本地工作许可。另外，Milan 不能现场参与工作，Milan 能够远程工作。
C. Riley 周二可以参与工作，Riley 能够远程工作。另外，Riley 能够现场参与工作，Riley 没有本地工作许可。
D. Ellis 能够远程工作，Ellis 具有本地工作许可。另外，Ellis 能够现场参与工作，Ellis 周二可以参与工作。

哪位候选人适合承担这项任务？

约束与 violation signature：

- `C1` `has_local_work_permit=True`：候选人需要具有本地工作许可。
- `C2` `available_tuesday=True`：候选人需要周二可以参与工作。
- `C3` `can_work_remote=True`：候选人需要能够远程工作。
- `C4` `can_work_onsite=True`：候选人需要能够现场参与工作。

- `A` violation: `['C3']`
- `B` violation: `['C2', 'C4']`
- `C` violation: `['C1']`
- `D` violation: `[]`

## 45. attr_en_000045_zh_view

- source: `attr_en_000045_original`
- scenario: `expert_recruitment`
- option_closeness: `hard`
- structural_complexity: `low`
- gold: `D`

某研究实验室正在为一个新项目选择一名研究人员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要具备客户沟通经验。
2. 候选人需要持有相关证书。
3. 候选人需要下午可以参与工作。

候选人：
A. Harper 持有相关专业证书。另外，Harper 有客户沟通经验，Harper 下午无法参与工作。
B. Kris 下午可以参与工作。另外，Kris 没有相关专业证书，Kris 有客户沟通经验。
C. Rowan 持有相关专业证书。另外，Rowan 下午可以参与工作，Rowan 没有客户沟通经验。
D. Casey 下午可以参与工作。另外，Casey 持有相关专业证书，Casey 有客户沟通经验。

哪位候选人满足所有要求？

约束与 violation signature：

- `C1` `has_client_communication_experience=True`：候选人需要具备客户沟通经验。
- `C2` `has_certificate=True`：候选人需要持有相关证书。
- `C3` `available_afternoon=True`：候选人需要下午可以参与工作。

- `A` violation: `['C3']`
- `B` violation: `['C2']`
- `C` violation: `['C1']`
- `D` violation: `[]`

## 46. attr_en_000046_zh_view

- source: `attr_en_000046_original`
- scenario: `expert_recruitment`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `B`

某研究实验室正在为一个新项目选择一名研究人员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人不能存在日程冲突。
2. 候选人需要了解相关项目领域。
3. 候选人需要参与过项目执行工作。
4. 候选人不能存在与项目相关的利益冲突。

候选人：
A. Payton 参与过项目执行，Payton 与项目存在利益冲突。另外，Payton 存在与项目安排冲突的日程，Payton 熟悉相关项目领域。
B. Hayden 熟悉相关项目领域，Hayden 参与过项目执行。另外，Hayden 不存在项目相关的利益冲突，Hayden 不存在日程冲突。
C. Finley 不存在项目相关的利益冲突，Finley 不熟悉相关项目领域。另外，Finley 不存在日程冲突，Finley 参与过项目执行。
D. Morgan 熟悉相关项目领域，Morgan 没有参与过项目执行。另外，Morgan 不存在项目相关的利益冲突，Morgan 不存在日程冲突。

哪位候选人满足所有要求？

约束与 violation signature：

- `C1` `has_schedule_conflict=False`：候选人不能存在日程冲突。
- `C2` `has_domain_knowledge=True`：候选人需要了解相关项目领域。
- `C3` `has_project_experience=True`：候选人需要参与过项目执行工作。
- `C4` `has_conflict=False`：候选人不能存在与项目相关的利益冲突。

- `A` violation: `['C1', 'C4']`
- `B` violation: `[]`
- `C` violation: `['C2']`
- `D` violation: `['C3']`

## 47. attr_en_000047_zh_view

- source: `attr_en_000047_original`
- scenario: `availability_selection`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `B`

协调人需要从四名候选人中找出唯一符合日程和参与要求的人。
被选中的人必须满足以下全部要求：

要求：
1. 候选人不能需要额外专用设备支持。
2. 候选人需要下个月可以加入项目。
3. 候选人需要能够现场参与工作。
4. 候选人需要周一可以参与工作。

候选人：
A. Arden 下个月无法加入项目，Arden 周一可以参与工作。另外，Arden 能够现场参与工作，Arden 需要额外专用设备支持。
B. Harper 不需要额外专用设备支持，Harper 周一可以参与工作。另外，Harper 能够现场参与工作，Harper 下个月可以加入项目。
C. Avery 能够现场参与工作，Avery 周一无法参与工作。另外，Avery 下个月可以加入项目，Avery 不需要额外专用设备支持。
D. Tatum 下个月可以加入项目，Tatum 不能现场参与工作。另外，Tatum 不需要额外专用设备支持，Tatum 周一可以参与工作。

哪位候选人符合全部要求？

约束与 violation signature：

- `C1` `requires_extra_equipment=False`：候选人不能需要额外专用设备支持。
- `C2` `available_next_month=True`：候选人需要下个月可以加入项目。
- `C3` `can_work_onsite=True`：候选人需要能够现场参与工作。
- `C4` `available_monday=True`：候选人需要周一可以参与工作。

- `A` violation: `['C1', 'C2']`
- `B` violation: `[]`
- `C` violation: `['C4']`
- `D` violation: `['C3']`

## 48. attr_en_000048_zh_view

- source: `attr_en_000048_original`
- scenario: `availability_selection`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `C`

协调人需要从四名候选人中找出唯一符合日程和参与要求的人。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要周二可以参与工作。
2. 候选人需要周一可以参与工作。
3. 候选人需要能够远程工作。
4. 候选人需要接受灵活工时安排。

候选人：
A. Jules 接受灵活工时安排，Jules 周一可以参与工作。另外，Jules 周二无法参与工作，Jules 能够远程工作。
B. Ellis 周一无法参与工作，Ellis 不接受灵活工时安排。另外，Ellis 能够远程工作，Ellis 周二可以参与工作。
C. Riley 周一可以参与工作，Riley 能够远程工作。另外，Riley 接受灵活工时安排，Riley 周二可以参与工作。
D. Harper 周一可以参与工作，Harper 接受灵活工时安排。另外，Harper 不能远程工作，Harper 周二可以参与工作。

哪位候选人符合全部要求？

约束与 violation signature：

- `C1` `available_tuesday=True`：候选人需要周二可以参与工作。
- `C2` `available_monday=True`：候选人需要周一可以参与工作。
- `C3` `can_work_remote=True`：候选人需要能够远程工作。
- `C4` `accepts_flexible_hours=True`：候选人需要接受灵活工时安排。

- `A` violation: `['C1']`
- `B` violation: `['C2', 'C4']`
- `C` violation: `[]`
- `D` violation: `['C3']`

## 49. attr_en_000049_zh_view

- source: `attr_en_000049_original`
- scenario: `project_assignment`
- option_closeness: `hard`
- structural_complexity: `low`
- gold: `D`

项目团队需要为一项专门任务分配一名成员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要接受灵活工时安排。
2. 候选人需要能够使用英语进行工作沟通。
3. 候选人需要具备数据分析经验。

候选人：
A. Drew 能够用英语进行工作沟通。另外，Drew 没有实际数据分析经历，Drew 接受灵活工时安排。
B. Harper 接受灵活工时安排。另外，Harper 做过数据分析工作，Harper 不能用英语进行工作沟通。
C. Ellis 能够用英语进行工作沟通。另外，Ellis 做过数据分析工作，Ellis 不接受灵活工时安排。
D. Lane 能够用英语进行工作沟通。另外，Lane 做过数据分析工作，Lane 接受灵活工时安排。

哪位候选人适合承担这项任务？

约束与 violation signature：

- `C1` `accepts_flexible_hours=True`：候选人需要接受灵活工时安排。
- `C2` `speaks_english=True`：候选人需要能够使用英语进行工作沟通。
- `C3` `has_data_analysis_experience=True`：候选人需要具备数据分析经验。

- `A` violation: `['C3']`
- `B` violation: `['C2']`
- `C` violation: `['C1']`
- `D` violation: `[]`

## 50. attr_en_000050_zh_view

- source: `attr_en_000050_original`
- scenario: `expert_recruitment`
- option_closeness: `easy`
- structural_complexity: `high`
- gold: `C`

某研究实验室正在为一个新项目选择一名研究人员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要有管理或协调经验。
2. 候选人需要具备团队协作经验。
3. 候选人需要周一可以参与工作。
4. 候选人需要具备机器学习经验。
5. 候选人需要能够独立工作。

候选人：
A. Morgan 没有管理或协调项目的经历，Morgan 周一无法参与工作。另外，Morgan 能够独立工作，Morgan 有机器学习项目经验，Morgan 有团队协作经验。
B. Hayden 周一可以参与工作，Hayden 有机器学习项目经验。另外，Hayden 不能独立完成工作，Hayden 没有管理或协调项目的经历，Hayden 有团队协作经验。
C. Cameron 能够独立工作，Cameron 有团队协作经验。另外，Cameron 有机器学习项目经验，Cameron 周一可以参与工作，Cameron 曾经负责过项目或团队协调。
D. Jules 不能独立完成工作，Jules 缺少团队协作经验。另外，Jules 曾经负责过项目或团队协调，Jules 周一可以参与工作，Jules 没有机器学习方面的实践经验。

哪位候选人满足所有要求？

约束与 violation signature：

- `C1` `has_management_experience=True`：候选人需要有管理或协调经验。
- `C2` `has_teamwork_experience=True`：候选人需要具备团队协作经验。
- `C3` `available_monday=True`：候选人需要周一可以参与工作。
- `C4` `has_ml_experience=True`：候选人需要具备机器学习经验。
- `C5` `can_work_independently=True`：候选人需要能够独立工作。

- `A` violation: `['C1', 'C3']`
- `B` violation: `['C1', 'C5']`
- `C` violation: `[]`
- `D` violation: `['C2', 'C4', 'C5']`

## 51. attr_en_000051_zh_view

- source: `attr_en_000051_original`
- scenario: `project_assignment`
- option_closeness: `medium`
- structural_complexity: `low`
- gold: `A`

项目团队需要为一项专门任务分配一名成员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要下个月可以加入项目。
2. 候选人需要能够在不需要额外监督的情况下工作。
3. 候选人不能需要额外专用设备支持。

候选人：
A. Tatum 下个月可以加入项目。另外，Tatum 不需要额外专用设备支持，Tatum 不需要额外监督也能完成工作。
B. Elliot 不需要额外专用设备支持。另外，Elliot 不需要额外监督也能完成工作，Elliot 下个月无法加入项目。
C. Harper 需要额外专用设备支持。另外，Harper 下个月无法加入项目，Harper 不需要额外监督也能完成工作。
D. Emerson 不需要额外专用设备支持。另外，Emerson 下个月可以加入项目，Emerson 需要额外监督才能完成工作。

哪位候选人适合承担这项任务？

约束与 violation signature：

- `C1` `available_next_month=True`：候选人需要下个月可以加入项目。
- `C2` `needs_supervision=False`：候选人需要能够在不需要额外监督的情况下工作。
- `C3` `requires_extra_equipment=False`：候选人不能需要额外专用设备支持。

- `A` violation: `[]`
- `B` violation: `['C1']`
- `C` violation: `['C1', 'C3']`
- `D` violation: `['C2']`

## 52. attr_en_000052_zh_view

- source: `attr_en_000052_original`
- scenario: `project_assignment`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `C`

项目团队需要为一项专门任务分配一名成员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要具备质量保证经验。
2. 候选人需要有公开表达或演讲经验。
3. 候选人需要具备机器学习经验。
4. 候选人需要能够在不需要额外监督的情况下工作。

候选人：
A. Gray 有机器学习项目经验，Gray 没有公开表达或演讲经验。另外，Gray 有质量保证经验，Gray 需要额外监督才能完成工作。
B. Jules 不需要额外监督也能完成工作，Jules 没有机器学习方面的实践经验。另外，Jules 有公开表达或演讲经验，Jules 有质量保证经验。
C. Logan 有机器学习项目经验，Logan 不需要额外监督也能完成工作。另外，Logan 有质量保证经验，Logan 有公开表达或演讲经验。
D. Parker 有公开表达或演讲经验，Parker 没有质量保证经验。另外，Parker 有机器学习项目经验，Parker 不需要额外监督也能完成工作。

哪位候选人适合承担这项任务？

约束与 violation signature：

- `C1` `has_quality_assurance_experience=True`：候选人需要具备质量保证经验。
- `C2` `has_public_speaking_experience=True`：候选人需要有公开表达或演讲经验。
- `C3` `has_ml_experience=True`：候选人需要具备机器学习经验。
- `C4` `needs_supervision=False`：候选人需要能够在不需要额外监督的情况下工作。

- `A` violation: `['C2', 'C4']`
- `B` violation: `['C3']`
- `C` violation: `[]`
- `D` violation: `['C1']`

## 53. attr_en_000053_zh_view

- source: `attr_en_000053_original`
- scenario: `availability_selection`
- option_closeness: `hard`
- structural_complexity: `low`
- gold: `B`

协调人需要从四名候选人中找出唯一符合日程和参与要求的人。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要周末可以参与工作。
2. 候选人需要上午可以参与工作。
3. 候选人需要周一可以参与工作。

候选人：
A. Parker 周末可以参与工作。另外，Parker 周一可以参与工作，Parker 上午无法参与工作。
B. Cameron 上午可以参与工作。另外，Cameron 周一可以参与工作，Cameron 周末可以参与工作。
C. Gray 上午可以参与工作。另外，Gray 周一可以参与工作，Gray 周末无法参与工作。
D. Hayden 周一无法参与工作。另外，Hayden 周末可以参与工作，Hayden 上午可以参与工作。

哪位候选人符合全部要求？

约束与 violation signature：

- `C1` `available_weekend=True`：候选人需要周末可以参与工作。
- `C2` `available_morning=True`：候选人需要上午可以参与工作。
- `C3` `available_monday=True`：候选人需要周一可以参与工作。

- `A` violation: `['C2']`
- `B` violation: `[]`
- `C` violation: `['C1']`
- `D` violation: `['C3']`

## 54. attr_en_000054_zh_view

- source: `attr_en_000054_original`
- scenario: `availability_selection`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `C`

协调人需要从四名候选人中找出唯一符合日程和参与要求的人。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要下午可以参与工作。
2. 候选人不能需要额外专用设备支持。
3. 候选人需要周二可以参与工作。
4. 候选人需要下个月可以加入项目。

候选人：
A. Kris 周二可以参与工作，Kris 下午无法参与工作。另外，Kris 不需要额外专用设备支持，Kris 下个月无法加入项目。
B. Payton 不需要额外专用设备支持，Payton 周二无法参与工作。另外，Payton 下个月可以加入项目，Payton 下午可以参与工作。
C. Tatum 不需要额外专用设备支持，Tatum 周二可以参与工作。另外，Tatum 下午可以参与工作，Tatum 下个月可以加入项目。
D. Wren 需要额外专用设备支持，Wren 下午可以参与工作。另外，Wren 下个月可以加入项目，Wren 周二可以参与工作。

哪位候选人符合全部要求？

约束与 violation signature：

- `C1` `available_afternoon=True`：候选人需要下午可以参与工作。
- `C2` `requires_extra_equipment=False`：候选人不能需要额外专用设备支持。
- `C3` `available_tuesday=True`：候选人需要周二可以参与工作。
- `C4` `available_next_month=True`：候选人需要下个月可以加入项目。

- `A` violation: `['C1', 'C4']`
- `B` violation: `['C3']`
- `C` violation: `[]`
- `D` violation: `['C2']`

## 55. attr_en_000055_zh_view

- source: `attr_en_000055_original`
- scenario: `project_assignment`
- option_closeness: `hard`
- structural_complexity: `low`
- gold: `A`

项目团队需要为一项专门任务分配一名成员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人不能存在与项目相关的利益冲突。
2. 候选人需要完成过相关培训。
3. 候选人需要上午可以参与工作。

候选人：
A. Sawyer 上午可以参与工作。另外，Sawyer 完成过相关培训，Sawyer 不存在项目相关的利益冲突。
B. Marley 完成过相关培训。另外，Marley 上午无法参与工作，Marley 不存在项目相关的利益冲突。
C. Morgan 完成过相关培训。另外，Morgan 上午可以参与工作，Morgan 与项目存在利益冲突。
D. Kris 上午可以参与工作。另外，Kris 没有完成相关培训，Kris 不存在项目相关的利益冲突。

哪位候选人适合承担这项任务？

约束与 violation signature：

- `C1` `has_conflict=False`：候选人不能存在与项目相关的利益冲突。
- `C2` `has_prior_training=True`：候选人需要完成过相关培训。
- `C3` `available_morning=True`：候选人需要上午可以参与工作。

- `A` violation: `[]`
- `B` violation: `['C3']`
- `C` violation: `['C1']`
- `D` violation: `['C2']`

## 56. attr_en_000056_zh_view

- source: `attr_en_000056_original`
- scenario: `availability_selection`
- option_closeness: `easy`
- structural_complexity: `high`
- gold: `C`

协调人需要从四名候选人中找出唯一符合日程和参与要求的人。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要周一可以参与工作。
2. 候选人不能需要额外专用设备支持。
3. 候选人需要周二可以参与工作。
4. 候选人需要下个月可以加入项目。
5. 候选人需要上午可以参与工作。

候选人：
A. Logan 下个月可以加入项目，Logan 周二可以参与工作。另外，Logan 周一无法参与工作，Logan 不需要额外专用设备支持，Logan 上午无法参与工作。
B. Reese 周一无法参与工作，Reese 上午可以参与工作。另外，Reese 不需要额外专用设备支持，Reese 周二可以参与工作，Reese 下个月无法加入项目。
C. Hayden 下个月可以加入项目，Hayden 周一可以参与工作。另外，Hayden 周二可以参与工作，Hayden 上午可以参与工作，Hayden 不需要额外专用设备支持。
D. Payton 需要额外专用设备支持，Payton 上午无法参与工作。另外，Payton 周一无法参与工作，Payton 周二无法参与工作，Payton 下个月无法加入项目。

哪位候选人符合全部要求？

约束与 violation signature：

- `C1` `available_monday=True`：候选人需要周一可以参与工作。
- `C2` `requires_extra_equipment=False`：候选人不能需要额外专用设备支持。
- `C3` `available_tuesday=True`：候选人需要周二可以参与工作。
- `C4` `available_next_month=True`：候选人需要下个月可以加入项目。
- `C5` `available_morning=True`：候选人需要上午可以参与工作。

- `A` violation: `['C1', 'C5']`
- `B` violation: `['C1', 'C4']`
- `C` violation: `[]`
- `D` violation: `['C1', 'C2', 'C3', 'C4', 'C5']`

## 57. attr_en_000057_zh_view

- source: `attr_en_000057_original`
- scenario: `expert_recruitment`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `B`

某研究实验室正在为一个新项目选择一名研究人员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要持有相关证书。
2. 候选人需要熟悉统计方法。
3. 候选人需要具备编程经验。
4. 候选人不能存在与项目相关的利益冲突。

候选人：
A. Blair 不熟悉统计方法，Blair 有实际编程经验。另外，Blair 不存在项目相关的利益冲突，Blair 持有相关专业证书。
B. Riley 不存在项目相关的利益冲突，Riley 持有相关专业证书。另外，Riley 熟悉统计方法，Riley 有实际编程经验。
C. Reese 有实际编程经验，Reese 没有相关专业证书。另外，Reese 熟悉统计方法，Reese 与项目存在利益冲突。
D. Drew 持有相关专业证书，Drew 不存在项目相关的利益冲突。另外，Drew 没有处理过编程任务，Drew 熟悉统计方法。

哪位候选人满足所有要求？

约束与 violation signature：

- `C1` `has_certificate=True`：候选人需要持有相关证书。
- `C2` `familiar_with_statistics=True`：候选人需要熟悉统计方法。
- `C3` `has_programming_experience=True`：候选人需要具备编程经验。
- `C4` `has_conflict=False`：候选人不能存在与项目相关的利益冲突。

- `A` violation: `['C2']`
- `B` violation: `[]`
- `C` violation: `['C1', 'C4']`
- `D` violation: `['C3']`

## 58. attr_en_000058_zh_view

- source: `attr_en_000058_original`
- scenario: `availability_selection`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `D`

协调人需要从四名候选人中找出唯一符合日程和参与要求的人。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要周末可以参与工作。
2. 候选人不能需要额外专用设备支持。
3. 候选人需要下个月可以加入项目。
4. 候选人不能存在日程冲突。

候选人：
A. Lane 不需要额外专用设备支持，Lane 不存在日程冲突。另外，Lane 周末无法参与工作，Lane 下个月可以加入项目。
B. Casey 不存在日程冲突，Casey 周末可以参与工作。另外，Casey 下个月无法加入项目，Casey 需要额外专用设备支持。
C. Jules 不需要额外专用设备支持，Jules 下个月可以加入项目。另外，Jules 存在与项目安排冲突的日程，Jules 周末可以参与工作。
D. Hayden 不存在日程冲突，Hayden 下个月可以加入项目。另外，Hayden 周末可以参与工作，Hayden 不需要额外专用设备支持。

哪位候选人符合全部要求？

约束与 violation signature：

- `C1` `available_weekend=True`：候选人需要周末可以参与工作。
- `C2` `requires_extra_equipment=False`：候选人不能需要额外专用设备支持。
- `C3` `available_next_month=True`：候选人需要下个月可以加入项目。
- `C4` `has_schedule_conflict=False`：候选人不能存在日程冲突。

- `A` violation: `['C1']`
- `B` violation: `['C2', 'C3']`
- `C` violation: `['C4']`
- `D` violation: `[]`

## 59. attr_en_000059_zh_view

- source: `attr_en_000059_original`
- scenario: `project_assignment`
- option_closeness: `easy`
- structural_complexity: `high`
- gold: `A`

项目团队需要为一项专门任务分配一名成员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要熟悉统计方法。
2. 候选人需要能够远程工作。
3. 候选人需要接受灵活工时安排。
4. 候选人需要参与过项目执行工作。
5. 候选人需要能够在不需要额外监督的情况下工作。

候选人：
A. Ellis 能够远程工作，Ellis 熟悉统计方法。另外，Ellis 接受灵活工时安排，Ellis 不需要额外监督也能完成工作，Ellis 参与过项目执行。
B. Blair 参与过项目执行，Blair 能够远程工作。另外，Blair 不熟悉统计方法，Blair 不需要额外监督也能完成工作，Blair 不接受灵活工时安排。
C. Quinn 需要额外监督才能完成工作，Quinn 没有参与过项目执行。另外，Quinn 熟悉统计方法，Quinn 不能远程工作，Quinn 接受灵活工时安排。
D. Noel 熟悉统计方法，Noel 不能远程工作。另外，Noel 接受灵活工时安排，Noel 不需要额外监督也能完成工作，Noel 没有参与过项目执行。

哪位候选人适合承担这项任务？

约束与 violation signature：

- `C1` `familiar_with_statistics=True`：候选人需要熟悉统计方法。
- `C2` `can_work_remote=True`：候选人需要能够远程工作。
- `C3` `accepts_flexible_hours=True`：候选人需要接受灵活工时安排。
- `C4` `has_project_experience=True`：候选人需要参与过项目执行工作。
- `C5` `needs_supervision=False`：候选人需要能够在不需要额外监督的情况下工作。

- `A` violation: `[]`
- `B` violation: `['C1', 'C3']`
- `C` violation: `['C2', 'C4', 'C5']`
- `D` violation: `['C2', 'C4']`

## 60. attr_en_000060_zh_view

- source: `attr_en_000060_original`
- scenario: `expert_recruitment`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `B`

某研究实验室正在为一个新项目选择一名研究人员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要下午可以参与工作。
2. 候选人需要具备数据分析经验。
3. 候选人需要有管理或协调经验。
4. 候选人需要持有相关证书。

候选人：
A. Riley 下午可以参与工作，Riley 没有相关专业证书。另外，Riley 做过数据分析工作，Riley 曾经负责过项目或团队协调。
B. Blair 持有相关专业证书，Blair 曾经负责过项目或团队协调。另外，Blair 下午可以参与工作，Blair 做过数据分析工作。
C. Elliot 做过数据分析工作，Elliot 持有相关专业证书。另外，Elliot 下午无法参与工作，Elliot 曾经负责过项目或团队协调。
D. Arden 持有相关专业证书，Arden 没有实际数据分析经历。另外，Arden 下午可以参与工作，Arden 没有管理或协调项目的经历。

哪位候选人满足所有要求？

约束与 violation signature：

- `C1` `available_afternoon=True`：候选人需要下午可以参与工作。
- `C2` `has_data_analysis_experience=True`：候选人需要具备数据分析经验。
- `C3` `has_management_experience=True`：候选人需要有管理或协调经验。
- `C4` `has_certificate=True`：候选人需要持有相关证书。

- `A` violation: `['C4']`
- `B` violation: `[]`
- `C` violation: `['C1']`
- `D` violation: `['C2', 'C3']`

## 61. attr_en_000061_zh_view

- source: `attr_en_000061_original`
- scenario: `project_assignment`
- option_closeness: `easy`
- structural_complexity: `high`
- gold: `D`

项目团队需要为一项专门任务分配一名成员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要有公开表达或演讲经验。
2. 候选人不能存在日程冲突。
3. 候选人需要具备机器学习经验。
4. 候选人需要接受灵活工时安排。
5. 候选人需要能够远程工作。

候选人：
A. Harper 没有机器学习方面的实践经验，Harper 不存在日程冲突。另外，Harper 不接受灵活工时安排，Harper 没有公开表达或演讲经验，Harper 不能远程工作。
B. Sage 接受灵活工时安排，Sage 能够远程工作。另外，Sage 没有机器学习方面的实践经验，Sage 存在与项目安排冲突的日程，Sage 有公开表达或演讲经验。
C. Kris 有机器学习项目经验，Kris 不接受灵活工时安排。另外，Kris 能够远程工作，Kris 有公开表达或演讲经验，Kris 存在与项目安排冲突的日程。
D. Rowan 接受灵活工时安排，Rowan 有机器学习项目经验。另外，Rowan 能够远程工作，Rowan 有公开表达或演讲经验，Rowan 不存在日程冲突。

哪位候选人适合承担这项任务？

约束与 violation signature：

- `C1` `has_public_speaking_experience=True`：候选人需要有公开表达或演讲经验。
- `C2` `has_schedule_conflict=False`：候选人不能存在日程冲突。
- `C3` `has_ml_experience=True`：候选人需要具备机器学习经验。
- `C4` `accepts_flexible_hours=True`：候选人需要接受灵活工时安排。
- `C5` `can_work_remote=True`：候选人需要能够远程工作。

- `A` violation: `['C1', 'C3', 'C4', 'C5']`
- `B` violation: `['C2', 'C3']`
- `C` violation: `['C2', 'C4']`
- `D` violation: `[]`

## 62. attr_en_000062_zh_view

- source: `attr_en_000062_original`
- scenario: `project_assignment`
- option_closeness: `hard`
- structural_complexity: `low`
- gold: `D`

项目团队需要为一项专门任务分配一名成员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要周一可以参与工作。
2. 候选人需要具备数据分析经验。
3. 候选人需要能够在不需要额外监督的情况下工作。

候选人：
A. Avery 周一可以参与工作。另外，Avery 需要额外监督才能完成工作，Avery 做过数据分析工作。
B. Emerson 不需要额外监督也能完成工作。另外，Emerson 周一无法参与工作，Emerson 做过数据分析工作。
C. Tatum 不需要额外监督也能完成工作。另外，Tatum 没有实际数据分析经历，Tatum 周一可以参与工作。
D. Elliot 不需要额外监督也能完成工作。另外，Elliot 周一可以参与工作，Elliot 做过数据分析工作。

哪位候选人适合承担这项任务？

约束与 violation signature：

- `C1` `available_monday=True`：候选人需要周一可以参与工作。
- `C2` `has_data_analysis_experience=True`：候选人需要具备数据分析经验。
- `C3` `needs_supervision=False`：候选人需要能够在不需要额外监督的情况下工作。

- `A` violation: `['C3']`
- `B` violation: `['C1']`
- `C` violation: `['C2']`
- `D` violation: `[]`

## 63. attr_en_000063_zh_view

- source: `attr_en_000063_original`
- scenario: `project_assignment`
- option_closeness: `hard`
- structural_complexity: `low`
- gold: `B`

项目团队需要为一项专门任务分配一名成员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要周二可以参与工作。
2. 候选人需要具备编程经验。
3. 候选人需要具备数据分析经验。

候选人：
A. Reese 没有实际数据分析经历。另外，Reese 有实际编程经验，Reese 周二可以参与工作。
B. Cameron 周二可以参与工作。另外，Cameron 做过数据分析工作，Cameron 有实际编程经验。
C. Morgan 没有处理过编程任务。另外，Morgan 做过数据分析工作，Morgan 周二可以参与工作。
D. Taylor 有实际编程经验。另外，Taylor 做过数据分析工作，Taylor 周二无法参与工作。

哪位候选人适合承担这项任务？

约束与 violation signature：

- `C1` `available_tuesday=True`：候选人需要周二可以参与工作。
- `C2` `has_programming_experience=True`：候选人需要具备编程经验。
- `C3` `has_data_analysis_experience=True`：候选人需要具备数据分析经验。

- `A` violation: `['C3']`
- `B` violation: `[]`
- `C` violation: `['C2']`
- `D` violation: `['C1']`

## 64. attr_en_000064_zh_view

- source: `attr_en_000064_original`
- scenario: `expert_recruitment`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `C`

某研究实验室正在为一个新项目选择一名研究人员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要具备客户沟通经验。
2. 候选人需要具有本地工作许可。
3. 候选人需要能够在不需要额外监督的情况下工作。
4. 候选人不能存在与项目相关的利益冲突。

候选人：
A. Marley 不需要额外监督也能完成工作，Marley 具有本地工作许可。另外，Marley 与项目存在利益冲突，Marley 有客户沟通经验。
B. Elliot 没有本地工作许可，Elliot 需要额外监督才能完成工作。另外，Elliot 不存在项目相关的利益冲突，Elliot 有客户沟通经验。
C. Jules 不需要额外监督也能完成工作，Jules 不存在项目相关的利益冲突。另外，Jules 有客户沟通经验，Jules 具有本地工作许可。
D. Kris 不存在项目相关的利益冲突，Kris 具有本地工作许可。另外，Kris 没有客户沟通经验，Kris 不需要额外监督也能完成工作。

哪位候选人满足所有要求？

约束与 violation signature：

- `C1` `has_client_communication_experience=True`：候选人需要具备客户沟通经验。
- `C2` `has_local_work_permit=True`：候选人需要具有本地工作许可。
- `C3` `needs_supervision=False`：候选人需要能够在不需要额外监督的情况下工作。
- `C4` `has_conflict=False`：候选人不能存在与项目相关的利益冲突。

- `A` violation: `['C4']`
- `B` violation: `['C2', 'C3']`
- `C` violation: `[]`
- `D` violation: `['C1']`

## 65. attr_en_000065_zh_view

- source: `attr_en_000065_original`
- scenario: `project_assignment`
- option_closeness: `medium`
- structural_complexity: `low`
- gold: `B`

项目团队需要为一项专门任务分配一名成员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要具备质量保证经验。
2. 候选人需要具备客户沟通经验。
3. 候选人需要愿意出差。

候选人：
A. Hayden 没有质量保证经验。另外，Hayden 愿意出差，Hayden 没有客户沟通经验。
B. Reese 有质量保证经验。另外，Reese 愿意出差，Reese 有客户沟通经验。
C. Arden 有客户沟通经验。另外，Arden 不愿意出差，Arden 有质量保证经验。
D. Marley 愿意出差。另外，Marley 有质量保证经验，Marley 没有客户沟通经验。

哪位候选人适合承担这项任务？

约束与 violation signature：

- `C1` `has_quality_assurance_experience=True`：候选人需要具备质量保证经验。
- `C2` `has_client_communication_experience=True`：候选人需要具备客户沟通经验。
- `C3` `willing_to_travel=True`：候选人需要愿意出差。

- `A` violation: `['C1', 'C2']`
- `B` violation: `[]`
- `C` violation: `['C3']`
- `D` violation: `['C2']`

## 66. attr_en_000066_zh_view

- source: `attr_en_000066_original`
- scenario: `project_assignment`
- option_closeness: `hard`
- structural_complexity: `low`
- gold: `C`

项目团队需要为一项专门任务分配一名成员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要接受灵活工时安排。
2. 候选人需要能够现场参与工作。
3. 候选人需要有管理或协调经验。

候选人：
A. Jordan 能够现场参与工作。另外，Jordan 接受灵活工时安排，Jordan 没有管理或协调项目的经历。
B. Jamie 不能现场参与工作。另外，Jamie 曾经负责过项目或团队协调，Jamie 接受灵活工时安排。
C. Jules 能够现场参与工作。另外，Jules 曾经负责过项目或团队协调，Jules 接受灵活工时安排。
D. Milan 能够现场参与工作。另外，Milan 曾经负责过项目或团队协调，Milan 不接受灵活工时安排。

哪位候选人适合承担这项任务？

约束与 violation signature：

- `C1` `accepts_flexible_hours=True`：候选人需要接受灵活工时安排。
- `C2` `can_work_onsite=True`：候选人需要能够现场参与工作。
- `C3` `has_management_experience=True`：候选人需要有管理或协调经验。

- `A` violation: `['C3']`
- `B` violation: `['C2']`
- `C` violation: `[]`
- `D` violation: `['C1']`

## 67. attr_en_000067_zh_view

- source: `attr_en_000067_original`
- scenario: `project_assignment`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `C`

项目团队需要为一项专门任务分配一名成员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要能够在不需要额外监督的情况下工作。
2. 候选人需要具备数据分析经验。
3. 候选人需要有研究项目经验。
4. 候选人需要具备客户沟通经验。

候选人：
A. Blair 做过数据分析工作，Blair 没有研究项目经历。另外，Blair 有客户沟通经验，Blair 不需要额外监督也能完成工作。
B. Casey 有客户沟通经验，Casey 没有实际数据分析经历。另外，Casey 需要额外监督才能完成工作，Casey 参与过研究项目。
C. Briar 做过数据分析工作，Briar 参与过研究项目。另外，Briar 有客户沟通经验，Briar 不需要额外监督也能完成工作。
D. Devon 做过数据分析工作，Devon 不需要额外监督也能完成工作。另外，Devon 参与过研究项目，Devon 没有客户沟通经验。

哪位候选人适合承担这项任务？

约束与 violation signature：

- `C1` `needs_supervision=False`：候选人需要能够在不需要额外监督的情况下工作。
- `C2` `has_data_analysis_experience=True`：候选人需要具备数据分析经验。
- `C3` `has_research_experience=True`：候选人需要有研究项目经验。
- `C4` `has_client_communication_experience=True`：候选人需要具备客户沟通经验。

- `A` violation: `['C3']`
- `B` violation: `['C1', 'C2']`
- `C` violation: `[]`
- `D` violation: `['C4']`

## 68. attr_en_000068_zh_view

- source: `attr_en_000068_original`
- scenario: `expert_recruitment`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `A`

某研究实验室正在为一个新项目选择一名研究人员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要具备安全许可。
2. 候选人需要具备质量保证经验。
3. 候选人需要下个月可以加入项目。
4. 候选人不能存在与项目相关的利益冲突。

候选人：
A. Robin 有质量保证经验，Robin 下个月可以加入项目。另外，Robin 具备安全许可，Robin 不存在项目相关的利益冲突。
B. Payton 有质量保证经验，Payton 具备安全许可。另外，Payton 下个月无法加入项目，Payton 不存在项目相关的利益冲突。
C. Reese 不存在项目相关的利益冲突，Reese 下个月可以加入项目。另外，Reese 没有质量保证经验，Reese 不具备安全许可。
D. Devon 有质量保证经验，Devon 与项目存在利益冲突。另外，Devon 下个月可以加入项目，Devon 具备安全许可。

哪位候选人满足所有要求？

约束与 violation signature：

- `C1` `has_security_clearance=True`：候选人需要具备安全许可。
- `C2` `has_quality_assurance_experience=True`：候选人需要具备质量保证经验。
- `C3` `available_next_month=True`：候选人需要下个月可以加入项目。
- `C4` `has_conflict=False`：候选人不能存在与项目相关的利益冲突。

- `A` violation: `[]`
- `B` violation: `['C3']`
- `C` violation: `['C1', 'C2']`
- `D` violation: `['C4']`

## 69. attr_en_000069_zh_view

- source: `attr_en_000069_original`
- scenario: `availability_selection`
- option_closeness: `medium`
- structural_complexity: `low`
- gold: `A`

协调人需要从四名候选人中找出唯一符合日程和参与要求的人。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要接受灵活工时安排。
2. 候选人需要能够现场参与工作。
3. 候选人需要下个月可以加入项目。

候选人：
A. Blair 能够现场参与工作。另外，Blair 下个月可以加入项目，Blair 接受灵活工时安排。
B. Rowan 能够现场参与工作。另外，Rowan 不接受灵活工时安排，Rowan 下个月可以加入项目。
C. Tatum 下个月可以加入项目。另外，Tatum 不能现场参与工作，Tatum 接受灵活工时安排。
D. Kris 下个月无法加入项目。另外，Kris 不能现场参与工作，Kris 接受灵活工时安排。

哪位候选人符合全部要求？

约束与 violation signature：

- `C1` `accepts_flexible_hours=True`：候选人需要接受灵活工时安排。
- `C2` `can_work_onsite=True`：候选人需要能够现场参与工作。
- `C3` `available_next_month=True`：候选人需要下个月可以加入项目。

- `A` violation: `[]`
- `B` violation: `['C1']`
- `C` violation: `['C2']`
- `D` violation: `['C2', 'C3']`

## 70. attr_en_000070_zh_view

- source: `attr_en_000070_original`
- scenario: `expert_recruitment`
- option_closeness: `easy`
- structural_complexity: `high`
- gold: `C`

某研究实验室正在为一个新项目选择一名研究人员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要具备客户沟通经验。
2. 候选人需要有公开表达或演讲经验。
3. 候选人需要具备机器学习经验。
4. 候选人需要具备质量保证经验。
5. 候选人需要具有本地工作许可。

候选人：
A. Reese 没有本地工作许可，Reese 有机器学习项目经验。另外，Reese 没有公开表达或演讲经验，Reese 有客户沟通经验，Reese 有质量保证经验。
B. Emerson 有机器学习项目经验，Emerson 没有公开表达或演讲经验。另外，Emerson 具有本地工作许可，Emerson 没有质量保证经验，Emerson 有客户沟通经验。
C. Harper 有质量保证经验，Harper 有客户沟通经验。另外，Harper 具有本地工作许可，Harper 有机器学习项目经验，Harper 有公开表达或演讲经验。
D. Sawyer 没有客户沟通经验，Sawyer 没有机器学习方面的实践经验。另外，Sawyer 有公开表达或演讲经验，Sawyer 没有本地工作许可，Sawyer 没有质量保证经验。

哪位候选人满足所有要求？

约束与 violation signature：

- `C1` `has_client_communication_experience=True`：候选人需要具备客户沟通经验。
- `C2` `has_public_speaking_experience=True`：候选人需要有公开表达或演讲经验。
- `C3` `has_ml_experience=True`：候选人需要具备机器学习经验。
- `C4` `has_quality_assurance_experience=True`：候选人需要具备质量保证经验。
- `C5` `has_local_work_permit=True`：候选人需要具有本地工作许可。

- `A` violation: `['C2', 'C5']`
- `B` violation: `['C2', 'C4']`
- `C` violation: `[]`
- `D` violation: `['C1', 'C3', 'C4', 'C5']`

## 71. attr_en_000071_zh_view

- source: `attr_en_000071_original`
- scenario: `expert_recruitment`
- option_closeness: `hard`
- structural_complexity: `low`
- gold: `C`

某研究实验室正在为一个新项目选择一名研究人员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人不能存在日程冲突。
2. 候选人不能存在与项目相关的利益冲突。
3. 候选人需要完成过相关培训。

候选人：
A. Marley 与项目存在利益冲突。另外，Marley 完成过相关培训，Marley 不存在日程冲突。
B. Kris 不存在项目相关的利益冲突。另外，Kris 完成过相关培训，Kris 存在与项目安排冲突的日程。
C. Reese 完成过相关培训。另外，Reese 不存在项目相关的利益冲突，Reese 不存在日程冲突。
D. Harper 不存在项目相关的利益冲突。另外，Harper 没有完成相关培训，Harper 不存在日程冲突。

哪位候选人满足所有要求？

约束与 violation signature：

- `C1` `has_schedule_conflict=False`：候选人不能存在日程冲突。
- `C2` `has_conflict=False`：候选人不能存在与项目相关的利益冲突。
- `C3` `has_prior_training=True`：候选人需要完成过相关培训。

- `A` violation: `['C2']`
- `B` violation: `['C1']`
- `C` violation: `[]`
- `D` violation: `['C3']`

## 72. attr_en_000072_zh_view

- source: `attr_en_000072_original`
- scenario: `expert_recruitment`
- option_closeness: `medium`
- structural_complexity: `low`
- gold: `D`

某研究实验室正在为一个新项目选择一名研究人员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要持有相关证书。
2. 候选人需要上午可以参与工作。
3. 候选人需要能够使用英语进行工作沟通。

候选人：
A. Robin 上午可以参与工作。另外，Robin 不能用英语进行工作沟通，Robin 没有相关专业证书。
B. Harper 能够用英语进行工作沟通。另外，Harper 持有相关专业证书，Harper 上午无法参与工作。
C. Reese 持有相关专业证书。另外，Reese 不能用英语进行工作沟通，Reese 上午可以参与工作。
D. Indigo 持有相关专业证书。另外，Indigo 能够用英语进行工作沟通，Indigo 上午可以参与工作。

哪位候选人满足所有要求？

约束与 violation signature：

- `C1` `has_certificate=True`：候选人需要持有相关证书。
- `C2` `available_morning=True`：候选人需要上午可以参与工作。
- `C3` `speaks_english=True`：候选人需要能够使用英语进行工作沟通。

- `A` violation: `['C1', 'C3']`
- `B` violation: `['C2']`
- `C` violation: `['C3']`
- `D` violation: `[]`

## 73. attr_en_000073_zh_view

- source: `attr_en_000073_original`
- scenario: `expert_recruitment`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `C`

某研究实验室正在为一个新项目选择一名研究人员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要下个月可以加入项目。
2. 候选人需要周二可以参与工作。
3. 候选人需要具备安全许可。
4. 候选人需要具备客户沟通经验。

候选人：
A. Payton 不具备安全许可，Payton 没有客户沟通经验。另外，Payton 周二可以参与工作，Payton 下个月可以加入项目。
B. Briar 周二无法参与工作，Briar 具备安全许可。另外，Briar 下个月可以加入项目，Briar 有客户沟通经验。
C. Jordan 具备安全许可，Jordan 下个月可以加入项目。另外，Jordan 周二可以参与工作，Jordan 有客户沟通经验。
D. Drew 具备安全许可，Drew 周二可以参与工作。另外，Drew 下个月无法加入项目，Drew 有客户沟通经验。

哪位候选人满足所有要求？

约束与 violation signature：

- `C1` `available_next_month=True`：候选人需要下个月可以加入项目。
- `C2` `available_tuesday=True`：候选人需要周二可以参与工作。
- `C3` `has_security_clearance=True`：候选人需要具备安全许可。
- `C4` `has_client_communication_experience=True`：候选人需要具备客户沟通经验。

- `A` violation: `['C3', 'C4']`
- `B` violation: `['C2']`
- `C` violation: `[]`
- `D` violation: `['C1']`

## 74. attr_en_000074_zh_view

- source: `attr_en_000074_original`
- scenario: `expert_recruitment`
- option_closeness: `medium`
- structural_complexity: `low`
- gold: `A`

某研究实验室正在为一个新项目选择一名研究人员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要有研究项目经验。
2. 候选人需要完成过相关培训。
3. 候选人需要了解相关项目领域。

候选人：
A. Arden 完成过相关培训。另外，Arden 熟悉相关项目领域，Arden 参与过研究项目。
B. Robin 没有完成相关培训。另外，Robin 参与过研究项目，Robin 不熟悉相关项目领域。
C. Parker 熟悉相关项目领域。另外，Parker 完成过相关培训，Parker 没有研究项目经历。
D. Quinn 完成过相关培训。另外，Quinn 参与过研究项目，Quinn 不熟悉相关项目领域。

哪位候选人满足所有要求？

约束与 violation signature：

- `C1` `has_research_experience=True`：候选人需要有研究项目经验。
- `C2` `has_prior_training=True`：候选人需要完成过相关培训。
- `C3` `has_domain_knowledge=True`：候选人需要了解相关项目领域。

- `A` violation: `[]`
- `B` violation: `['C2', 'C3']`
- `C` violation: `['C1']`
- `D` violation: `['C3']`

## 75. attr_en_000075_zh_view

- source: `attr_en_000075_original`
- scenario: `availability_selection`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `C`

协调人需要从四名候选人中找出唯一符合日程和参与要求的人。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要下个月可以加入项目。
2. 候选人不能需要额外专用设备支持。
3. 候选人需要周末可以参与工作。
4. 候选人不能存在日程冲突。

候选人：
A. Skyler 需要额外专用设备支持，Skyler 下个月可以加入项目。另外，Skyler 周末无法参与工作，Skyler 不存在日程冲突。
B. Harper 下个月无法加入项目，Harper 周末可以参与工作。另外，Harper 不需要额外专用设备支持，Harper 不存在日程冲突。
C. Sawyer 不存在日程冲突，Sawyer 周末可以参与工作。另外，Sawyer 不需要额外专用设备支持，Sawyer 下个月可以加入项目。
D. Morgan 周末可以参与工作，Morgan 不需要额外专用设备支持。另外，Morgan 下个月可以加入项目，Morgan 存在与项目安排冲突的日程。

哪位候选人符合全部要求？

约束与 violation signature：

- `C1` `available_next_month=True`：候选人需要下个月可以加入项目。
- `C2` `requires_extra_equipment=False`：候选人不能需要额外专用设备支持。
- `C3` `available_weekend=True`：候选人需要周末可以参与工作。
- `C4` `has_schedule_conflict=False`：候选人不能存在日程冲突。

- `A` violation: `['C2', 'C3']`
- `B` violation: `['C1']`
- `C` violation: `[]`
- `D` violation: `['C4']`

## 76. attr_en_000076_zh_view

- source: `attr_en_000076_original`
- scenario: `project_assignment`
- option_closeness: `medium`
- structural_complexity: `low`
- gold: `B`

项目团队需要为一项专门任务分配一名成员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要接受灵活工时安排。
2. 候选人需要能够在不需要额外监督的情况下工作。
3. 候选人需要能够独立工作。

候选人：
A. Elliot 不接受灵活工时安排。另外，Elliot 不能独立完成工作，Elliot 不需要额外监督也能完成工作。
B. Logan 能够独立工作。另外，Logan 不需要额外监督也能完成工作，Logan 接受灵活工时安排。
C. Parker 不需要额外监督也能完成工作。另外，Parker 能够独立工作，Parker 不接受灵活工时安排。
D. Marley 能够独立工作。另外，Marley 接受灵活工时安排，Marley 需要额外监督才能完成工作。

哪位候选人适合承担这项任务？

约束与 violation signature：

- `C1` `accepts_flexible_hours=True`：候选人需要接受灵活工时安排。
- `C2` `needs_supervision=False`：候选人需要能够在不需要额外监督的情况下工作。
- `C3` `can_work_independently=True`：候选人需要能够独立工作。

- `A` violation: `['C1', 'C3']`
- `B` violation: `[]`
- `C` violation: `['C1']`
- `D` violation: `['C2']`

## 77. attr_en_000077_zh_view

- source: `attr_en_000077_original`
- scenario: `availability_selection`
- option_closeness: `easy`
- structural_complexity: `high`
- gold: `C`

协调人需要从四名候选人中找出唯一符合日程和参与要求的人。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要能够现场参与工作。
2. 候选人需要周一可以参与工作。
3. 候选人不能需要额外专用设备支持。
4. 候选人需要上午可以参与工作。
5. 候选人需要下个月可以加入项目。

候选人：
A. Arden 需要额外专用设备支持，Arden 上午无法参与工作。另外，Arden 不能现场参与工作，Arden 下个月无法加入项目，Arden 周一无法参与工作。
B. Sage 周一可以参与工作，Sage 下个月无法加入项目。另外，Sage 能够现场参与工作，Sage 需要额外专用设备支持，Sage 上午可以参与工作。
C. Indigo 不需要额外专用设备支持，Indigo 周一可以参与工作。另外，Indigo 下个月可以加入项目，Indigo 上午可以参与工作，Indigo 能够现场参与工作。
D. Finley 周一无法参与工作，Finley 下个月可以加入项目。另外，Finley 不需要额外专用设备支持，Finley 上午可以参与工作，Finley 不能现场参与工作。

哪位候选人符合全部要求？

约束与 violation signature：

- `C1` `can_work_onsite=True`：候选人需要能够现场参与工作。
- `C2` `available_monday=True`：候选人需要周一可以参与工作。
- `C3` `requires_extra_equipment=False`：候选人不能需要额外专用设备支持。
- `C4` `available_morning=True`：候选人需要上午可以参与工作。
- `C5` `available_next_month=True`：候选人需要下个月可以加入项目。

- `A` violation: `['C1', 'C2', 'C3', 'C4', 'C5']`
- `B` violation: `['C3', 'C5']`
- `C` violation: `[]`
- `D` violation: `['C1', 'C2']`

## 78. attr_en_000078_zh_view

- source: `attr_en_000078_original`
- scenario: `expert_recruitment`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `B`

某研究实验室正在为一个新项目选择一名研究人员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要有管理或协调经验。
2. 候选人需要熟悉统计方法。
3. 候选人需要参与过项目执行工作。
4. 候选人需要具备数据分析经验。

候选人：
A. Tatum 参与过项目执行，Tatum 没有实际数据分析经历。另外，Tatum 熟悉统计方法，Tatum 曾经负责过项目或团队协调。
B. Payton 熟悉统计方法，Payton 参与过项目执行。另外，Payton 曾经负责过项目或团队协调，Payton 做过数据分析工作。
C. Drew 没有管理或协调项目的经历，Drew 没有参与过项目执行。另外，Drew 熟悉统计方法，Drew 做过数据分析工作。
D. Hayden 不熟悉统计方法，Hayden 曾经负责过项目或团队协调。另外，Hayden 做过数据分析工作，Hayden 参与过项目执行。

哪位候选人满足所有要求？

约束与 violation signature：

- `C1` `has_management_experience=True`：候选人需要有管理或协调经验。
- `C2` `familiar_with_statistics=True`：候选人需要熟悉统计方法。
- `C3` `has_project_experience=True`：候选人需要参与过项目执行工作。
- `C4` `has_data_analysis_experience=True`：候选人需要具备数据分析经验。

- `A` violation: `['C4']`
- `B` violation: `[]`
- `C` violation: `['C1', 'C3']`
- `D` violation: `['C2']`

## 79. attr_en_000079_zh_view

- source: `attr_en_000079_original`
- scenario: `project_assignment`
- option_closeness: `medium`
- structural_complexity: `low`
- gold: `B`

项目团队需要为一项专门任务分配一名成员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要能够在不需要额外监督的情况下工作。
2. 候选人需要完成过相关培训。
3. 候选人需要参与过项目执行工作。

候选人：
A. Sage 需要额外监督才能完成工作。另外，Sage 参与过项目执行，Sage 完成过相关培训。
B. Finley 完成过相关培训。另外，Finley 不需要额外监督也能完成工作，Finley 参与过项目执行。
C. Jordan 没有参与过项目执行。另外，Jordan 需要额外监督才能完成工作，Jordan 完成过相关培训。
D. Morgan 参与过项目执行。另外，Morgan 没有完成相关培训，Morgan 不需要额外监督也能完成工作。

哪位候选人适合承担这项任务？

约束与 violation signature：

- `C1` `needs_supervision=False`：候选人需要能够在不需要额外监督的情况下工作。
- `C2` `has_prior_training=True`：候选人需要完成过相关培训。
- `C3` `has_project_experience=True`：候选人需要参与过项目执行工作。

- `A` violation: `['C1']`
- `B` violation: `[]`
- `C` violation: `['C1', 'C3']`
- `D` violation: `['C2']`

## 80. attr_en_000080_zh_view

- source: `attr_en_000080_original`
- scenario: `project_assignment`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `C`

项目团队需要为一项专门任务分配一名成员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要有管理或协调经验。
2. 候选人需要具备团队协作经验。
3. 候选人需要接受灵活工时安排。
4. 候选人需要有公开表达或演讲经验。

候选人：
A. Quinn 有公开表达或演讲经验，Quinn 不接受灵活工时安排。另外，Quinn 没有管理或协调项目的经历，Quinn 有团队协作经验。
B. Taylor 缺少团队协作经验，Taylor 曾经负责过项目或团队协调。另外，Taylor 接受灵活工时安排，Taylor 有公开表达或演讲经验。
C. Gray 曾经负责过项目或团队协调，Gray 接受灵活工时安排。另外，Gray 有团队协作经验，Gray 有公开表达或演讲经验。
D. Wren 有团队协作经验，Wren 曾经负责过项目或团队协调。另外，Wren 没有公开表达或演讲经验，Wren 接受灵活工时安排。

哪位候选人适合承担这项任务？

约束与 violation signature：

- `C1` `has_management_experience=True`：候选人需要有管理或协调经验。
- `C2` `has_teamwork_experience=True`：候选人需要具备团队协作经验。
- `C3` `accepts_flexible_hours=True`：候选人需要接受灵活工时安排。
- `C4` `has_public_speaking_experience=True`：候选人需要有公开表达或演讲经验。

- `A` violation: `['C1', 'C3']`
- `B` violation: `['C2']`
- `C` violation: `[]`
- `D` violation: `['C4']`

## 81. attr_en_000081_zh_view

- source: `attr_en_000081_original`
- scenario: `availability_selection`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `D`

协调人需要从四名候选人中找出唯一符合日程和参与要求的人。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要能够远程工作。
2. 候选人需要上午可以参与工作。
3. 候选人需要能够现场参与工作。
4. 候选人不能存在日程冲突。

候选人：
A. Sage 能够现场参与工作，Sage 能够远程工作。另外，Sage 不存在日程冲突，Sage 上午无法参与工作。
B. Robin 上午可以参与工作，Robin 能够现场参与工作。另外，Robin 不能远程工作，Robin 存在与项目安排冲突的日程。
C. Kris 不能现场参与工作，Kris 能够远程工作。另外，Kris 上午可以参与工作，Kris 不存在日程冲突。
D. Drew 不存在日程冲突，Drew 上午可以参与工作。另外，Drew 能够远程工作，Drew 能够现场参与工作。

哪位候选人符合全部要求？

约束与 violation signature：

- `C1` `can_work_remote=True`：候选人需要能够远程工作。
- `C2` `available_morning=True`：候选人需要上午可以参与工作。
- `C3` `can_work_onsite=True`：候选人需要能够现场参与工作。
- `C4` `has_schedule_conflict=False`：候选人不能存在日程冲突。

- `A` violation: `['C2']`
- `B` violation: `['C1', 'C4']`
- `C` violation: `['C3']`
- `D` violation: `[]`

## 82. attr_en_000082_zh_view

- source: `attr_en_000082_original`
- scenario: `project_assignment`
- option_closeness: `easy`
- structural_complexity: `high`
- gold: `B`

项目团队需要为一项专门任务分配一名成员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要能够现场参与工作。
2. 候选人需要能够使用英语进行工作沟通。
3. 候选人需要接受灵活工时安排。
4. 候选人需要愿意出差。
5. 候选人需要具备质量保证经验。

候选人：
A. Marley 能够用英语进行工作沟通，Marley 有质量保证经验。另外，Marley 不愿意出差，Marley 接受灵活工时安排，Marley 不能现场参与工作。
B. Jordan 接受灵活工时安排，Jordan 有质量保证经验。另外，Jordan 能够现场参与工作，Jordan 能够用英语进行工作沟通，Jordan 愿意出差。
C. Logan 能够用英语进行工作沟通，Logan 不愿意出差。另外，Logan 不能现场参与工作，Logan 不接受灵活工时安排，Logan 没有质量保证经验。
D. Robin 不愿意出差，Robin 不能用英语进行工作沟通。另外，Robin 接受灵活工时安排，Robin 能够现场参与工作，Robin 有质量保证经验。

哪位候选人适合承担这项任务？

约束与 violation signature：

- `C1` `can_work_onsite=True`：候选人需要能够现场参与工作。
- `C2` `speaks_english=True`：候选人需要能够使用英语进行工作沟通。
- `C3` `accepts_flexible_hours=True`：候选人需要接受灵活工时安排。
- `C4` `willing_to_travel=True`：候选人需要愿意出差。
- `C5` `has_quality_assurance_experience=True`：候选人需要具备质量保证经验。

- `A` violation: `['C1', 'C4']`
- `B` violation: `[]`
- `C` violation: `['C1', 'C3', 'C4', 'C5']`
- `D` violation: `['C2', 'C4']`

## 83. attr_en_000083_zh_view

- source: `attr_en_000083_original`
- scenario: `availability_selection`
- option_closeness: `easy`
- structural_complexity: `high`
- gold: `A`

协调人需要从四名候选人中找出唯一符合日程和参与要求的人。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要下个月可以加入项目。
2. 候选人需要周一可以参与工作。
3. 候选人需要能够远程工作。
4. 候选人需要上午可以参与工作。
5. 候选人需要周末可以参与工作。

候选人：
A. Tatum 上午可以参与工作，Tatum 周一可以参与工作。另外，Tatum 能够远程工作，Tatum 下个月可以加入项目，Tatum 周末可以参与工作。
B. Kris 周末可以参与工作，Kris 能够远程工作。另外，Kris 下个月无法加入项目，Kris 周一可以参与工作，Kris 上午无法参与工作。
C. Jamie 不能远程工作，Jamie 周一无法参与工作。另外，Jamie 周末无法参与工作，Jamie 下个月无法加入项目，Jamie 上午可以参与工作。
D. Indigo 能够远程工作，Indigo 下个月无法加入项目。另外，Indigo 周一可以参与工作，Indigo 上午可以参与工作，Indigo 周末无法参与工作。

哪位候选人符合全部要求？

约束与 violation signature：

- `C1` `available_next_month=True`：候选人需要下个月可以加入项目。
- `C2` `available_monday=True`：候选人需要周一可以参与工作。
- `C3` `can_work_remote=True`：候选人需要能够远程工作。
- `C4` `available_morning=True`：候选人需要上午可以参与工作。
- `C5` `available_weekend=True`：候选人需要周末可以参与工作。

- `A` violation: `[]`
- `B` violation: `['C1', 'C4']`
- `C` violation: `['C1', 'C2', 'C3', 'C5']`
- `D` violation: `['C1', 'C5']`

## 84. attr_en_000084_zh_view

- source: `attr_en_000084_original`
- scenario: `availability_selection`
- option_closeness: `medium`
- structural_complexity: `low`
- gold: `D`

协调人需要从四名候选人中找出唯一符合日程和参与要求的人。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要下午可以参与工作。
2. 候选人需要能够远程工作。
3. 候选人需要接受灵活工时安排。

候选人：
A. Payton 下午可以参与工作。另外，Payton 接受灵活工时安排，Payton 不能远程工作。
B. Tatum 不接受灵活工时安排。另外，Tatum 下午可以参与工作，Tatum 不能远程工作。
C. Sawyer 接受灵活工时安排。另外，Sawyer 能够远程工作，Sawyer 下午无法参与工作。
D. Parker 接受灵活工时安排。另外，Parker 能够远程工作，Parker 下午可以参与工作。

哪位候选人符合全部要求？

约束与 violation signature：

- `C1` `available_afternoon=True`：候选人需要下午可以参与工作。
- `C2` `can_work_remote=True`：候选人需要能够远程工作。
- `C3` `accepts_flexible_hours=True`：候选人需要接受灵活工时安排。

- `A` violation: `['C2']`
- `B` violation: `['C2', 'C3']`
- `C` violation: `['C1']`
- `D` violation: `[]`

## 85. attr_en_000085_zh_view

- source: `attr_en_000085_original`
- scenario: `availability_selection`
- option_closeness: `medium`
- structural_complexity: `low`
- gold: `D`

协调人需要从四名候选人中找出唯一符合日程和参与要求的人。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要下个月可以加入项目。
2. 候选人需要上午可以参与工作。
3. 候选人需要下午可以参与工作。

候选人：
A. Logan 上午可以参与工作。另外，Logan 下午无法参与工作，Logan 下个月可以加入项目。
B. Harper 下个月无法加入项目。另外，Harper 下午可以参与工作，Harper 上午可以参与工作。
C. Emerson 上午无法参与工作。另外，Emerson 下个月无法加入项目，Emerson 下午可以参与工作。
D. Morgan 上午可以参与工作。另外，Morgan 下午可以参与工作，Morgan 下个月可以加入项目。

哪位候选人符合全部要求？

约束与 violation signature：

- `C1` `available_next_month=True`：候选人需要下个月可以加入项目。
- `C2` `available_morning=True`：候选人需要上午可以参与工作。
- `C3` `available_afternoon=True`：候选人需要下午可以参与工作。

- `A` violation: `['C3']`
- `B` violation: `['C1']`
- `C` violation: `['C1', 'C2']`
- `D` violation: `[]`

## 86. attr_en_000086_zh_view

- source: `attr_en_000086_original`
- scenario: `availability_selection`
- option_closeness: `hard`
- structural_complexity: `low`
- gold: `A`

协调人需要从四名候选人中找出唯一符合日程和参与要求的人。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要周一可以参与工作。
2. 候选人需要接受灵活工时安排。
3. 候选人需要周末可以参与工作。

候选人：
A. Ellis 周一可以参与工作。另外，Ellis 周末可以参与工作，Ellis 接受灵活工时安排。
B. Noel 不接受灵活工时安排。另外，Noel 周末可以参与工作，Noel 周一可以参与工作。
C. Kris 接受灵活工时安排。另外，Kris 周一可以参与工作，Kris 周末无法参与工作。
D. Marley 接受灵活工时安排。另外，Marley 周一无法参与工作，Marley 周末可以参与工作。

哪位候选人符合全部要求？

约束与 violation signature：

- `C1` `available_monday=True`：候选人需要周一可以参与工作。
- `C2` `accepts_flexible_hours=True`：候选人需要接受灵活工时安排。
- `C3` `available_weekend=True`：候选人需要周末可以参与工作。

- `A` violation: `[]`
- `B` violation: `['C2']`
- `C` violation: `['C3']`
- `D` violation: `['C1']`

## 87. attr_en_000087_zh_view

- source: `attr_en_000087_original`
- scenario: `expert_recruitment`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `D`

某研究实验室正在为一个新项目选择一名研究人员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要能够在不需要额外监督的情况下工作。
2. 候选人需要上午可以参与工作。
3. 候选人需要具有本地工作许可。
4. 候选人需要有管理或协调经验。

候选人：
A. Parker 具有本地工作许可，Parker 上午可以参与工作。另外，Parker 没有管理或协调项目的经历，Parker 不需要额外监督也能完成工作。
B. Skyler 具有本地工作许可，Skyler 曾经负责过项目或团队协调。另外，Skyler 需要额外监督才能完成工作，Skyler 上午无法参与工作。
C. Jordan 没有本地工作许可，Jordan 不需要额外监督也能完成工作。另外，Jordan 曾经负责过项目或团队协调，Jordan 上午可以参与工作。
D. Briar 曾经负责过项目或团队协调，Briar 具有本地工作许可。另外，Briar 不需要额外监督也能完成工作，Briar 上午可以参与工作。

哪位候选人满足所有要求？

约束与 violation signature：

- `C1` `needs_supervision=False`：候选人需要能够在不需要额外监督的情况下工作。
- `C2` `available_morning=True`：候选人需要上午可以参与工作。
- `C3` `has_local_work_permit=True`：候选人需要具有本地工作许可。
- `C4` `has_management_experience=True`：候选人需要有管理或协调经验。

- `A` violation: `['C4']`
- `B` violation: `['C1', 'C2']`
- `C` violation: `['C3']`
- `D` violation: `[]`

## 88. attr_en_000088_zh_view

- source: `attr_en_000088_original`
- scenario: `expert_recruitment`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `A`

某研究实验室正在为一个新项目选择一名研究人员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要有公开表达或演讲经验。
2. 候选人需要具备数据分析经验。
3. 候选人需要上午可以参与工作。
4. 候选人需要有研究项目经验。

候选人：
A. Arden 做过数据分析工作，Arden 有公开表达或演讲经验。另外，Arden 参与过研究项目，Arden 上午可以参与工作。
B. Tatum 有公开表达或演讲经验，Tatum 上午可以参与工作。另外，Tatum 做过数据分析工作，Tatum 没有研究项目经历。
C. Robin 上午无法参与工作，Robin 没有实际数据分析经历。另外，Robin 有公开表达或演讲经验，Robin 参与过研究项目。
D. Kendall 没有公开表达或演讲经验，Kendall 上午可以参与工作。另外，Kendall 做过数据分析工作，Kendall 参与过研究项目。

哪位候选人满足所有要求？

约束与 violation signature：

- `C1` `has_public_speaking_experience=True`：候选人需要有公开表达或演讲经验。
- `C2` `has_data_analysis_experience=True`：候选人需要具备数据分析经验。
- `C3` `available_morning=True`：候选人需要上午可以参与工作。
- `C4` `has_research_experience=True`：候选人需要有研究项目经验。

- `A` violation: `[]`
- `B` violation: `['C4']`
- `C` violation: `['C2', 'C3']`
- `D` violation: `['C1']`

## 89. attr_en_000089_zh_view

- source: `attr_en_000089_original`
- scenario: `expert_recruitment`
- option_closeness: `hard`
- structural_complexity: `low`
- gold: `A`

某研究实验室正在为一个新项目选择一名研究人员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要上午可以参与工作。
2. 候选人需要下个月可以加入项目。
3. 候选人需要有公开表达或演讲经验。

候选人：
A. Indigo 有公开表达或演讲经验。另外，Indigo 上午可以参与工作，Indigo 下个月可以加入项目。
B. Skyler 上午可以参与工作。另外，Skyler 有公开表达或演讲经验，Skyler 下个月无法加入项目。
C. Avery 上午无法参与工作。另外，Avery 有公开表达或演讲经验，Avery 下个月可以加入项目。
D. Briar 下个月可以加入项目。另外，Briar 没有公开表达或演讲经验，Briar 上午可以参与工作。

哪位候选人满足所有要求？

约束与 violation signature：

- `C1` `available_morning=True`：候选人需要上午可以参与工作。
- `C2` `available_next_month=True`：候选人需要下个月可以加入项目。
- `C3` `has_public_speaking_experience=True`：候选人需要有公开表达或演讲经验。

- `A` violation: `[]`
- `B` violation: `['C2']`
- `C` violation: `['C1']`
- `D` violation: `['C3']`

## 90. attr_en_000090_zh_view

- source: `attr_en_000090_original`
- scenario: `expert_recruitment`
- option_closeness: `medium`
- structural_complexity: `medium`
- gold: `D`

某研究实验室正在为一个新项目选择一名研究人员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要能够在不需要额外监督的情况下工作。
2. 候选人不能存在与项目相关的利益冲突。
3. 候选人需要完成过相关培训。
4. 候选人需要具备质量保证经验。

候选人：
A. Blair 有质量保证经验，Blair 与项目存在利益冲突。另外，Blair 不需要额外监督也能完成工作，Blair 完成过相关培训。
B. Arden 没有完成相关培训，Arden 需要额外监督才能完成工作。另外，Arden 不存在项目相关的利益冲突，Arden 有质量保证经验。
C. Payton 不存在项目相关的利益冲突，Payton 不需要额外监督也能完成工作。另外，Payton 完成过相关培训，Payton 没有质量保证经验。
D. Finley 不存在项目相关的利益冲突，Finley 有质量保证经验。另外，Finley 不需要额外监督也能完成工作，Finley 完成过相关培训。

哪位候选人满足所有要求？

约束与 violation signature：

- `C1` `needs_supervision=False`：候选人需要能够在不需要额外监督的情况下工作。
- `C2` `has_conflict=False`：候选人不能存在与项目相关的利益冲突。
- `C3` `has_prior_training=True`：候选人需要完成过相关培训。
- `C4` `has_quality_assurance_experience=True`：候选人需要具备质量保证经验。

- `A` violation: `['C2']`
- `B` violation: `['C1', 'C3']`
- `C` violation: `['C4']`
- `D` violation: `[]`

## 91. attr_en_000091_zh_view

- source: `attr_en_000091_original`
- scenario: `project_assignment`
- option_closeness: `medium`
- structural_complexity: `low`
- gold: `D`

项目团队需要为一项专门任务分配一名成员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要具备质量保证经验。
2. 候选人需要愿意出差。
3. 候选人需要具备客户沟通经验。

候选人：
A. Harper 愿意出差。另外，Harper 有客户沟通经验，Harper 没有质量保证经验。
B. Gray 有客户沟通经验。另外，Gray 不愿意出差，Gray 没有质量保证经验。
C. Hayden 愿意出差。另外，Hayden 没有客户沟通经验，Hayden 有质量保证经验。
D. Jamie 有质量保证经验。另外，Jamie 有客户沟通经验，Jamie 愿意出差。

哪位候选人适合承担这项任务？

约束与 violation signature：

- `C1` `has_quality_assurance_experience=True`：候选人需要具备质量保证经验。
- `C2` `willing_to_travel=True`：候选人需要愿意出差。
- `C3` `has_client_communication_experience=True`：候选人需要具备客户沟通经验。

- `A` violation: `['C1']`
- `B` violation: `['C1', 'C2']`
- `C` violation: `['C3']`
- `D` violation: `[]`

## 92. attr_en_000092_zh_view

- source: `attr_en_000092_original`
- scenario: `availability_selection`
- option_closeness: `hard`
- structural_complexity: `low`
- gold: `B`

协调人需要从四名候选人中找出唯一符合日程和参与要求的人。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要上午可以参与工作。
2. 候选人不能存在日程冲突。
3. 候选人需要周二可以参与工作。

候选人：
A. Avery 存在与项目安排冲突的日程。另外，Avery 上午可以参与工作，Avery 周二可以参与工作。
B. Jamie 不存在日程冲突。另外，Jamie 周二可以参与工作，Jamie 上午可以参与工作。
C. Arden 不存在日程冲突。另外，Arden 上午无法参与工作，Arden 周二可以参与工作。
D. Devon 不存在日程冲突。另外，Devon 上午可以参与工作，Devon 周二无法参与工作。

哪位候选人符合全部要求？

约束与 violation signature：

- `C1` `available_morning=True`：候选人需要上午可以参与工作。
- `C2` `has_schedule_conflict=False`：候选人不能存在日程冲突。
- `C3` `available_tuesday=True`：候选人需要周二可以参与工作。

- `A` violation: `['C2']`
- `B` violation: `[]`
- `C` violation: `['C1']`
- `D` violation: `['C3']`

## 93. attr_en_000093_zh_view

- source: `attr_en_000093_original`
- scenario: `project_assignment`
- option_closeness: `hard`
- structural_complexity: `low`
- gold: `C`

项目团队需要为一项专门任务分配一名成员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要周末可以参与工作。
2. 候选人需要熟悉统计方法。
3. 候选人需要了解相关项目领域。

候选人：
A. Elliot 熟悉相关项目领域。另外，Elliot 不熟悉统计方法，Elliot 周末可以参与工作。
B. Indigo 熟悉统计方法。另外，Indigo 周末无法参与工作，Indigo 熟悉相关项目领域。
C. Jamie 熟悉相关项目领域。另外，Jamie 熟悉统计方法，Jamie 周末可以参与工作。
D. Kendall 熟悉统计方法。另外，Kendall 不熟悉相关项目领域，Kendall 周末可以参与工作。

哪位候选人适合承担这项任务？

约束与 violation signature：

- `C1` `available_weekend=True`：候选人需要周末可以参与工作。
- `C2` `familiar_with_statistics=True`：候选人需要熟悉统计方法。
- `C3` `has_domain_knowledge=True`：候选人需要了解相关项目领域。

- `A` violation: `['C2']`
- `B` violation: `['C1']`
- `C` violation: `[]`
- `D` violation: `['C3']`

## 94. attr_en_000094_zh_view

- source: `attr_en_000094_original`
- scenario: `project_assignment`
- option_closeness: `easy`
- structural_complexity: `high`
- gold: `D`

项目团队需要为一项专门任务分配一名成员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人不能存在与项目相关的利益冲突。
2. 候选人需要有研究项目经验。
3. 候选人需要具备安全许可。
4. 候选人需要了解相关项目领域。
5. 候选人需要有管理或协调经验。

候选人：
A. Payton 熟悉相关项目领域，Payton 不存在项目相关的利益冲突。另外，Payton 具备安全许可，Payton 没有研究项目经历，Payton 没有管理或协调项目的经历。
B. Finley 不具备安全许可，Finley 没有管理或协调项目的经历。另外，Finley 不熟悉相关项目领域，Finley 与项目存在利益冲突，Finley 没有研究项目经历。
C. Harper 熟悉相关项目领域，Harper 没有管理或协调项目的经历。另外，Harper 参与过研究项目，Harper 具备安全许可，Harper 与项目存在利益冲突。
D. Jordan 参与过研究项目，Jordan 曾经负责过项目或团队协调。另外，Jordan 不存在项目相关的利益冲突，Jordan 具备安全许可，Jordan 熟悉相关项目领域。

哪位候选人适合承担这项任务？

约束与 violation signature：

- `C1` `has_conflict=False`：候选人不能存在与项目相关的利益冲突。
- `C2` `has_research_experience=True`：候选人需要有研究项目经验。
- `C3` `has_security_clearance=True`：候选人需要具备安全许可。
- `C4` `has_domain_knowledge=True`：候选人需要了解相关项目领域。
- `C5` `has_management_experience=True`：候选人需要有管理或协调经验。

- `A` violation: `['C2', 'C5']`
- `B` violation: `['C1', 'C2', 'C3', 'C4', 'C5']`
- `C` violation: `['C1', 'C5']`
- `D` violation: `[]`

## 95. attr_en_000095_zh_view

- source: `attr_en_000095_original`
- scenario: `availability_selection`
- option_closeness: `easy`
- structural_complexity: `high`
- gold: `A`

协调人需要从四名候选人中找出唯一符合日程和参与要求的人。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要上午可以参与工作。
2. 候选人需要下午可以参与工作。
3. 候选人需要周末可以参与工作。
4. 候选人需要周一可以参与工作。
5. 候选人需要能够现场参与工作。

候选人：
A. Logan 能够现场参与工作，Logan 上午可以参与工作。另外，Logan 下午可以参与工作，Logan 周一可以参与工作，Logan 周末可以参与工作。
B. Hayden 下午无法参与工作，Hayden 周末可以参与工作。另外，Hayden 周一无法参与工作，Hayden 能够现场参与工作，Hayden 上午可以参与工作。
C. Wren 周末无法参与工作，Wren 下午无法参与工作。另外，Wren 能够现场参与工作，Wren 周一无法参与工作，Wren 上午无法参与工作。
D. Gray 周末可以参与工作，Gray 上午无法参与工作。另外，Gray 下午可以参与工作，Gray 周一可以参与工作，Gray 不能现场参与工作。

哪位候选人符合全部要求？

约束与 violation signature：

- `C1` `available_morning=True`：候选人需要上午可以参与工作。
- `C2` `available_afternoon=True`：候选人需要下午可以参与工作。
- `C3` `available_weekend=True`：候选人需要周末可以参与工作。
- `C4` `available_monday=True`：候选人需要周一可以参与工作。
- `C5` `can_work_onsite=True`：候选人需要能够现场参与工作。

- `A` violation: `[]`
- `B` violation: `['C2', 'C4']`
- `C` violation: `['C1', 'C2', 'C3', 'C4']`
- `D` violation: `['C1', 'C5']`

## 96. attr_en_000096_zh_view

- source: `attr_en_000096_original`
- scenario: `availability_selection`
- option_closeness: `easy`
- structural_complexity: `high`
- gold: `B`

协调人需要从四名候选人中找出唯一符合日程和参与要求的人。
被选中的人必须满足以下全部要求：

要求：
1. 候选人不能存在日程冲突。
2. 候选人需要接受灵活工时安排。
3. 候选人需要周一可以参与工作。
4. 候选人不能需要额外专用设备支持。
5. 候选人需要能够远程工作。

候选人：
A. Arden 接受灵活工时安排，Arden 周一可以参与工作。另外，Arden 不需要额外专用设备支持，Arden 不能远程工作，Arden 存在与项目安排冲突的日程。
B. Rowan 周一可以参与工作，Rowan 能够远程工作。另外，Rowan 不需要额外专用设备支持，Rowan 不存在日程冲突，Rowan 接受灵活工时安排。
C. Cameron 能够远程工作，Cameron 需要额外专用设备支持。另外，Cameron 不存在日程冲突，Cameron 周一无法参与工作，Cameron 接受灵活工时安排。
D. Parker 能够远程工作，Parker 需要额外专用设备支持。另外，Parker 周一可以参与工作，Parker 不存在日程冲突，Parker 不接受灵活工时安排。

哪位候选人符合全部要求？

约束与 violation signature：

- `C1` `has_schedule_conflict=False`：候选人不能存在日程冲突。
- `C2` `accepts_flexible_hours=True`：候选人需要接受灵活工时安排。
- `C3` `available_monday=True`：候选人需要周一可以参与工作。
- `C4` `requires_extra_equipment=False`：候选人不能需要额外专用设备支持。
- `C5` `can_work_remote=True`：候选人需要能够远程工作。

- `A` violation: `['C1', 'C5']`
- `B` violation: `[]`
- `C` violation: `['C3', 'C4']`
- `D` violation: `['C2', 'C4']`

## 97. attr_en_000097_zh_view

- source: `attr_en_000097_original`
- scenario: `project_assignment`
- option_closeness: `medium`
- structural_complexity: `low`
- gold: `A`

项目团队需要为一项专门任务分配一名成员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要完成过相关培训。
2. 候选人需要能够在不需要额外监督的情况下工作。
3. 候选人需要具备数据分析经验。

候选人：
A. Drew 不需要额外监督也能完成工作。另外，Drew 做过数据分析工作，Drew 完成过相关培训。
B. Wren 完成过相关培训。另外，Wren 没有实际数据分析经历，Wren 不需要额外监督也能完成工作。
C. Rowan 需要额外监督才能完成工作。另外，Rowan 没有实际数据分析经历，Rowan 完成过相关培训。
D. Blair 做过数据分析工作。另外，Blair 没有完成相关培训，Blair 不需要额外监督也能完成工作。

哪位候选人适合承担这项任务？

约束与 violation signature：

- `C1` `has_prior_training=True`：候选人需要完成过相关培训。
- `C2` `needs_supervision=False`：候选人需要能够在不需要额外监督的情况下工作。
- `C3` `has_data_analysis_experience=True`：候选人需要具备数据分析经验。

- `A` violation: `[]`
- `B` violation: `['C3']`
- `C` violation: `['C2', 'C3']`
- `D` violation: `['C1']`

## 98. attr_en_000098_zh_view

- source: `attr_en_000098_original`
- scenario: `availability_selection`
- option_closeness: `hard`
- structural_complexity: `low`
- gold: `B`

协调人需要从四名候选人中找出唯一符合日程和参与要求的人。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要能够现场参与工作。
2. 候选人需要能够远程工作。
3. 候选人需要周末可以参与工作。

候选人：
A. Arden 能够远程工作。另外，Arden 不能现场参与工作，Arden 周末可以参与工作。
B. Jordan 能够现场参与工作。另外，Jordan 周末可以参与工作，Jordan 能够远程工作。
C. Lane 能够现场参与工作。另外，Lane 周末可以参与工作，Lane 不能远程工作。
D. Casey 周末无法参与工作。另外，Casey 能够远程工作，Casey 能够现场参与工作。

哪位候选人符合全部要求？

约束与 violation signature：

- `C1` `can_work_onsite=True`：候选人需要能够现场参与工作。
- `C2` `can_work_remote=True`：候选人需要能够远程工作。
- `C3` `available_weekend=True`：候选人需要周末可以参与工作。

- `A` violation: `['C1']`
- `B` violation: `[]`
- `C` violation: `['C2']`
- `D` violation: `['C3']`

## 99. attr_en_000099_zh_view

- source: `attr_en_000099_original`
- scenario: `availability_selection`
- option_closeness: `hard`
- structural_complexity: `low`
- gold: `B`

协调人需要从四名候选人中找出唯一符合日程和参与要求的人。
被选中的人必须满足以下全部要求：

要求：
1. 候选人需要下午可以参与工作。
2. 候选人不能需要额外专用设备支持。
3. 候选人不能存在日程冲突。

候选人：
A. Robin 不存在日程冲突。另外，Robin 需要额外专用设备支持，Robin 下午可以参与工作。
B. Noel 不需要额外专用设备支持。另外，Noel 不存在日程冲突，Noel 下午可以参与工作。
C. Jamie 存在与项目安排冲突的日程。另外，Jamie 下午可以参与工作，Jamie 不需要额外专用设备支持。
D. Cameron 不需要额外专用设备支持。另外，Cameron 不存在日程冲突，Cameron 下午无法参与工作。

哪位候选人符合全部要求？

约束与 violation signature：

- `C1` `available_afternoon=True`：候选人需要下午可以参与工作。
- `C2` `requires_extra_equipment=False`：候选人不能需要额外专用设备支持。
- `C3` `has_schedule_conflict=False`：候选人不能存在日程冲突。

- `A` violation: `['C2']`
- `B` violation: `[]`
- `C` violation: `['C3']`
- `D` violation: `['C1']`

## 100. attr_en_000100_zh_view

- source: `attr_en_000100_original`
- scenario: `expert_recruitment`
- option_closeness: `medium`
- structural_complexity: `low`
- gold: `A`

某研究实验室正在为一个新项目选择一名研究人员。
被选中的人必须满足以下全部要求：

要求：
1. 候选人不能存在与项目相关的利益冲突。
2. 候选人需要具备编程经验。
3. 候选人需要有公开表达或演讲经验。

候选人：
A. Lane 有公开表达或演讲经验。另外，Lane 不存在项目相关的利益冲突，Lane 有实际编程经验。
B. Cameron 与项目存在利益冲突。另外，Cameron 有公开表达或演讲经验，Cameron 没有处理过编程任务。
C. Emerson 没有处理过编程任务。另外，Emerson 有公开表达或演讲经验，Emerson 不存在项目相关的利益冲突。
D. Harper 不存在项目相关的利益冲突。另外，Harper 没有公开表达或演讲经验，Harper 有实际编程经验。

哪位候选人满足所有要求？

约束与 violation signature：

- `C1` `has_conflict=False`：候选人不能存在与项目相关的利益冲突。
- `C2` `has_programming_experience=True`：候选人需要具备编程经验。
- `C3` `has_public_speaking_experience=True`：候选人需要有公开表达或演讲经验。

- `A` violation: `[]`
- `B` violation: `['C1', 'C2']`
- `C` violation: `['C2']`
- `D` violation: `['C3']`
