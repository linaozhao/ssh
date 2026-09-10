# Qwen v4.1 稳定错误语义复核

本文件是智能体依据题面、结构化字段和已保存输出完成的语义复核，不是人工标注，也不把输出文本诊断解释为模型内部认知机制。

- 复核题目：11（稳定全错 10，正误共存 1）
- 发现题面或标注缺陷：0
- 错误响应：31
- 输出文本诊断：`{'explicit_requirement_relaxation': 3, 'selected_fact_misread_or_not_applied': 27, 'unsupported_constraint_substitution': 1}`

## attr_v4_1_000045_original

- 状态：`mixed`；组合：`CL1__DS3_near__IL1_low`；Gold：`A`
- 复核结论：The item and annotation are internally consistent; observed wrong answers select formally violating candidates.
- 远程与现场同时要求（不冲突但较特殊）：True
- run 1：回答 C（Reese），违反 `['C3']`；C3 The candidate must be available for on-site work. / 题面事实: Reese is not available for on-site work。
  输出文本证据：The requirements are: (1) remote participation is allowed, (2) availability on Tuesday, and (3) availability for on-site work. Candidate C meets all three: remote participation is possible, available on Tuesday, and available for on-site work. Other candidates fail at least one requirement. 诊断：`selected_fact_misread_or_not_applied`。
- run 2：回答 A，正确。解释：Candidate A can participate on site, has the setup for remote collaboration, and is available on Tuesday. This satisfies all requirements: remote participation, Tuesday availability, and on-site availability. Other candidates fail one or more requirements.
- run 3：回答 A，正确。解释：Candidate A meets all requirements: they can participate remotely, are available on Tuesday, and can work on-site. Candidates B, C, and D fail to meet one or more requirements.

## attr_v4_1_000081_original

- 状态：`stable_wrong`；组合：`CL2__DS2_medium__IL1_low`；Gold：`A`
- 复核结论：The item and annotation are internally consistent; observed wrong answers select formally violating candidates.
- 远程与现场同时要求（不冲突但较特殊）：False
- run 1：回答 D（Quinn），违反 `['C2']`；C2 Monday availability is required. / 题面事实: Quinn cannot join project work on Monday。
  输出文本证据：Candidate D satisfies all the requirements: available for on-site work, available on Monday, available on Tuesday, able to participate on the weekend, and available in the morning. 诊断：`selected_fact_misread_or_not_applied`。
- run 2：回答 D（Quinn），违反 `['C2']`；C2 Monday availability is required. / 题面事实: Quinn cannot join project work on Monday。
  输出文本证据：Candidate D satisfies all the requirements: available for on-site work, available on Monday, available on Tuesday, able to participate on the weekend, and has morning availability. 诊断：`selected_fact_misread_or_not_applied`。
- run 3：回答 D（Quinn），违反 `['C2']`；C2 Monday availability is required. / 题面事实: Quinn cannot join project work on Monday。
  输出文本证据：Candidate D satisfies all requirements: available for on-site work, available on Monday, available on Tuesday, able to participate on the weekend, and has morning availability. Other candidates fail one or more requirements. 诊断：`selected_fact_misread_or_not_applied`。

## attr_v4_1_000083_original

- 状态：`stable_wrong`；组合：`CL2__DS2_medium__IL1_low`；Gold：`C`
- 复核结论：The item and annotation are internally consistent; observed wrong answers select formally violating candidates.
- 远程与现场同时要求（不冲突但较特殊）：False
- run 1：回答 D（Sage），违反 `['C4']`；C4 Only candidates with prior public presentation experience are eligible. / 题面事实: Sage has no background in formal presentation duties。
  输出文本证据：Candidate D meets all the requirements: valid local work authorization, valid security clearance, availability on Monday, practical experience analyzing datasets, and prior public presentation experience (implied by 'formal presentation duties'). 诊断：`unsupported_constraint_substitution`。
- run 2：回答 D（Sage），违反 `['C4']`；C4 Only candidates with prior public presentation experience are eligible. / 题面事实: Sage has no background in formal presentation duties。
  输出文本证据：Candidate D meets all the requirements: valid local work authorization, valid security clearance, available on Monday, has practical experience analyzing datasets, and has experience speaking to an audience. 诊断：`selected_fact_misread_or_not_applied`。
