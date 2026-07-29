# 模型接入规范

## LLM

职责：
- 剧本
- 分镜
- Prompt生成

Phase 2A 使用 Director Agent 生成结构化短剧大纲。Phase 2B 在同一 Provider 接口上增加 Writer Agent，用于生成单集结构化剧本。Phase 2C 使用 Character Agent 一次生成当前项目全部角色圣经。LLM QC v1 使用 QC Agent 对已保存单集剧本生成结构化质检报告。

当前默认 Provider：DeepSeek V4 Pro。

未来计划 Provider：OpenAI（本阶段不实现）。

业务层只依赖通用 `LLMProvider.generate_structured(system_prompt, user_prompt, output_schema)`，不依赖供应商 SDK 或专有类型。新增 OpenAI 支持时，只新增对应 Provider 并通过 `LLM_PROVIDER=openai` 选择；Director Agent、Outline Service、API、Schema 和数据库保持不变。

Writer Agent 同样只依赖 `LLMProvider`，不直接导入或创建 DeepSeek 客户端。Writer 输入整体大纲、角色设定、已生成剧本的 `story_memory`、指定分集大纲、相邻分集边界和目标时长，输出经 `EpisodeScript` 及大纲上下文二次校验后才能持久化。传给模型的整体大纲只包含前一集和当前集的完整分集信息，下一集只保留编号和标题作为边界提示，用于约束当前集只展开本集大纲，避免提前完成后续集核心事件、关键线索或人物关系反转。Writer 输出的 `duration_seconds` 必须与请求目标时长偏差不超过 3 秒，否则视为 LLM 结构响应无效。

Phase 2D-1 使用规则型 Story Memory v1，不额外调用 LLM：每集剧本成功生成后，从结构化剧本中提取 episode goal、scene goal、出场角色和 ending hook，保存为 `Project.memory_json`。角色记忆按出场场景写入 `knows`，`current_goal` 使用该角色最后一次出场场景目标，不再把整集目标无差别写入所有角色。后续生成第 N 集时，Writer 输入会携带此前已保存的 Story Memory。重生成第 N 集会重建第 N 集 memory，并丢弃第 N 集之后的旧 memory。旧项目如果已有 `scripts_json` 但没有 `memory_json`，读取时会从已保存剧本懒回填 Story Memory。

LLM QC v1 仍只依赖 `LLMProvider.generate_structured(system_prompt, user_prompt, output_schema)`。QC 输入包含有限故事大纲上下文、角色设定、当前剧本、相邻分集边界和 Story Memory；输出必须通过 `QCReport` Schema 校验。v1 只返回报告，不自动改写剧本、不覆盖 `scripts_json`，也不持久化 QC 结果。

Character Agent 只依赖同一 `LLMProvider`，输入完整大纲、原始角色概念、世界观、核心冲突和十集大纲，一次输出全部 `CharacterBible`。模型输出必须经过角色 ID 集合、身份字段和关系引用的上下文二次校验。Writer 在 `characters_json` 存在时优先使用角色圣经，否则回退到原始角色概念。

## DeepSeek Provider

- 使用官方 OpenAI 兼容 Chat Completions API
- `base_url`、模型、超时、最大 token 和 thinking 开关均来自环境变量
- 使用 `response_format={"type": "json_object"}`
- 流程固定为 JSON 字符串 → `json.loads` → Pydantic Schema 校验
- 默认关闭 thinking；可通过环境变量开启，不修改业务代码
- 上游异常在 Provider 边界转换为分类异常，API 只返回清理后的错误
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
