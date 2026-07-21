# 模型接入规范

## LLM

职责：
- 剧本
- 分镜
- Prompt生成

Phase 2A 当前范围仅包含 Director Agent 的结构化短剧大纲生成。

当前默认 Provider：DeepSeek V4 Pro。

未来计划 Provider：OpenAI（本阶段不实现）。

业务层只依赖通用 `LLMProvider.generate_structured(system_prompt, user_prompt, output_schema)`，不依赖供应商 SDK 或专有类型。新增 OpenAI 支持时，只新增对应 Provider 并通过 `LLM_PROVIDER=openai` 选择；Director Agent、Outline Service、API、Schema 和数据库保持不变。

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
