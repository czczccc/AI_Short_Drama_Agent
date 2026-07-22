# 模型接入规范

## LLM

职责：
- 剧本
- 分镜
- Prompt生成

Phase 2A 使用 Director Agent 生成结构化短剧大纲。Phase 2B 在同一 Provider 接口上增加 Writer Agent，用于生成单集结构化剧本。Phase 2C 使用 Character Agent 一次生成当前项目全部角色圣经。

当前默认 Provider：DeepSeek V4 Pro。

未来计划 Provider：OpenAI（本阶段不实现）。

业务层只依赖通用 `LLMProvider.generate_structured(system_prompt, user_prompt, output_schema)`，不依赖供应商 SDK 或专有类型。新增 OpenAI 支持时，只新增对应 Provider 并通过 `LLM_PROVIDER=openai` 选择；Director Agent、Outline Service、API、Schema 和数据库保持不变。

Writer Agent 同样只依赖 `LLMProvider`，不直接导入或创建 DeepSeek 客户端。Writer 输入整体大纲、角色设定、指定分集大纲和目标时长，输出经 `EpisodeScript` 及大纲上下文二次校验后才能持久化。

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

统一接口：

submit()

get_status()

download()

cancel()


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
