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

Phase 2C 的 Character Agent 一次读取完整故事大纲并生成全部主要角色圣经，经 Pydantic 和大纲上下文校验后，以 `character_id` 为 key 保存到 `Project.characters_json`。用户可以查询或整体替换角色圣经。Writer 生成新剧本时优先读取角色圣经；旧项目没有角色圣经时继续使用 `StoryOutline.characters`。

Phase 3.1 增加 Showrunner State MVP：在大纲和角色圣经均已生成后，Showrunner Agent 读取 `outline_json` 与 `characters_json`，生成整季总控状态并保存到 `Project.showrunner_json`。该状态包含 Story Bible、Episode Plan 和 Character Arc，用于后续 Writer Brief 与 Showrunner QC 的基础数据。本阶段不修改 Writer、Story Memory 或 QC 流程。

Phase 3.2 增加 Writer Brief MVP：在 Showrunner State 已生成后，Showrunner Agent 可为指定第 N 集读取 Story Bible、该集 Episode Plan、角色弧线和当前 Story Memory，生成单集 Writer Brief，并保存到 `showrunner_json.writer_briefs[N]`。本阶段只生成和查询 Brief，不把 Brief 接入 Writer，不改变剧本保存和 Story Memory 更新流程。

Phase 3.3 将已保存 Writer Brief 作为可选输入接入 Writer：生成剧本请求默认不使用 Brief，保持旧流程；当请求设置 `use_showrunner_brief=true` 时，系统读取 `showrunner_json.writer_briefs[N]` 并传给 Writer Agent，Writer Prompt 要求优先遵守 Brief。若该集 Brief 不存在，接口返回错误，不自动生成 Brief。本阶段仍不改变剧本保存和 Story Memory 更新流程。

Phase 3.4 增加 Showrunner QC 门禁：当生成剧本请求设置 `run_showrunner_qc=true` 时，必须同时设置 `use_showrunner_brief=true` 并存在当前集 Writer Brief。Writer 输出先作为 draft 交给 QC Agent 检查，QC 输入包含 draft、Writer Brief、Story Memory、角色设定和分集边界。只有 QC 报告 `status=pass` 时，系统才保存正式剧本到 `scripts_json` 并更新正式 `memory_json`；当 QC 为 `warning` 或 `fail` 时，接口返回错误，不保存 draft、不更新 Story Memory，但会把 QC 报告保存到 `showrunner_json.qc_reports[N]` 供查询。

Phase 2D-1 增加 Story Memory v1：每集剧本生成并校验成功后，系统从 `EpisodeScript` 中提取本集摘要、新增场景事实、出场角色状态和结尾钩子，保存到 `Project.memory_json`。角色状态按该角色实际出场场景提取：`knows` 保存该角色参与场景的 scene goal，`current_goal` 保存该角色最后一次出场场景目标。之后生成后续集时，Writer 会收到此前已保存的 `story_memory`，用于承接前文。重生成第 N 集时会覆盖第 N 集 memory，并删除第 N 集之后的旧 memory，避免后续上下文基于过期剧本。

Showrunner 门禁流程原则：Writer 生成的剧本在 `run_showrunner_qc=true` 时先作为 draft 接受 Showrunner QC；只有 QC 通过后，才能保存为正式剧本并更新正式 Story Memory。QC 不通过时，草稿事实不得写入 `memory_json`。

LLM QC v1 是剧本生成后的人工确认辅助步骤：对已保存的第 N 集剧本读取 Story Outline、Character Bible、Story Memory 和当前剧本，调用 QC Agent 生成结构化质检报告。v1 只返回问题清单、严重级别和修改建议，不自动改写剧本、不覆盖已保存剧本。确认 QC 报告后，再由人工决定是否重生成或手动编辑剧本。

## 工作流日志

后端会为每个 HTTP 请求生成或继承 `X-Request-ID`，并将关键工作流节点写入本地 JSONL 日志，默认路径为 `logs/app.jsonl`。当前记录的事件包括项目创建、大纲生成、角色圣经保存、Showrunner State 生成、Writer Brief 生成、Writer draft 生成、Showrunner QC 保存/通过/拦截、正式剧本保存以及 HTTP 请求完成/失败。

日志只保存可排查链路的元数据，例如 `project_id`、`episode_number`、`event`、`status_code`、`duration_ms` 和 `qc_status`，不保存完整 Prompt、API Key 或完整剧本正文。本地开发可通过 `/dev/logs` 按项目查询最近日志，用于复盘“用户输入一句创意后具体发生了什么”。

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