- run 3：回答 D（Sage），违反 `['C4']`；C4 Only candidates with prior public presentation experience are eligible. / 题面事实: Sage has no background in formal presentation duties。
  输出文本证据：Candidate D meets all the requirements: has valid local work authorization, has security clearance, is available on Monday, has practical experience analyzing datasets, and has experience speaking to an audience. 诊断：`selected_fact_misread_or_not_applied`。

## attr_v4_1_000112_original

- 状态：`stable_wrong`；组合：`CL2__DS3_near__IL2_high`；Gold：`D`
- 复核结论：The item and annotation are internally consistent; observed wrong answers select formally violating candidates.
- 远程与现场同时要求（不冲突但较特殊）：False
- run 1：回答 C（Logan），违反 `['C5']`；C5 Availability next month is required. / 题面事实: Logan cannot join the project next month。
  输出文本证据：Candidate C satisfies all the requirements: they can work independently, have hands-on machine learning experience, have a local work permit, do not have a scheduling conflict, and are available next month. Other candidates fail at least one requirement. 诊断：`selected_fact_misread_or_not_applied`。
- run 2：回答 C（Logan），违反 `['C5']`；C5 Availability next month is required. / 题面事实: Logan cannot join the project next month。
  输出文本证据：Candidate C satisfies all the requirements: works independently, has hands-on machine learning experience, has a local work permit, no scheduling conflict, and is available next month. Other candidates fail at least one requirement. 诊断：`selected_fact_misread_or_not_applied`。
- run 3：回答 C（Logan），违反 `['C5']`；C5 Availability next month is required. / 题面事实: Logan cannot join the project next month。
  输出文本证据：Candidate C meets all the requirements: they can work independently, have hands-on machine learning experience, have a local work permit, have no scheduling conflict, and are available next month. The other candidates fail at least one requirement. 诊断：`selected_fact_misread_or_not_applied`。

## attr_v4_1_000149_original

- 状态：`stable_wrong`；组合：`CL3__DS2_medium__IL1_low`；Gold：`A`
- 复核结论：The item and annotation are internally consistent; observed wrong answers select formally violating candidates.
- 远程与现场同时要求（不冲突但较特殊）：False
- run 1：回答 B（Ellis），违反 `['C7']`；C7 Afternoon availability is required. / 题面事实: Ellis cannot work in the afternoon time slot。
  输出文本证据：Candidate B satisfies all requirements: remote work capability, willingness to travel, quality assurance experience, no scheduling conflict, morning availability, software implementation experience, and afternoon availability. 诊断：`selected_fact_misread_or_not_applied`。
- run 2：回答 B（Ellis），违反 `['C7']`；C7 Afternoon availability is required. / 题面事实: Ellis cannot work in the afternoon time slot。
  输出文本证据：Candidate B satisfies all the requirements: remote work capability, willingness to travel, quality assurance experience, no scheduling conflict, morning and afternoon availability, and software implementation experience. 诊断：`selected_fact_misread_or_not_applied`。
- run 3：回答 B（Ellis），违反 `['C7']`；C7 Afternoon availability is required. / 题面事实: Ellis cannot work in the afternoon time slot。
  输出文本证据：Candidate B satisfies all requirements: remote work capability, willingness to travel, quality assurance experience, no scheduling conflict, morning availability, software implementation experience, and afternoon availability. 诊断：`selected_fact_misread_or_not_applied`。

## attr_v4_1_000153_original

- 状态：`stable_wrong`；组合：`CL3__DS2_medium__IL2_high`；Gold：`A`
- 复核结论：The item and annotation are internally consistent; observed wrong answers select formally violating candidates.
- 远程与现场同时要求（不冲突但较特殊）：True
- run 1：回答 D（Jamie），违反 `['C1']`；C1 Weekend availability is required. / 题面事实: Jamie cannot join weekend project activities。
  输出文本证据：Candidate D satisfies all the requirements: availability on Monday and Tuesday, weekend availability is not required, but the requirement for afternoon availability is met, on-site participation is possible, there is no scheduling conflict, and remote work capability is confirmed. Other candidates fail at least one requirement. 诊断：`explicit_requirement_relaxation`。
- run 2：回答 D（Jamie），违反 `['C1']`；C1 Weekend availability is required. / 题面事实: Jamie cannot join weekend project activities。
  输出文本证据：Candidate D satisfies all the requirements: weekend availability is not required, but the requirement for Monday and Tuesday availability is met. The candidate is available in the afternoon, can participate on site, has no scheduling conflict, and can work remotely. Other candidates fail to meet one or more requirements. 诊断：`explicit_requirement_relaxation`。
