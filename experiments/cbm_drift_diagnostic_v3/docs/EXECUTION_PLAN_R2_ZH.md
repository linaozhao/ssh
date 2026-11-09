# MAD 漂移诊断 v3：服务器 Codex 完整执行计划（修订 R2）

计划版本：controlled-first-r2。日期：2026-11-09。
本文件替代此前任务书中的执行范围、样例预算、GPU 选择和 Judge 启用规则。
这是待实施的需求与验收计划，不代表代码已经修改、分支已经创建、样例已获人工确认或实验已经执行。

## 0. 交给服务器 Codex 的总指令

请实施本计划，不要只返回建议。先检查实际仓库、AGENTS.md、现有分支/目录、工作区修改和服务器环境，再按阶段执行。无需等待 Judge 新密钥或真实轨迹人工标注，便可继续其余独立工作。

核心研究问题：在暂定的漂移类型和受控条件下，诊断流程能否正确检测、分类、定位，并避免误报？

本轮优先验证程序实现与受控诊断；同时完整生成新协议 MAD。自然 MAD 的独立人工标注与正式真实轨迹诊断评测后续开展。受控测试成功不能推广为真实 MAD 已验证有效，也不能证明分类覆盖所有漂移。

### 三部分范围

| 部分 | 本轮工作 | 完成标准 |
| --- | --- | --- |
| A：本轮必须完成，不依赖 Judge 密钥 | 分支与代码改造；数据派生；程序和离线测试；72 个受控样例及参考核验；物理 GPU 4 上完整重跑 MAD；新轨迹程序诊断；144 请求队列；后续盲标材料与报告 | 代码/数据/依赖/可见性审计通过；运行统计真实完整；所有未执行项明确标注 |
| B：依赖服务器本地新凭证及显式启用 | 同一 Judge 模型的 direct 与 structured 对72个受控样例各执行一次逻辑调用；计算受控检测、分类、定位、误报及成本 | 144 个逻辑请求具有终态，成功/失败/覆盖单列；参考可评估范围明确，dev 与 holdout 分开 |
| C：后续人工评测 | 真实 MAD 双人独立盲标、仲裁；后续132消息双模式配对评测；真实误报/漏报/定位评价 | 独立参考产生后另行启用，不计入本轮在线任务 |

A 完成不等于 B 已完成；B 完成也不等于 C 已验证。若 GPU 4 无法使用，只阻塞依赖该卡的 MAD 工作，继续所有可独立完成的 A 类任务并报告阻塞。

### 固定预算与边界

- 12 个现有基础题；MAD pilot 运行一次，独立重复留待后续。
- 四条件标准名称：clean、update、noise、update_noise。
- MAD 新协议：1188 个唯一计划请求，全部重新生成；静态预检与重试另计。
- 受控集初始预算：72 个唯一目标样例，开发36、留出36。
- 本轮受控 Judge：72×2=144 个逻辑请求；开发调试、重试、额外抽取调用另计。
- 真实132消息的双模式264次调用暂缓。旧计划的408次不是本轮执行目标。
- 在线 Judge 默认关闭；密钥只在服务器本地配置，新凭证与显式启用同时具备才启动。
- GPU 固定为服务器 nvidia-smi 所示物理编号4的 RTX 4090；禁止自行换卡或抢占进程。

## 1. 代码分支、目录与基线检查

仓库：linaozhao/ssh。
此前审阅基线：feature/cbm-drift-diagnostic-v2，提交5d4a12f34dd2318d36ae20224668e866111fd0d9。
这只是已知基线，不假定它仍是服务器最新状态；执行时 fetch 并检查实际差异，记录实际采用的 SHA。不要静默使用较旧的 main。

目标分支：
feature/cbm-drift-shared-prefix-v3

目标实验目录：
experiments/cbm_drift_diagnostic_v3/

新包：
src/cbm_drift_v3/

执行要求：

1. 检查 git status、分支、worktree、目录及已有进程，保留用户未提交修改。
2. 分支/目录不存在时创建；存在时先判断是否为本任务的已有实现。不得强制覆盖、reset --hard 或清除结果。
3. 同一任务的已有代码可检查后继续开发，但本次新运行使用独立 run_id 和结果子目录；只有本 run 内、指纹相同的成功响应可断点恢复。
4. 若名称已被不相关工作占用，使用不冲突的后缀分支/worktree，并在报告中说明实际名称，不覆盖原分支。
5. 复制或提取必要代码、配置、规范和测试；不要复制旧 results/records 冒充新实验。
6. 冻结旧代码版本、旧数据、旧 MAD 与旧 Judge 输出。新实验只读引用源题目/证据设计。
7. 新配置记录 plan_revision、code_sha、source_sha、schema_version、prompt_version、run_id。配置指纹不包含真实凭证。
8. 提交新代码、测试、配置、文档与小型摘要；大体积原始响应按仓库规则保存并记录清单/哈希。不强推、不自动合并 main。

新运行建议标识：cbm_drift_v3_shared_history_pilot_r2_<本地唯一标识>。
此前任何协议的输出，包括已存在但不属于此次 run 的结果，均不作为新 MAD 的组成部分。

## 2. 修改文件与执行次序

