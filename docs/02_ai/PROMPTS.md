# Prompt管理规范

所有Prompt禁止写死在代码。

统一管理：

app/prompts/

director

writer

storyboard

video_adapter

qc


每个Prompt包含：

目标

输入

输出格式

限制条件

示例

## Director v1

Phase 2A 使用 `app/prompts/director_v1.md`。Prompt 要求：

- 只输出合法 JSON，不包含 Markdown 或额外解释
- 所有内容使用中文，面向中文竖屏短剧
- 强冲突、快节奏，每集结尾有悬念，角色动机明确
- 不模仿受版权保护的具体影视角色，不使用现实名人身份和肖像
- 提供完整 JSON 结构示例，并与 Pydantic Schema 字段一致
