# MAD Drift Pilot v1 案例复核

以下为程序选择的可审查案例，不声称是人工标注或内部机制证明。

## 有害修改

- item: `attr_v4_1_000250`; condition: `C_clean`; stage: `5`; team: 1; agent: `agent_2`
- 要求：Candidates must have valid local work authorization. / The selected candidate must have prior coding experience. / Only candidates with the required prior training are eligible.
- 当轮 oracle：`['B']`
- 修改前：`('B',)`，解释：No new evidence has been added, only a restatement of Payton's local work permit status. All other candidates have been eliminated due to lacking required attributes. Milan meets all requirements.
- 同伴消息：`[{"agent_id": "agent_1", "prediction": ["B", "C"], "reasoning": "Payton now meets the local work permit requirement and has prior training, so they are not eliminated. Milan meets all requirements. A and D have been eliminated for lacking required attributes. C lacks programming experience, which does not violate the requirements.", "correct": false}, {"agent_id": "agent_3", "prediction": ["B", "C"], "reasoning": "Candidates A and D have been eliminated. A lacks required training and local work authorization. D does not meet the local work permit requirement. B has programming experience, a local work permit, and completed prerequisite training. C meets the local work permit requirement and has prior training, though lacks programming experience, which is not explicitly violated.", "correct": false}]`
- 修改后：`('B', 'C')`，解释：Payton now meets the local work permit requirement and has prior training, so they are not eliminated. Milan meets all requirements. Candidates A and D have been eliminated for lacking required attributes. C has prior training and local work permit but lacks programming experience, which does not violate the requirements.
- 程序判定：`correct_to_wrong`；采用同伴上一轮答案信号：`True`。
- 边界：该事件能确定答案与标准状态的变化，不能单凭输出解释确定模型内部原因。

## 有效纠错

- item: `attr_v4_1_000187`; condition: `C_clean`; stage: `1`; team: 1; agent: `agent_3`
- 要求：Only candidates who can join next month are eligible. / Candidates must have experience presenting to an audience. / Client communication experience is required.
- 当轮 oracle：`['C', 'D']`
- 修改前：`('B', 'C', 'D')`，解释：Quinn has not given public presentations before, violating requirement 2. Devon has no practical background in client communication, violating requirement 3. Jordan is available next month and Jamie has client-facing discussions experience, so they meet requirements.
- 同伴消息：`[{"agent_id": "agent_1", "prediction": ["C", "D"], "reasoning": "Quinn is eliminated due to lack of public speaking experience. Devon is eliminated due to lack of client communication experience. Jordan is eligible as available next month and no requirements violated. Jamie is eligible as has client communication experience.", "correct": true}, {"agent_id": "agent_2", "prediction": ["C", "D"], "reasoning": "Quinn is eliminated due to lack of public speaking experience. Devon is eliminated due to lack of client communication experience. Jordan is eligible as available next month and no disqualifying attributes are known. Jamie is eligible due to client communication experience.", "correct": true}]`
- 修改后：`('C', 'D')`，解释：Quinn is eliminated due to lack of public speaking experience. Devon is eliminated due to lack of client communication experience. Jordan is available next month but lacks evidence of public speaking experience and client communication, so he does not meet all requirements. Jamie has client communication experience and is available next month, so he meets all requirements.
- 程序判定：`wrong_to_correct`；采用同伴上一轮答案信号：`True`。
- 边界：该事件能确定答案与标准状态的变化，不能单凭输出解释确定模型内部原因。

## 正确保持

- item: `attr_v4_1_000187`; condition: `C_clean`; stage: `1`; team: 1; agent: `agent_1`
- 要求：Only candidates who can join next month are eligible. / Candidates must have experience presenting to an audience. / Client communication experience is required.
- 当轮 oracle：`['C', 'D']`
- 修改前：`('C', 'D')`，解释：Quinn is eliminated due to lack of public speaking experience. Devon is eliminated due to lack of client communication experience. Jordan is eligible as available next month and no requirements violated. Jamie is eligible as has client communication experience.
- 同伴消息：`[{"agent_id": "agent_2", "prediction": ["C", "D"], "reasoning": "Quinn is eliminated due to lack of public speaking experience. Devon is eliminated due to lack of client communication experience. Jordan is eligible as available next month and no disqualifying attributes are known. Jamie is eligible due to client communication experience.", "correct": true}, {"agent_id": "agent_3", "prediction": ["C", "D"], "reasoning": "Quinn is eliminated due to lack of public speaking experience. Devon is eliminated due to lack of client communication experience. Jordan is available next month but lacks evidence of public speaking experience and client communication, so he does not meet all requirements. Jamie has client communication experience and is available next month, so he meets all requirements.", "correct": true}]`
- 修改后：`('C', 'D')`，解释：Quinn is eliminated due to lack of public speaking experience. Devon is eliminated due to lack of client communication experience. Jordan is eligible as available next month, but no evidence of public speaking experience or client communication is provided, so he does not meet all requirements. Jamie is eligible as has client communication experience and is available next month.
- 程序判定：`correct_to_correct`；采用同伴上一轮答案信号：`False`。
- 边界：该事件能确定答案与标准状态的变化，不能单凭输出解释确定模型内部原因。