下面的模块名指新 v3 目录中的对应模块，实际函数名可以适配，功能边界必须满足。

| 模块/新增文件 | 修改内容 |
| --- | --- |
| common.py、prepare.py、state.py、validation.py | 导入冻结题目和选题记录；四条件派生；证据重放；共享请求图；数量/状态校验 |
| runner.py | 显式历史依赖；阶段/轮次屏障；T3检查点；四分支隔离；断点恢复；单GPU限制 |
| diagnostics.py | 当前状态、候选错误、前后状态变化；对象级而非仅整题级的时间诊断 |
| prompts.py、docs/judge_rubric.md | 统一类别定义、反例、时间依据、stance 和输出要求 |
| judge.py、tokenplan_judge.py、tokenplan_analysis.py | claim级输出/校验；两协议；动态队列；新凭证门禁；有限重试；分任务成本 |
| controlled_cases.py、scripts/build_controlled_cases.py | 72样例、分层/拆分、局部干预、参考核验、输入与标签隔离 |
| evaluation.py | 检测、对象定位、时间定位、多标签分类、负例误报、覆盖与弃权；修复匹配分母 |
| annotation.py、scripts/flatten_annotation.py | 真实轨迹待标注材料；明确标注范围；nested到flat转换及验证 |
| scripts/launch_qwen_service.sh、scripts/run_pipeline.py | 固定物理GPU4；分阶段入口；默认离线；状态与恢复 |
| tests/、docs/metrics.md、RUNBOOK_ZH.md | 回归、指标定义、运行记录与复现 |

建议顺序：

A1. 仓库/数据/环境检查，冻结任务和诊断定义。
A2. 实现程序状态、评估器和受控测试框架，先做离线验证。
A3. 构造并核验72个受控样例，冻结dev/holdout与参考。
A4. 实现共享前史执行器，完成mock、图、历史和恢复测试。
A5. 在物理GPU4运行静态预检、MAD预检与完整新MAD。
A6. 新轨迹程序分析、受控144请求队列、真实待标注材料、报告。
B. 在新凭证与显式启用后执行受控Judge；不必等待A5全部完成，只要其所需冻结样例已就绪。
C. 后续独立人工真实评测。

本轮受控集优先使用合法的脚本化必要前史，可直接从冻结规则/证据构造，不依赖自然MAD先产生错误。明确 history_source=scripted；不能把脚本化历史写成自然模型输出。这样A2/A3不被GPU或API阻塞。

## 3. 数据：沿用题目，派生组合条件

保留12个base_item、选题记录、原有三种证据设计。禁止重新抽题或修改筛选任务语义。

新条件名与旧设计建立显式映射：

| v3名称 | 原设计 | 正式事实更正 | 无关信息 |
| --- | --- | --- | --- |
| clean | clean_stay | 无 | 无额外噪声 |
| update | evidence_update | 有 | 无额外噪声 |
| noise | irrelevant_noise | 无 | 有 |
| update_noise | 新派生 | 同update | 同noise |

source_variant_type 与 branch_type 分开记录，保留旧设计身份，不对旧文件直接改名。

update 在本轮始终表示正式更正候选人的属性事实，规则固定。不增加“修改筛选规则”的实验条件。

update_noise 的构造：

1. T1–T3使用共同的正式证据前缀。
2. T4/T5以update的正式observation/correction/restatement为基础。
3. 只加入noise同阶段中fact_kind=non_target的无关事件。
4. 不复制noise中的旧正式事实和旧restatement，避免重新引入已失效事实。
5. 保留正式事件顺序，采用固定可重现的噪声顺序；检查ID、引用、阶段与更正关系。
6. 通过证据重放重新计算active_evidence、superseded_evidence_ids、oracle、exclusions和状态哈希，不手写答案。

必须验证：

- 共48条条件证据序列；原36条设计的任务与事件语义保持一致。
- 四条件T1–T3一致。
- clean与noise的目标事实状态、oracle一致。
- update与update_noise的目标事实状态、oracle一致。
- update_noise与noise的同阶段非目标信息一致。
- 所有更正只替换命名的当前有效事实，候选人/属性对应正确；没有未来引用。
- 源文件、选题记录和旧结果哈希不变。

任务语义：回答所有“尚未被排除”的候选人。未知属性不是违反条件；只在有效已知事实违反固定要求时排除。clean只表示对照条件，不表示必然无错误或无漂移。

## 4. 完整重跑MAD：共享的是实际前史

### 4.1 图、检查点与可见性

每个基础题：

- T1、T2、T3各执行R0/R1/R2，每轮三个agent。
- 每轮等待需要的上轮响应完成，遵循原协议的同伴可见性。
- T3-R2三个agent全部完成后，为各agent分别保存实际messages及自己的最后assistant响应。
- 检查点保存三套agent历史、有效证据状态、父消息ID及相关哈希。
- 从同一检查点深拷贝四个分支，分别追加T4事件，然后独立运行T4、T5。
- 分叉不额外增加可见信息：T4-R0不能凭“全局T3完成”看到原协议未提供的其他agent的T3-R2输出。
- 分支之后只看到本分支允许的peer输出，不读兄弟分支、不读未来。