- run 3：回答 D（Jamie），违反 `['C1']`；C1 Weekend availability is required. / 题面事实: Jamie cannot join weekend project activities。
  输出文本证据：Candidate D satisfies all requirements: availability on Monday and Tuesday, weekend availability is not required, but the requirement for afternoon availability is met, on-site participation is possible, there is no scheduling conflict, and remote work capability is confirmed. Other candidates fail one or more requirements. 诊断：`explicit_requirement_relaxation`。

## attr_v4_1_000157_original

- 状态：`stable_wrong`；组合：`CL3__DS2_medium__IL2_high`；Gold：`A`
- 复核结论：The item and annotation are internally consistent; observed wrong answers select formally violating candidates.
- 远程与现场同时要求（不冲突但较特殊）：False
- run 1：回答 C（Casey），违反 `['C7']`；C7 The role requires experience coordinating people or projects. / 题面事实: Casey has no record of management responsibilities。
  输出文本证据：Candidate C satisfies all the requirements: they can participate during the afternoon and morning, have a local work permit, can join next month, are available in the morning, have no project-related conflicts, have teamwork experience, and have experience coordinating people or projects (via experience working with project teams). 诊断：`selected_fact_misread_or_not_applied`。
- run 2：回答 C（Casey），违反 `['C7']`；C7 The role requires experience coordinating people or projects. / 题面事实: Casey has no record of management responsibilities。
  输出文本证据：Candidate C satisfies all the requirements. They can participate during the afternoon (requirement 1), have a local work permit (requirement 2), can join next month (requirement 3), are available in the morning (requirement 4), have no project-related conflicts (requirement 5), have teamwork experience (requirement 6), and have experience coordinating people or projects (requirement 7). 诊断：`selected_fact_misread_or_not_applied`。
- run 3：回答 C（Casey），违反 `['C7']`；C7 The role requires experience coordinating people or projects. / 题面事实: Casey has no record of management responsibilities。
  输出文本证据：Candidate C satisfies all requirements: can participate during the afternoon and morning, has a local work permit, can join next month, is available in the morning, has no project-related conflict, has teamwork experience, and has experience coordinating people or projects (via working with project teams and preparing stakeholder briefings). 诊断：`selected_fact_misread_or_not_applied`。

## attr_v4_1_000162_original

- 状态：`stable_wrong`；组合：`CL3__DS3_near__IL1_low`；Gold：`B`
- 复核结论：The item and annotation are internally consistent; observed wrong answers select formally violating candidates.
- 远程与现场同时要求（不冲突但较特殊）：True
- run 1：回答 C（Kendall），违反 `['C6']`；C6 The selected candidate must be available next month. / 题面事实: Kendall cannot start participating next month。
  输出文本证据：Candidate C satisfies all the requirements: available on Tuesday, can work remotely, can participate on the weekend, available in the morning, can participate without additional equipment, available next month, and can work on-site. 诊断：`selected_fact_misread_or_not_applied`。
- run 2：回答 C（Kendall），违反 `['C6']`；C6 The selected candidate must be available next month. / 题面事实: Kendall cannot start participating next month。
  输出文本证据：Candidate C satisfies all the requirements: available on Tuesday, can work remotely, can participate on the weekend, available in the morning, can participate without additional equipment, available next month, and can work on-site. 诊断：`selected_fact_misread_or_not_applied`。
- run 3：回答 C（Kendall），违反 `['C6']`；C6 The selected candidate must be available next month. / 题面事实: Kendall cannot start participating next month。
  输出文本证据：Candidate C satisfies all requirements: available on Tuesday, can work remotely, can participate on the weekend, available in the morning, can participate without additional equipment, available next month, and can work on-site. 诊断：`selected_fact_misread_or_not_applied`。

## attr_v4_1_000169_original

- 状态：`stable_wrong`；组合：`CL3__DS3_near__IL1_low`；Gold：`A`
- 复核结论：The item and annotation are internally consistent; observed wrong answers select formally violating candidates.
- 远程与现场同时要求（不冲突但较特殊）：False
- run 1：回答 B（Finley），违反 `['C6']`；C6 Candidates must have experience with quality control work. / 题面事实: Finley has no background in quality review work。
  输出文本证据：Candidate B satisfies all the requirements: has a statistics background, client communication experience, project execution experience, research work participation, presentation experience, quality control experience, and can work in English. Other candidates fail to meet one or more of these criteria. 诊断：`selected_fact_misread_or_not_applied`。
