# 模型接入规范

## LLM

职责：
- 剧本
- 分镜
- Prompt生成

Phase 2A 使用 Director Agent 生成结构化短剧大纲。Phase 2B 在同一 Provider 接口上增加 Writer Agent，用于生成单集结构化剧本。Phase 2C 使用 Character Agent 一次生成当前项目全部角色圣经。LLM QC v1 使用 QC Agent 对已保存单集剧本生成结构化质检报告。Phase 3.1 使用 Showrunner Agent 根据已生成大纲和角色圣经生成整季总控状态。Phase 3.2 使用 Showrunner Agent 为指定集生成 Writer Brief。Phase 3.3 允许 Writer Agent 在请求开启时读取并遵守已保存 Writer Brief。Phase 3.4 增加 Showrunner QC 门禁：Writer draft 只有 QC 通过后才保存为正式剧本并更新 Story Memory。

当前默认 Provider：DeepSeek V4 Pro。

未来计划 Provider：OpenAI（本阶段不实现）。

业务层只依赖通用 `LLMProvider.generate_structured(system_prompt, user_prompt, output_schema)`，不依赖供应商 SDK 或专有类型。新增 OpenAI 支持时，只新增对应 Provider 并通过 `LLM_PROVIDER=openai` 选择；Director Agent、Outline Service、API、Schema 和数据库保持不变。

Writer Agent 同样只依赖 `LLMProvider`，不直接导入或创建 DeepSeek 客户端。Writer 输入整体大纲、角色设定、已生成剧本的 `story_memory`、指定分集大纲、相邻分集边界、目标时长和可选 `writer_brief`，输出经 `EpisodeScript` 及大纲上下文二次校验后才能进入后续保存流程。传给模型的整体大纲只包含前一集和当前集的完整分集信息，下一集只保留编号和标题作为边界提示，用于约束当前集只展开本集大纲，避免提前完成后续集核心事件、关键线索或人物关系反转。Writer 输出的 `duration_seconds` 必须与请求目标时长偏差不超过 3 秒，否则视为 LLM 结构响应无效。`use_showrunner_brief` 默认为 `false`；设为 `true` 时，业务层只读取已保存 Brief，不自动生成 Brief。

Writer 输出通过基础 Schema 但未通过上下文二次校验时，会先记录 `workflow.writer.context_retrying` 并把 `duration_mismatch`、`episode_number_mismatch`、`unknown_character_id` 等安全原因反馈给模型，最多重新生成一次完整剧本。第二次仍失败时记录 `workflow.writer.validation_failed` 并返回 502；日志只包含原因码和数值元数据，不记录剧本正文。

Story Memory v2 在 Showrunner QC 通过时使用同一次 QC 调用输出的 `approved_memory`，不增加额外模型调用。该快照只从实际场景提取事实、人物认知、道具状态和末场状态，并标记 `source=qc_approved`。未开启 QC 或旧项目懒回填时继续使用规则型保守摘要并标记 `source=rule_extracted`。重生成第 N 集会重建第 N 集 memory，并丢弃第 N 集之后的旧 memory。

LLM QC 仍只依赖 `LLMProvider.generate_structured(system_prompt, user_prompt, output_schema)`。QC 输入包含规则型问题、有限大纲上下文、角色设定、当前剧本、相邻分集边界、Story Memory 和可选 Writer Brief；输出必须通过 `QCReport` Schema 校验。`status=pass` 时必须同时输出 `approved_memory`。开发辅助 QC 只返回报告，不自动改写或持久化；正式 Showrunner 门禁可以按 `max_revision_attempts` 将问题反馈给 Writer 有限返修，多轮反馈会按问题码和消息累积去重。