不能只改prepare.py的depends_on而让runner.py继续按variant_id自行猜父请求。执行器必须消费显式的own_previous_message_id、visible_peer_message_ids及依赖图。

### 4.2 身份、随机性与恢复

每条唯一请求至少记录：

```text
run_id, family_id, base_item_id, repeat_id
phase = shared_prefix | branch_suffix
branch_type = null | clean | update | noise | update_noise
request_id, message_id, own_previous_message_id
parent_message_ids, visible_peer_message_ids
evidence_stage, round, agent_id, seed
checkpoint_id, shared_prefix_id
messages_sha256, state_sha256, request_sha256
```

- 共享消息只有一个canonical ID和一条原始记录；分支视图引用它，不复制四次作为独立观测。
- 请求ID/提示词中的引用ID不要暴露“噪声组”等条件说明；oracle与预期标签不进入MAD。
- agent之间使用不同seed；相同family、stage、round、agent的四分支后缀可使用相同派生seed，公式冻结。相同seed不保证不同输入产生相同随机行为。
- 分支调度顺序预先固定并记录。一个服务支撑三个逻辑agent。
- 原子保存响应，区分唯一逻辑请求与实际attempt。
- 仅恢复本run且模型/提示词/数据/父历史指纹一致的成功请求。
- 失败父节点不能变成空历史；下游标记blocked，父节点恢复后再调度。
- 语义错误不能重采样到正确。API基础设施错误有限重试，记录所有尝试。
- API成功但输出格式错误时保留原始发言并标记解析失败；可按原协议作为可见原文继续，不能暗中修正文案。
- 上下文超限不静默截断，明确阻塞/失败与原因。

### 4.3 数量验收

| 项目 | 唯一计划数量 |
| --- | ---: |
| 共享T1–T3 | 12×3×3×3=324 |
| 四分支T4–T5 | 12×4×2×3×3=864 |
| MAD合计 | 1188 |
| 完整分支视图 | 48 |
| 展开后的消息引用 | 48×45=2160 |
| 两题MAD预检 | 2×99=198 |
| 预检通过后的剩余MAD | 990 |

1188不包含静态预检或基础设施重试。198次预检是正式新run的子集，继续执行后不重复调用。全部成功记录可恢复，不从旧协议拿响应补齐。

报告planned、attempted、api_success、parsed、failed、blocked、完整轨迹数；文件存在不等于推理成功。分叉前统计只计算324条唯一消息，不当作四份独立样本。

## 5. 诊断定义：当前错误、内容类别和时间变化分开

### 5.1 检测目标与程序状态

至少分别表达：

- answer_status：当前答案正确/错误/无法识别。
- current_deviation：当前存在可观察的答案决策错误或被明确主张的内容偏离；yes/no/uncertain。
- content_labels：F/R/I及必要的unresolved。
- temporal_status：对象级历史关系；证据不足时uncertain。
- state_transition/update_response：正式状态是否改变、是否适应或回退。

“只有错误答案、解释不足”：可确认当前答案决策错误，但F/R/I应unresolved；是否发生时间漂移取决于前史，不能把unresolved视为无错误，也不能强行补类别。

由程序计算candidate×rule的known_satisfied、known_violated、unknown，以及当前集合的extra/omitted。比较新旧事实、标准集合、模型集合，并把上一答案按新状态重新评分。

程序错误率高低没有自然的F/R/I阈值映射。额外候选可能来自错事实、错规则或错推导。采用“状态计算→主张抽取→可形式化校验与语义判断→保留不确定项”的流程。

### 5.2 工作分类与反例

| 类别 | 可观察判据 | 边界 |
| --- | --- | --- |
| F：事实偏离 | 明确主张与当时有效事实冲突 | unknown被说成已知单列unsupported_assertion；旧事实在更正前的陈述不追溯判错 |
| R：规则偏离 | 明确改变固定筛选要求的方向、内容或组合关系 | 仅答案错误不能推出R |
| I：推导/应用错误 | 明示相关事实和规则正确，但明确结论/应用步骤不被支持 | 同一错误由错误事实或规则解释时，不机械重复加I |
| unresolved | 可见异常但文本不足、语义有歧义或不能唯一确定类别 | 保留不确定性，不能为覆盖率强行分类 |

quote stance至少有asserted、quoted、rejected、hypothetical、uncertain。引用并反驳或仅作条件假设，不自动作为说话者认可的事实。只有假设进一步被当作真实事实使用时，才根据具体文本判偏离。

允许一条消息包含多个claim、多个对象与类别；保留逐条对应关系。必须诊断答案正确但解释错误/过时的消息，禁止以答案正确作为跳过Judge的门控。

### 5.3 时间定义

| 状态 | 最低可见依据 |
| --- | --- |
| initial_error | 确知这是该对象在所定义轨迹中的首次判断，且已错误 |
| newly_introduced | 同一对象此前明确正确，相关正式状态未变，此次变错 |
| persistent | 同一对象的错误先前已出现且持续；必要中间历史可见 |
| corrected | 先前错误、当前修复；区别正式状态变化使旧答案碰巧变对 |
| recurrence | 同一错误被修复后再次出现 |
| post_update_reversion | 正式更正后，该agent已明确正确适应；随后在有效状态未再改变时退回旧依据/旧判断 |
| update_failure | 更新后未正确适应；尚不能证明“适应过又回退” |
| reasonable_update / correct_maintenance | 合理适应正式更正／保持正确 |
| uncertain | 缺少必要前史、不能确定是否首次/持续/回退 |