## 错误持续

- item: `attr_v4_1_000187`; condition: `C_clean`; stage: `3`; team: 1; agent: `agent_1`
- 要求：Only candidates who can join next month are eligible. / Candidates must have experience presenting to an audience. / Client communication experience is required.
- 当轮 oracle：`['C']`
- 修改前：`('B', 'C')`，解释：Quinn is eligible as available next month and has client communication experience. Jordan is eligible as has public speaking experience and client communication. Devon is eliminated due to unavailability. Jamie is eliminated due to lack of public speaking experience.
- 同伴消息：`[{"agent_id": "agent_2", "prediction": ["B", "C"], "reasoning": "Quinn is eligible as available next month and has client communication experience. Jordan is eligible as available next month and has public speaking experience and client communication. Devon is eliminated due to unavailability and lack of public speaking experience. Jamie is eliminated due to lack of public speaking experience and unavailability.", "correct": false}, {"agent_id": "agent_3", "prediction": ["B", "C"], "reasoning": "Quinn is available next month and has client communication experience, meeting all requirements. Jordan has public speaking experience and is available next month, meeting all requirements. Devon cannot start next month and lacks public speaking experience, violating requirements 1 and 2. Jamie lacks public speaking experience and cannot start next month, violating requirements 1 and 2.", "correct": false}]`
- 修改后：`('B', 'C')`，解释：Quinn is eligible as available next month and has client communication experience. Jordan is eligible as has public speaking experience and client communication. Devon is eliminated due to unavailability and lack of public speaking experience. Jamie is eliminated due to lack of public speaking experience and unavailability.
- 程序判定：`wrong_to_wrong`；采用同伴上一轮答案信号：`False`。
- 边界：该事件能确定答案与标准状态的变化，不能单凭输出解释确定模型内部原因。

## CBM 更正后的更新

- item: `attr_v4_1_000525`; team: 1; agent: `agent_1`
- 更正前 oracle/输出：`['A']` / `['A', 'B', 'C', 'D']`
- 正式更正：Evidence update, round 4:
- CORRECTION: withdraw attr_v4_1_000525:D:available_monday:v1 and replace it with: Indigo can participate on Monday.

Based on all currently active evidence, which candidates have not yet been eliminated?
- 更正后讨论前 oracle/输出：`['A', 'D']` / `['A', 'B', 'C', 'D']`
- MAD R2 输出：`['A', 'B', 'C', 'D']`；解释：All candidates meet the requirements based on the active evidence. Indigo has Monday availability, security clearance, certificate, and no conflicts. Casey has security clearance, certificate, no conflicts, and client communication experience. Morgan has security clearance, certificate, and no conflicts. Skyler has management experience, client communication experience, security clearance, and Monday availability.
- 边界：更正导致标准状态变化，不把这一步本身记为同伴讨论漂移；只对更正后的阶段内修订单独判断。

## MAD 与阶段内自我修正不同

- item: `attr_v4_1_000525`; condition: `C_clean`; stage: `2`; team: 1; agent: `agent_1`
- oracle：`['A', 'C']`
- MAD R2：`['A', 'B', 'C']`；解释：Indigo has been eliminated due to lack of Monday availability. Skyler, Casey, and Morgan meet all requirements based on the active evidence.
- 同起点自我修正 R2：`['A', 'B', 'C', 'D']`；解释：No candidate has been eliminated based on the active evidence. Indigo's Monday availability was reported as unavailable, but that was in the previous round and has not been corrected or confirmed. All other requirements are either met or not yet reported, and missing attributes are considered unknown.
- 结论边界：两路线共享当阶段讨论前状态，但 token 数与输入内容不同；差异是配对观察，不证明具体内部机制。