- run 2：回答 B（Finley），违反 `['C6']`；C6 Candidates must have experience with quality control work. / 题面事实: Finley has no background in quality review work。
  输出文本证据：Candidate B satisfies all the requirements: has a statistics background, client communication experience, project execution experience, research work participation, presentation experience, quality control experience, and can work in English. 诊断：`selected_fact_misread_or_not_applied`。
- run 3：回答 B（Finley），违反 `['C6']`；C6 Candidates must have experience with quality control work. / 题面事实: Finley has no background in quality review work。
  输出文本证据：Candidate B satisfies all requirements: has a statistics background, client communication experience, project execution experience, research work participation, presentation experience, quality control experience, and can work in English. 诊断：`selected_fact_misread_or_not_applied`。

## attr_v4_1_000173_original

- 状态：`stable_wrong`；组合：`CL3__DS3_near__IL2_high`；Gold：`A`
- 复核结论：The item and annotation are internally consistent; observed wrong answers select formally violating candidates.
- 远程与现场同时要求（不冲突但较特殊）：False
- run 1：回答 D（Avery），违反 `['C2']`；C2 Applicants must have experience working with machine learning systems. / 题面事实: Avery has no prior exposure to machine learning projects。
  输出文本证据：Candidate D satisfies all the requirements: practical programming experience, experience with machine learning systems, relevant domain knowledge, statistics background, required professional certification, on-site participation, and participation on Tuesday. Other candidates fail to meet one or more of these criteria. 诊断：`selected_fact_misread_or_not_applied`。
- run 2：回答 D（Avery），违反 `['C2']`；C2 Applicants must have experience working with machine learning systems. / 题面事实: Avery has no prior exposure to machine learning projects。
  输出文本证据：Candidate D satisfies all the requirements: practical programming experience, experience with machine learning systems, relevant domain knowledge, statistics background, required professional certification, on-site participation, and availability on Tuesday. Other candidates fail to meet one or more of these requirements. 诊断：`selected_fact_misread_or_not_applied`。
- run 3：回答 D（Avery），违反 `['C2']`；C2 Applicants must have experience working with machine learning systems. / 题面事实: Avery has no prior exposure to machine learning projects。
  输出文本证据：Candidate D satisfies all requirements: has programming experience, experience with machine learning systems, relevant domain knowledge, statistics background, holds the required certification, can participate on site, and can participate on Tuesday. Other candidates fail to meet one or more requirements. 诊断：`selected_fact_misread_or_not_applied`。

## attr_v4_1_000177_original

- 状态：`stable_wrong`；组合：`CL3__DS3_near__IL2_high`；Gold：`A`
- 复核结论：The item and annotation are internally consistent; observed wrong answers select formally violating candidates.
- 远程与现场同时要求（不冲突但较特殊）：False
- run 1：回答 C（Ellis），违反 `['C6']`；C6 Availability next month is required. / 题面事实: Ellis cannot join the project next month。
  输出文本证据：Candidate C satisfies all the requirements: they can participate during the morning, work flexible hours, have no scheduling conflict, are available on Monday, can work during the weekend, are available next month, and can work on-site. All stated requirements are met by Candidate C. 诊断：`selected_fact_misread_or_not_applied`。
- run 2：回答 C（Ellis），违反 `['C6']`；C6 Availability next month is required. / 题面事实: Ellis cannot join the project next month。
  输出文本证据：Candidate C satisfies all the requirements: (1) can participate during the morning, (2) can work flexible hours, (3) has no scheduling conflict, (4) is available on Monday, (5) can work during the weekend, (6) is available next month, and (7) can work on-site. 诊断：`selected_fact_misread_or_not_applied`。
- run 3：回答 C（Ellis），违反 `['C6']`；C6 Availability next month is required. / 题面事实: Ellis cannot join the project next month。
  输出文本证据：Candidate C satisfies all requirements: can participate during the morning, works flexible hours, has no scheduling conflict, is available on Monday, can work during the weekend, is available next month, and can work on-site. All stated requirements are met by Candidate C. 诊断：`selected_fact_misread_or_not_applied`。