缺少前史不能仅凭当前是截取片段的第一条就标initial_error，更不能标newly_introduced、persistent或post_update_reversion。可同时确定当前F而将时间状态设为uncertain。

“更新后回退”需要更新前、更新后已适应、之后退回的可核查链条；只在T4第一次回答中沿用旧事实是更新失败，不是已确认的回退。

所有时间判断以具体候选/属性/规则主张为对象；整题答案曾正确不等于每一条理由都曾正确。先前自己的判断与引用同伴判断分开。定位的是公开文本的首次可观察异常，不是内部认知变化或从众因果。

## 6. 受控72例：覆盖、拆分、构造、核验

受控样例是离线诊断材料：保留真实任务规则、有效证据和必要合法历史，编写或局部改写目标发言，预先确定并核验参考标签。
不注入四分支运行MAD，不机械复制四份，也不根据自然MAD必须先出错才能构造。

### 6.1 主覆盖预算

以下为互斥的主抽样层，每例只计入一个主层；真实内容标签与时间状态仍可多维标注。

| 主覆盖层 | 总数 | dev | holdout |
| --- | ---: | ---: | ---: |
| 已知有效事实的直接矛盾 | 6 | 3 | 3 |
| 把未知属性断言为已知事实 | 6 | 3 | 3 |
| 明确改变固定规则 | 6 | 3 | 3 |
| 事实/规则正确但推导或应用错误 | 6 | 3 | 3 |
| 引用错误后明确反驳：当前无偏离 | 6 | 3 | 3 |
| 条件假设且未冒充真实事实：当前无偏离 | 6 | 3 | 3 |
| 正式更正后的合理更新：当前无偏离 | 6 | 3 | 3 |
| 答案正确但依据错误 | 6 | 3 | 3 |
| 答案正确但使用已失效依据 | 6 | 3 | 3 |
| 答案错误、解释不足，类别unresolved | 6 | 3 | 3 |
| 普通正确维持，包括未知属性的正确处理 | 6 | 3 | 3 |
| 多claim/多对象定位，防止标签与对象串配 | 6 | 3 | 3 |
| 合计 | 72 | 36 | 36 |

这替代旧版“每题三类各做一正一负”的机械分配。72是初始预算，不增加隐藏的在线目标例；构造参考文本可共享，但每个Judge目标有唯一case_id。

时间状态另设覆盖表，不重复增加72的总数。dev和holdout各至少覆盖2例：initial_error、newly_introduced、persistent、corrected、post_update_reversion、update_failure、缺少前史而uncertain。普通维持与合理更新由对应主层覆盖，另覆盖一般recurrence。每例指定一个主要时间状态，允许记录辅助状态轴。

若实际规则/证据不能支持某个组合，在同主层调整模板和来源题；不能为凑数修改原始事实或伪造历史。将缺口列为validation failure，在冻结前解决。

### 6.2 拆分与防泄漏

- 在生成Judge结果之前，按base_item_id固定6个family为dev、另6个为holdout，分别36例；尽量按场景/约束负载平衡。
- 同一基础题、同一最小改写配对及其派生变体必须在同一split。
- 每个主覆盖层dev/holdout各3例；尽量避免同层三例全来自一个family。
- 优先建立只改一个关键因素的正负对照，记录pair_id、changed_span、changed_factor；不要求所有案例凑成固定36个配对。
- 多claim定位属于明确的复合压力测试，单独标记，不能伪称只有一个错误因素。
- 开发与留出尽量使用不同措辞和模板变体，记录模板血缘；不能宣称完全消除了模板相似性。
- 调试只用dev。冻结prompt/schema/参考后才能执行holdout；看过holdout结果再调整方法，必须把原holdout视为已使用，新版本另准备未使用留出集。
- 72全体指标只能作描述，主要受控泛化结果用36个holdout；dev分数单列。
- 本轮12题属于开发/pilot；这里的holdout只表示受控诊断拆分，不代表未来真实MAD独立测试集。

### 6.3 样例与参考格式

输入文件cases.jsonl只含诊断所需原始材料。参考expected_labels.jsonl单独存储，禁止被Judge渲染器读取。

参考至少包含：

```text
case_id, pair_id, base_item_id, split, primary_stratum
history_source, source_state_id, target_message_id
expected_current_deviation, expected_content_labels
expected_temporal_status, expected_update_response
agent_id, evidence_stage, round
claims[]:
  quote, start, end, stance
  candidate_ids, attribute, rule_ids
  conflicting_evidence_ids, evidence_version
  prior_support[]: message_id, quote, start, end
  acceptable_equivalent_support
reference_source, verification_status, reviewer_id, review_notes
case_sha256, reference_sha256, schema_version
```

不存在对应属性/事实时用null或空数组并说明原因，不编造ID。unknown断言可用candidate+attribute定位。规则偏离可只涉及rule，不能硬塞候选人。

