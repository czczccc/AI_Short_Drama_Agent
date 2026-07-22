# Prompt管理规范

所有Prompt禁止写死在代码。

统一管理：

app/prompts/

director

writer

character

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

## Writer v1

Phase 2B 使用 `app/prompts/writer_v1.md`。Prompt 要求：

- 输入故事整体大纲、角色设定、指定分集大纲和目标时长
- 只生成指定一集，不批量生成 10 集剧本
- 开场前 5 秒出现冲突或悬念，对白短且适合表演
- 每场推进剧情并至少包含动作或对白
- 结尾形成下一集钩子，不新增无关主要角色
- 只使用大纲中的 `character_id`
- 只输出合法 JSON，不包含 Markdown 或额外解释
- 提供与 `EpisodeScript` 一致的完整 JSON 示例

## Character v1

Phase 2C 使用 `app/prompts/character_v1.md`。Prompt 要求：

- 一次深化当前项目全部主要角色，不逐角色调用模型
- 保持原 `character_id`、姓名、年龄和角色定位，不新增或删除角色
- 输出可指导编剧和表演的说话方式、行为边界、关系、成长弧线和连续性规则
- 视觉身份只保存文字描述，不生成图片或图像/视频 Prompt
- 只输出合法 JSON，不包含 Markdown 或解释文字
