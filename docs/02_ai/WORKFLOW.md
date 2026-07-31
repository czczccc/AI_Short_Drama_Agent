# 工作流设计

## 剧本流程

创意输入

↓

Director Agent

↓

Story Bible

↓

Character Agent

↓

Character Bible

↓

Writer Agent

↓

Episode Script

Phase 2B 每次只处理一个指定 `episode_number`：从 Project 的 `outline_json` 读取整体大纲和对应分集，Writer Agent 生成结构化剧本，经 Pydantic 校验后按集号合并保存到 `scripts_json`。同集重新生成会覆盖旧值，不影响其他集。

Writer 的基础 JSON/Schema 错误由 Provider 执行一次结构修复；集号、目标时长或角色 ID 等上下文二次校验失败时，由 Writer Agent 把安全原因反馈给模型并最多重新生成一次。上下文修复与 Showrunner QC 返修是两个独立层级，任何未通过的结果都不会保存为正式剧本。

Phase 2C 的 Character Agent 一次读取完整故事大纲并生成全部主要角色圣经，经 Pydantic 和大纲上下文校验后，以 `character_id` 为 key 保存到 `Project.characters_json`。用户可以查询或整体替换角色圣经。Writer 生成新剧本时优先读取角色圣经；旧项目没有角色圣经时继续使用 `StoryOutline.characters`。

Character Agent 的基础 JSON/Schema 错误由 Provider 执行一次结构修复；角色 ID 集合或身份字段等上下文二次校验失败时，由 Character Agent 把安全原因码反馈给模型并最多重新生成一次。任何最终失败的角色结果都不会写入 `characters_json`。

Phase 3.1 增加 Showrunner State MVP：在大纲和角色圣经均已生成后，Showrunner Agent 读取 `outline_json` 与 `characters_json`，生成整季总控状态并保存到 `Project.showrunner_json`。该状态包含 Story Bible、完整 10 集 Episode Plan 和稀疏 Character Arc 关键转折，用于后续 Writer Brief 与 Showrunner QC 的基础数据。为控制单次模型输出规模，Prompt 要求新状态每个角色通常只生成 2–4 个真正发生变化的关键 beat；旧的逐集 beat 状态仍兼容读取。本阶段不修改 Writer、Story Memory 或 QC 流程。

Phase 3.2 增加 Writer Brief MVP：在 Showrunner State 已生成后，Showrunner Agent 可为指定第 N 集读取 Story Bible、该集 Episode Plan、角色弧线和当前 Story Memory，生成单集 Writer Brief，并保存到 `showrunner_json.writer_briefs[N]`。当前集没有专属角色弧线 beat 时，Brief 输入使用此前最近转折和角色整季起止状态进行推导，并把下一次未来转折仅作为禁止提前展开的边界。本阶段只生成和查询 Brief，不把 Brief 接入 Writer，不改变剧本保存和 Story Memory 更新流程。

Phase 3.3 将已保存 Writer Brief 作为可选输入接入 Writer：生成剧本请求默认不使用 Brief，保持旧流程；当请求设置 `use_showrunner_brief=true` 时，系统读取 `showrunner_json.writer_briefs[N]` 并传给 Writer Agent，Writer Prompt 要求优先遵守 Brief。若该集 Brief 不存在，接口返回错误，不自动生成 Brief。本阶段仍不改变剧本保存和 Story Memory 更新流程。

Phase 3.4 增加 Showrunner QC 门禁：当生成剧本请求设置 `run_showrunner_qc=true` 时，必须同时设置 `use_showrunner_brief=true` 并存在当前集 Writer Brief。Writer 输出先作为 draft 交给 QC Agent 检查，QC 输入包含 draft、Writer Brief、Story Memory、角色设定和分集边界。只有 QC 报告 `status=pass` 时，系统才保存正式剧本到 `scripts_json` 并更新正式 `memory_json`；当 QC 为 `warning` 或 `fail` 时，接口返回错误，不保存 draft、不更新 Story Memory，但会把 QC 报告保存到 `showrunner_json.qc_reports[N]` 供查询。

Phase S3-5 增加 QC v2 连续性门禁：规则型 QC 先检查场景密度和场景角色一致性，LLM QC 再检查钩子是否在实际场景落地、上一集末场承接、分集边界、角色认知、时间地点与道具状态。请求可用 `max_revision_attempts=0–2` 显式开启有限返修；失败报告作为 `revision_feedback` 传回 Writer，多轮问题累积去重，达到上限仍未通过则不保存 draft。

Story Memory v2：QC 通过时，QC 报告必须同时输出基于实际场景的 `approved_memory`，包含新增事实、角色认知、道具与证据、未解决问题和末场状态。只有该快照会以 `source=qc_approved` 写入正式上下文。未开启 QC 的兼容流程仍可生成 `source=rule_extracted` 的保守摘要，但 Writer 和 Brief 不得把其中仅存在于顶部目标或钩子字段的声明视为已发生事实。重生成第 N 集仍会删除第 N 集之后的旧 memory。

Showrunner 门禁流程原则：Writer 生成的剧本在 `run_showrunner_qc=true` 时先作为 draft 接受规则型 QC 和 Showrunner QC；只有 QC 通过后，才能保存为正式剧本并更新正式 Story Memory。QC 不通过时，草稿事实不得写入 `memory_json`。

LLM QC v1 是剧本生成后的人工确认辅助步骤：对已保存的第 N 集剧本读取 Story Outline、Character Bible、Story Memory 和当前剧本，调用 QC Agent 生成结构化质检报告。v1 只返回问题清单、严重级别和修改建议，不自动改写剧本、不覆盖已保存剧本。确认 QC 报告后，再由人工决定是否重生成或手动编辑剧本。

## 工作流日志

后端会为每个 HTTP 请求生成或继承 `X-Request-ID`，并将关键工作流节点写入本地 JSONL 日志，默认路径为 `logs/app.jsonl`。当前记录的事件包括项目创建、大纲生成、角色圣经保存、Showrunner State 生成、Writer Brief 生成、Writer draft 生成、QC 评估、自动返修请求、Showrunner QC 保存/通过/拦截、正式剧本保存、LLM Provider 调用开始/完成/失败以及 HTTP 请求完成/失败。

日志只保存可排查链路的元数据，例如 `project_id`、`episode_number`、`event`、`status_code`、`duration_ms`、`qc_status`、`output_schema`、`failure_stage` 和 Writer 上下文校验的安全 `failure_reasons`，不保存完整 Prompt、API Key、完整模型输出或完整剧本正文。本地开发可通过 `/dev/logs` 按项目查询最近日志，用于复盘“用户输入一句创意后具体发生了什么”。

↓

Storyboard Agent

↓

Shot List


## 视频流程

Shot

↓

Prompt Adapter

↓

Video Provider

↓

任务轮询

↓

素材保存

↓

FFmpeg合成