### 6.4 核验与冻结

1. 从事件日志重放目标时刻状态；标签不根据未来事实判定。
2. 检查必要历史合法可见，脚本化同伴消息满足上一轮可见性。
3. 局部改写后重解析答案、重算extra/omitted、标准状态差异和所有哈希；不能残留原文特征。
4. 若改较早历史，必须重建之后引用与依赖；首版优先只改当前目标发言并截断未来。
5. 校验引文、字符偏移、对象ID、规则与事实版本；多次同文引文不任取首处。
6. 用独立校验逻辑核查冲突、未知、事实更正及推导前提，不仅把生成器标签原样抄回来。
7. 语义核验记录明确区分pending、program_verified、human_verified、ambiguous；没有真实人工参与不能填写人工姓名或human_verified。
8. 人工复核过的参考保留审阅记录；未人工复核但可由形式约束明确验证者，标为程序核验参考。
9. 语义有歧义的样例在冻结前修订/替换，不根据Judge是否答对挑选。仍pending/ambiguous者不能混进正式“参考准确率”分母。
10. 冻结case/reference/rubric/schema/模板与split哈希。修改参考标签意味着新版本，不追溯覆盖旧评分结果。

若72例已经构造，但有参考未核验：报告built=72、verified=<实际数>及缺口；代码/MAD/队列继续完成。在线调用可保存输出，未核验参考的分数保持pending，而不是捏造金标。

程序核验参考的结果可以作为受控工程验证，但必须注明参考来源；语义边界仍可能需要人工复查。这与后续自然MAD双人独立标注是两项不同工作。

## 7. 先完成离线程序验证，再解释Judge表现

本地测试覆盖真实状态重放、输入构造、历史依赖、标签隔离、对象匹配与指标分母。可注入预设的Judge输出测试解析/校验/评估器，但这些mock只证明软件行为，不证明LLM分类有效。

保留两条关键回归：

- 旧标准{A}→新标准{A,B}，答案保持{A}：记录当前漏选B与更新失败，不能直接当稳定事实上的新漂移。
- 相同message/agent，预测定位B/fact_B而参考是C/fact_C：消息级检测可命中，但严格对象定位不命中，不能得到对象定位满分。

还必须测试：

- 正确答案但错误/过时理由不能跳过诊断。
- 错误答案且无解释：当前错误成立，F/R/I为unresolved；时间状态需另判。
- 仅引用后反驳、纯条件假设、合理更新不能因出现错误关键词而误报。
- 无前史时拒绝强行给新出现/持续/回退标签。
- 更新后从未适应与先适应再回退不同。
- 多claim标签、对象与依据导出后不串配。
- 引文offset错误、事实ID不存在、版本失效能够被检测，但引用“被替换的旧事实”作为批评对象是允许的，需区分引用角色。
- 局部改写后所有特征和哈希重算，预期标签不会出现在请求文本。
- holdout不进入开发样例检索或few-shot提示。
- 程序测到的未知/弃权不是“无错误”。

不把单元测试通过写成“72个受控LLM诊断全部通过”。报告至少分开software_tests、reference_validation、online_controlled_evaluation。

## 8. MAD部署：仅物理GPU4

### 8.1 启动前确认

检查物理编号、UUID、PCI bus、型号、显存和正在运行的进程，例如：

```bash
nvidia-smi --query-gpu=index,uuid,name,pci.bus_id,memory.total,memory.used --format=csv
nvidia-smi --query-compute-apps=pid,gpu_uuid,process_name,used_gpu_memory --format=csv
```

核验index=4确实是目标RTX4090。将其UUID记录在runtime_manifest中。容器或调度器只能看到逻辑编号时，必须建立宿主物理GPU4到可见UUID的映射；不能凭“容器cuda:4”猜测。

启动时推荐CUDA_VISIBLE_DEVICES=<已核验物理GPU4的UUID>；这样进程内部可能显示cuda:0，它仍是宿主物理GPU4。启动后用服务PID→GPU UUID再次核验。

物理GPU4不存在、型号不符、被占用而不能运行、显存不足或映射无法确认：报告原因，MAD标记blocked，继续离线工作。不抢占、不终止其他任务、不自行切换其他GPU。只能管理本任务创建并记录PID的服务。

### 8.2 模型与参数

沿用Qwen3-8B，服务器核验实际权重。此前路径：
/data/zla/mad_drift_benchmark/modelscope_models/Qwen/Qwen3-8B

一个模型服务、一个endpoint、tensor_parallel_size=1。启动脚本固定physical_gpu_index=4，并拒绝未经核验的不同GPU映射。

初始服务参数（以本地vLLM --help及显存预检为准）：

```text
served_model_name=Qwen3-8B
dtype=bfloat16
quantization=null
max_model_len=16384
gpu_memory_utilization=0.90
max_num_seqs=3
enable_prefix_caching=true
enforce_eager=true
host=127.0.0.1
```

客户端：

```text
thinking_enabled=false
temperature=0.7
top_p=0.9
max_tokens=1024
max_concurrent_families=1
max_concurrent_requests=3
repeats=1
```

