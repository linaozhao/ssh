# R2 运行说明

所有命令从本实验目录执行。先看 `RUN_SUMMARY_ZH.md`，不要因请求图已生成就认定模型已运行。

## 离线阶段

```bash
python scripts/run_pipeline.py --prepare --validate --build-controlled --validate-controlled
python scripts/run_pipeline.py --analyze-program --prepare-controlled-judge --prepare-deferred-real --evaluate-controlled --report
```

prepare/build/queue为冻结输出：内容不同则拒绝覆盖，须使用新目录/版本。
旧数据、代码、选题记录、已跟踪结果的哈希在 `data/source_manifest.json`。
分析无新MAD记录时输出 `not_run`，无Judge输出时输出 `not_evaluated`。

## GPU4 门禁与MAD

启动前必须在可访问宿主NVML的环境中执行只读检查；不能以容器逻辑编号猜测物理卡。

```bash
RUN=cbm_drift_v3_shared_history_pilot_r2_20261109T084647Z
PYTHONPATH=src python -m cbm_drift_v3.runtime --config config/experiment_gpu4_r2.json --manifest results/$RUN/runtime_manifest.json
```

卡不可用则停止GPU部分。只可在没有外来计算进程、显存足够时显式启动：

```bash
bash scripts/launch_qwen_service.sh config/experiment_gpu4_r2.json results/$RUN/service_manifest.json
```

启动器使用当前Python；须事先核验该环境已有vLLM及其参数。不自动安装、量化或更换模型。
启动器是前台服务监督进程，只管理本任务创建的session。另一个终端执行：

```bash
python scripts/run_pipeline.py --run-protocol --run-mad --preflight --resume --report
python scripts/run_pipeline.py --run-mad --resume --analyze-program --report
```

前198条是本run前两题的完整新请求，正式续跑不重复。静态108单独记账。
执行器串行发请求，遵守family并发1、请求并发不超过3。会等待真实依赖和T3三agent屏障。
每次使用真实chat template计算输入长度，预留1024输出tokens；超限阻塞，不删前史。
只有同run、代码/数据/配置/请求/父历史指纹一致的成功记录可跳过。
格式错误保留并可作为后续原文；语义错误不重采样。基础设施最多3次总attempt。
Interrupted attempt也计入预算，不能通过重启无限重试。

## 在线受控Judge

本轮不从聊天消息读取密钥。新凭证只经本地安全输入注入环境，例如在你的服务器交互终端：

```bash
read -rsp 'New Judge key: ' JUDGE_API_KEY_V3_NEW
export JUDGE_API_KEY_V3_NEW
```

这不会把真实值写进命令行参数或仓库。不要把真实密钥填进配置JSON、历史日志或Git。
当前provider地址沿用旧配置起点，但所要求的DeepSeek-v4.1 flash实际模型ID尚未验证。
必须先在该凭证下核验接口、权限和实际返回模型，再为已核验配置建立新的冻结Judge目录。
不得把旧 `deepseek/deepseek-v4-flash` 当成已核验的v4.1。
当前队列是144个待执行逻辑目标，模型配置尚未核验；配置改变时旧队列保留，不混用输出。

```bash
python scripts/run_pipeline.py --run-online-judge --judge-config config/judge_controlled_r2.json --dataset controlled --logical-request-cap 144 --resume --evaluate-controlled --report
```

在线默认为关；上述开关只是显式启用条件之一，还必须有本地新凭证和已核验模型。
最多144逻辑请求、每条最多一次基础设施重试、总HTTP上限288。
保守窗口最多100次attempt/5小时，触顶停止；不自动五小时轮询或充值。
12预检请求计入144；先72 dev，再冻结进入72 holdout。分类错不重试。
更改prompt/schema/参考后必须新版本，开发调用单列，不能把已看过的holdout当新留出。

## 后续人工工作

`annotation/deferred_real/blind_annotation.html` 可直接本地打开，不需要服务器。
MAD未生成时目标内容显示not_generated，人工模板是not_annotated，不是显式负例。
真实132条补齐后生成新的材料版本，保留原清单。两人独立标注、仲裁之后才能启用后续264请求。

```bash
python scripts/flatten_annotation.py annotation/deferred_real/annotator_1_template.jsonl /tmp/annotation_flat.jsonl
```

flatten不把未标注、uncertain转成no，也不读取Judge预测替代人工参考。