Showrunner Agent 只依赖同一 `LLMProvider`。生成 Showrunner State 时，输入精简后的 `StoryOutline`、`CharacterBibleCollection`、`source_outline_hash` 和 `source_characters_hash`，输出必须通过 `ShowrunnerState` Schema 校验后保存到 `Project.showrunner_json`。输入会删除大纲中与角色圣经重复的角色概念，并从角色圣经移除无关视觉细节，只保留剧情连续性和标志道具所需字段。Character Arc 使用稀疏关键转折：Prompt 要求每个角色通常只生成 2–4 个真正发生变化的 `episode_beats`；Schema 允许稀疏列表并继续兼容旧的 10 集完整 beat。哈希仍基于完整已保存数据，由业务层使用 `json.dumps(..., sort_keys=True, separators=(",", ":"))` 的稳定 JSON 内容计算 SHA-256，不使用 Python 内置 `hash()`。

生成 Writer Brief 时，Showrunner Agent 输入已保存的 `ShowrunnerState`、指定 `episode_number`、目标时长和当前 `StoryMemory`，输出必须通过 `WriterBrief` Schema 校验后保存到 `showrunner_json.writer_briefs[episode_number]`。若当前集没有专属 Character Arc beat，输入会同时提供此前最近转折和下一次未来转折，后者只能作为边界而不能当作已发生事实。服务层会校验模型返回的 `episode_number` 和 `target_duration_seconds` 必须与请求一致。Phase 3.3 已将已保存 Brief 作为可选输入接入 Writer；Phase 3.4 已实现 draft + QC 门禁；Phase S3-5 已实现最多两次的显式自动返修。

Character Agent 只依赖同一 `LLMProvider`，输入完整大纲、原始角色概念、世界观、核心冲突和十集大纲，一次输出全部 `CharacterBible`。模型输出必须经过角色 ID 集合、身份字段和关系引用的上下文二次校验。首次上下文校验失败时，Agent 会把缺失/多余角色 ID 或身份冲突字段等安全原因反馈给模型，并最多重新生成一次完整角色圣经；第二次仍失败才返回 502。Writer 在 `characters_json` 存在时优先使用角色圣经，否则回退到原始角色概念。

## DeepSeek Provider

- 使用官方 OpenAI 兼容 Chat Completions API
- `base_url`、模型、超时、最大 token 和 thinking 开关均来自环境变量
- 使用 `response_format={"type": "json_object"}`
- 流程固定为 JSON 字符串 → `json.loads` → Pydantic Schema 校验
- 空响应、非法 JSON 或 Schema 校验失败时，Provider 会把安全的字段路径、错误类型和不超过 200 字的校验消息反馈给模型，并最多自动重试两次完整结构化生成；远端调用错误不自动重试
- 默认关闭 thinking；可通过环境变量开启，不修改业务代码
- 上游异常在 Provider 边界转换为分类异常，API 只返回清理后的错误
- Provider 边界会写结构化日志：`llm.call.started`、`llm.call.retrying`、`llm.call.completed`、`llm.call.failed`
- LLM 日志只记录 provider、model、输出 Schema、输入字符数、响应字符数、耗时和失败阶段，不记录 API Key、完整 Prompt 或完整模型输出
- 不使用正则、Markdown 截取、`eval` 或无 Schema 字典持久化


## Video Provider

Phase 3-1 已完成 Video Provider 抽象接口。本阶段只提供统一合同和 Fake Provider，不接真实视频供应商、不提交外部任务、不保存视频任务到数据库。

统一接口：

- `submit(request: VideoSubmitRequest) -> VideoTask`
- `get_status(provider_task_id: str) -> VideoTask`
- `download(provider_task_id: str) -> bytes`
- `cancel(provider_task_id: str) -> VideoTask`

统一任务状态：

- `pending`
- `running`
- `succeeded`
- `failed`
- `canceled`

当前默认 Provider：`fake`。`FakeVideoProvider` 只用于自动测试和本地流程验证，返回 `fake://` 视频地址，不调用任何外部视频 API。


## Provider模式

业务层不知道具体模型。

支持：

Seedance

Kling

Veo


## 必须记录

- 请求参数
- 返回结果
- 消耗
- 失败原因