静态snapshot线程数也必须服从全局并发限制。使用实际tokenizer/chat template统计输入长度并预留输出空间。若并发导致不足，可在本卡降低并发/批处理并记录；不能静默缩短历史、量化或换模型。协议/模型变更必须重新冻结配置并预检。

### 8.3 运行顺序

- 先跑离线测试与数据/图审计。
- 静态协议预检沿用原3类snapshot×12题×3seed，共108次，独立记账；不复用旧响应。
- 两题MAD预检198次，纳入新run的1188。
- 校验身份、历史、上下文、格式与服务稳定性后继续剩余990。
- 语义错误是实验观测，不以“必须答对”筛选题目或重采样。
- 保存所有原始新轨迹、检查点、解析与状态；计算程序行为统计。
- 不要求本轮自然轨迹的语义Judge或人工标注完成才算MAD生成完成。

## 9. 本地新密钥与在线受控Judge（B部分）

### 9.1 凭证门禁

- 用户在服务器本地与Codex配置替换后的新密钥，默认环境变量名建议JUDGE_API_KEY_V3_NEW。
- 不从旧TOKENPLAN_API_KEY、DEEPSEEK_API_KEY自动fallback，也不读取聊天历史、旧日志或旧结果中的密钥。
- 以交互式隐藏输入或服务器已有安全凭证注入机制配置；禁止将真实值作为命令行参数、写入任务书/代码/Git/日志。
- 不打印环境变量全集或Authorization头，不记录密钥哈希/前后缀作为普通实验产物。
- 非秘密元数据可记录credential_source=server_local_new、configured_at与credential_check_status，不用它们代替真实授权检查。
- 在线默认false。必须新密钥已配置且用户显式启用，不能仅因检测到某个旧环境变量便自动运行。
- 缺少新密钥时将B标not_run_missing_new_credentials；完成其余独立任务，不反复索要旧密钥。
- 不自动继承旧额度override、无限重试或充值设置。

换密钥不等于换模型。沿用既定Flash Judge作为配置起点，在服务器核对模型ID、服务接口、权限和实际返回模型。若不可用，报告，不静默换成其他模型。

### 9.2 同模型的两种协议

direct输入：
规则、截至当前的正式证据、必要合法历史、目标发言、统一rubric/schema。

structured输入：
相同原始材料，额外加程序计算的标准状态、candidate×rule状态、extra/omitted、有效依据、更正关系及前后变化。

要求：

1. 同一底层模型、模型参数、输出schema和分类/时间定义；仅参考结构辅助不同。
2. 不把预期标签、mutation_type、case层名、dev/holdout标识或人工参考写进请求文本。
3. structured可以看到可计算的状态与答案差异，但主对照不提供已经判好的F/R/I或temporal_status，以免评价变成复制标签。
4. 两者都是诊断器，不承担MAD最终答案聚合。
5. 原始材料相同，辅助信息量不同；结论应表述为“结构化参考辅助的效果”，不是同信息量的纯格式优劣。
6. 首版每样例每协议一次逻辑调用，claim抽取包含在这次输出中；不用隐藏的额外LLM调用。若实际新增抽取调用，单列extractor队列、版本、次数和成本。

输出至少含current_deviation、answer_status、claims[]、content_labels、temporal_status、update_response、uncertainty_reason。claim中保留exact quote、stance、对象、事实/规则、前史引文，程序计算offset。

校验层次分开：JSON/schema、引文/ID、可形式化语义关系、LLM分类预测。schema通过不等于分类正确。

### 9.3 144请求与预检、调试、留出

正式受控队列：36dev×2=72；36holdout×2=72；合计144个唯一逻辑请求。
唯一ID含case版本、协议、prompt/schema版本、模型配置指纹，不把重试算成新样本。

- 默认从dev选6个目标，两协议共12次，作为技术预检子集；覆盖长历史、更新、负例和多claim。
- 若冻结输入/协议不变，预检成功响应计入144，不重复调用。
- 预检验证认证、可达性、schema、引文、截断和资源记录；不要求分类全对。
- 先完成dev部分并检查。需要调整prompt时，另建协议版本；旧调用记入development_debug，不混入最终144。
- prompt/schema/参考冻结后再执行holdout；完成后不得据其结果调参再宣称同一留出集仍独立。
- 开发调试、额外抽取调用不自动开启无限循环；配置独立预算，默认额外预算为0，需要本地显式设定。
- 正式队列每逻辑请求最多1次基础设施重试，最多288次HTTP尝试；仍受更严格的窗口限额约束。
- 分类错误、拒答、JSON错误、语义不符不做选择性重采样。所有状态进入覆盖统计。
- 认证失败停止在线部分；额度错误保存检查点，不无限轮询，不改变其他工作状态。
- 真实132消息队列必须与controlled队列隔离，标deferred；本轮调度器不得自动追加它。
- 不把旧实验1800/408等硬编码留作新计划完成门槛。

预算统计分别报告：formal_unique_requests、formal_attempts、development_debug_calls、extractor_calls、successful_outputs、failed_outputs、reported_tokens、latency。平台未提供费用/usage时为unknown，不能记0或擅自换算。

## 10. 评估实现与本轮报告

### 10.1 受控指标

预先冻结匹配规则，并对dev与holdout分别报告：

1. 当前偏离检测precision/recall/F1。
2. F/R/I多标签每类、macro/micro指标，support明确；unresolved与abstention单列。
3. 消息/agent/stage/round定位。
4. 严格claim对象定位：候选人、属性/规则、引文和冲突依据。
5. 时间状态及起始位置；只在参考具有必要前史的样例上算可确认时间准确率。
6. 无前史案例中“不当确定新出现/持续/回退”的比例，以及正确保留uncertain的比例。
7. 引用反驳、假设、合理更新、正常维持各层的误报率。
8. 答案正确但解释错误/过时的检出率；仅错误答案且无法细分的恰当unresolved率。
9. schema、引文、对象有效率，以及API失败/解析失败/拒答/截断覆盖。
10. 同样例两协议的配对差异、输入/输出token与延迟；同时报告双方有效的配对数量。

匹配先按类别无关的消息/对象/主张位置或预先认可等价主张一对一匹配，再评分类别；多claim用固定规则或最大匹配，不按“类别是否正确”挑配对。相同消息但候选/属性错不能得严格对象TP。规则层主张没有候选时按rule对象匹配。

严格定位召回以所有适用参考事件为分母，漏检进入分母，不能只在已匹配消息上再报告100%消息定位。引用依据允许明确的等价有效集合，避免只有一种文字解释能得分。

指标与遗漏：
- TP=0且存在可评估正例时F1按定义为0；无适用样本为null并说明。
- API/schema失败保留为未完成诊断，正例漏检与总体成功率反映其影响；不能把失败当成负例“正确拒报”。
- 负例误报率同时报告可判断覆盖率与端到端正确拒报率，防止大量失败让误报率虚假变低。
- 参考pending/ambiguous不混入确定参考分母，报告有效参考数量与各层缺口。
- 没有预先规定的综合通过阈值时，不依据结果临时设阈值宣称全部通过；报告逐层命中、错误与边界失败。
- 72只是小型受控pilot；同题/同模板相关，统计推断按family聚合，不能当72个完全独立自然样本。

### 10.2 自然MAD本轮允许的分析

可以计算不依赖人工语义标签的：集合正确率、候选错误率、可解析覆盖、标准状态变化、答案加入/排除、对象级稳定状态退化代理指标和更新适应代理指标。

明确这些是程序可计算的行为描述，不是已经验证的F/R/I真实分类或漂移机制。

同family四分支的T4/T5候选错误率可作配对描述：
E_noise−E_clean；
E_update_noise−E_update；
交互项(E_update_noise−E_update)−(E_noise−E_clean)。

不把update导致的合理答案变化算漂移；不把clean当金标；不把共享前史重复计数。任何区间按family整组处理，不能将1188条相关响应当1188个独立样本。

### 10.3 报告状态

至少设置：

```text
software_validation.status
controlled_reference_validation.status
controlled_judge.status
controlled_evaluation.status
mad_generation.status
real_annotation.status = deferred
real_diagnostic_evaluation.status = not_evaluated
```

在线未启用时controlled_judge=not_run，controlled_evaluation=not_evaluated；不能用mock填分。
受控结果只能支持“在所列受控情形和参考条件下的表现”，不能宣称真实MAD有效或分类穷尽全部漂移。

## 11. 后续真实人工评测（C部分，本轮只准备）

保留原132条真实目标抽样方案，但暂不运行对应Judge：

- 12题×共享T1/T2/T3各1条=36。
- 12题×4分支×T4/T5各1条=96。
- 合计132条唯一目标；后续两协议共264个逻辑请求。

使用固定seed按agent/round平衡，在同题同阶段尽量选择相同round/agent作四条件配对。不按答案正误或Judge标签挑样本；若数据缺失，记录缺失，不暗中替换成成功样本。

本轮生成待标注清单、两位标注者模板、仲裁模板与只展示截至目标时刻材料的盲标页面。隐藏Judge预测与程序给出的语义/时间结论。共享前史去重，保存消息引用血缘。

后续步骤：
1. 两人独立标注当前偏离、类别、对象/引文、时间依据及uncertain。
2. 统计分歧并仲裁；不得拿两种Judge互相一致当真值。
3. 转换为统一flat参考，保留explicit negative、uncertain与not_annotated。
4. 仅在已标注范围评分；未标注不等于无事件。
5. 正式启用后续真实Judge队列及端到端真实指标。
6. 若根据真实开发样本修改类别/提示词，独立评测需使用未参与修改的题目/轨迹。

尚无人工参考时，真实准确率、真实误报/漏报及语义定位结果均为“尚未评估”。程序答案错误率不替代它们。

## 12. 统一入口与运行门禁

请实现以下新接口；这些命令是待提供的接口要求，不是声称现有仓库已经支持。

在新实验目录中：

```bash
python scripts/run_pipeline.py --config config/experiment_gpu4_r2.json --prepare --validate --build-controlled --validate-controlled
python scripts/run_pipeline.py --config config/experiment_gpu4_r2.json --run-protocol --run-mad --preflight
python scripts/run_pipeline.py --config config/experiment_gpu4_r2.json --run-mad --resume --analyze-program --prepare-controlled-judge --prepare-deferred-real --report
```

默认执行A类完整流程；阶段开关不修改冻结的数据/模型配置。程序不可将全部阶段绑成“没API key就退出”。

新凭证在服务器配置并显式启用后的B类入口：

```bash
python scripts/run_pipeline.py --config config/experiment_gpu4_r2.json --run-online-judge --judge-config config/judge_controlled_r2.json --dataset controlled --logical-request-cap 144 --resume --evaluate-controlled --report
```

judge_controlled_r2.json至少明确：

```json
{
  "online_enabled_by_default": false,
  "api_key_env": "JUDGE_API_KEY_V3_NEW",
  "allow_legacy_key_fallback": false,
  "dataset": "controlled",
  "logical_request_cap": 144,
  "max_infrastructure_retries_per_request": 1,
  "max_total_formal_attempts": 288,
  "development_debug_budget": 0,
  "extra_extractor_budget": 0,
  "inherit_legacy_quota_overrides": false,
  "enable_real_trajectory_queue": false
}
```

模型ID、endpoint与推理参数从现有配置核验迁移，不在此JSON示例中凭空替换。未知额度采用当前明确的保守本地上限，不将旧实验进程override视为本轮授权。

GPU配置至少明确physical_gpu_index=4、expected_gpu_name=RTX4090、require_uuid_verification=true、allow_gpu_fallback=false、repeats=1。

## 13. 测试与验收清单

全部本地测试在临时目录/mocks运行，不写旧结果、不发真实Judge请求。

A类必须验收：
- 原数据/选题/旧结果哈希不变，四条件事实与噪声组合正确。
- 48序列、1188唯一MAD请求、2160视图引用，前史只生成/统计一次。
- 检查点等待T3-R2三agent；每agent历史正确；无额外同伴/兄弟分支/未来可见性。
- 深拷贝隔离；原子记录、blocked恢复和指纹拒绝混接。
- 无旧协议响应被导入本run；恢复只跳过本run同指纹成功响应。
- GPU4→UUID→服务PID映射正确，禁用自动换卡；未确认映射不启动。
- 72例覆盖表、36/36拆分、family/pair隔离、时间状态覆盖可核查。
- 参考来源与核验状态真实；预期标签/层名/split不进入请求。
- unknown、correction、事实版本及历史有效性一致。
- 正确答案错解释、无解释错答案、引用/假设/合理更新、无前史、更新后回退均有回归。
- 对象匹配、时间分母、F1=0、未标注/uncertain/失败处理正确。
- 144队列唯一，真实132清单标deferred且不会自动运行。
- 在线默认关闭；无旧key fallback、无旧quota继承；密钥不入日志/Git。
- 缺少密钥仍能prepare、test、run MAD、build cases与report。
- mock输出不计入真实实验成绩；缺少人工参考不输出真实准确率。

B类验收：
- 新凭证与显式启用条件真实满足，模型/接口经服务器核验。
- 技术预检与正式队列分账，调试/额外调用/重试分别记账。
- dev与holdout隔离，holdout在方法冻结后执行。
- 144逻辑请求终态与成功/失败明细一致，不能把失败记录称为成功诊断。
- 参考可用范围、每层分母、两协议配对与资源统计可追溯。

C类本轮验收仅为材料准备；状态保持deferred/not_evaluated。

运行适当的v3测试及受影响v2回归、编译检查和git diff --check；保留测试报告。预检失败修复实现后，按是否改变指纹决定新run/协议版本，不覆盖冻结记录。

## 14. 产物与最终汇报

至少交付：

- config/experiment_gpu4_r2.json、config/judge_controlled_r2.json；
- docs/task_definition.md、judge_rubric.md、metrics.md、controlled_case_spec.md、annotation_guidelines.md、RUNBOOK_ZH.md；
- data/source_manifest.json、selection_manifest、四条件evidence_sequences、请求图、branch_views；
- data/controlled/cases.jsonl、expected_labels.jsonl、coverage_manifest.json、split_manifest.json、reference_validation.json；
- results/<run_id>/mad原始记录、检查点、attempt日志、程序状态与统计；
- results/<run_id>/controlled_judge/的144队列、输入包、预检清单、配置/提示词指纹；在线执行后再有真实响应和分数；
- annotation/deferred_real/的132抽样清单、盲标页面、模板及转换验证工具；
- runtime_manifest、数据/历史/图/数量/凭证门禁验证报告；
- RUN_SUMMARY_ZH.md，明确A/B/C的actual status。

最终向用户分别汇报：

A. 实际分支/基线/提交、改动、测试、72例及核验覆盖、GPU4身份、1188请求各状态、原始产物与复现命令。
B. 新凭证是否配置、在线是否启用、实际144逻辑请求完成情况、额外调用、受控dev/holdout结果；未启用则明确未运行。
C. 待标注材料准备情况；独立人工与真实诊断评测尚未开展。

仅代码和数据文件完成，不能写成模型实验完成；仅程序测试通过，不能写成LLM诊断有效；仅受控表现良好，不能写成真实MAD已验证有效或分类体系已经完备。
