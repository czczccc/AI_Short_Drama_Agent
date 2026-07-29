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
showrunner


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

## Writer v2

Phase 2B 当前使用 `app/prompts/writer_v2.md`。Prompt 要求：

- 输入故事整体大纲、角色设定、已生成剧本的 `story_memory`、指定分集大纲、相邻分集边界和目标时长
- 只生成指定一集，不批量生成 10 集剧本
- `current_episode_outline` 是唯一可完整展开的剧情范围
- `previous_episode_outline` 只用于承接已发生事实，`next_episode_outline` 只保留下一集编号和标题作为边界提示
- `story_memory` 用于承接此前已生成剧本中已经保存的事实、出场角色和结尾钩子
- `writer_brief` 为可选输入；当不为 `null` 时，Writer 必须优先遵守 Brief 中的本集写作边界、必写节拍、禁止内容、角色认知和结尾要求
- 不提前引入后续集才首次出现的核心事件、关键线索、人物首次登场、关系反转、死亡/复活、身份揭露、证据结果或结局
- 检查角色事实、标志道具、人物认知、剧情事实和首次见面关系一致性
- 开场前 5 秒出现冲突或悬念，对白短且适合表演
- `duration_seconds` 必须尽量贴近请求目标时长，允许偏差不超过 3 秒
- 每场推进剧情并至少包含动作或对白
- 结尾形成下一集钩子，不新增无关主要角色
- 只使用大纲中的 `character_id`
- 每个场景的对白数组字段必须使用 `dialogues`
- 只输出合法 JSON，不包含 Markdown 或额外解释
- 提供与 `EpisodeScript` 一致的完整 JSON 示例

## Character v1

Phase 2C 使用 `app/prompts/character_v1.md`。Prompt 要求：

- 一次深化当前项目全部主要角色，不逐角色调用模型
- 保持原 `character_id`、姓名、年龄和角色定位，不新增或删除角色
- 输出可指导编剧和表演的说话方式、行为边界、关系、成长弧线和连续性规则
- 视觉身份只保存文字描述，不生成图片或图像/视频 Prompt
- 只输出合法 JSON，不包含 Markdown 或解释文字

## QC v1

LLM QC v1 使用 `app/prompts/qc_v1.md`。Prompt 要求：

- 只检查指定单集已保存剧本，不改写剧本
- 输入有限故事大纲上下文、角色设定、当前剧本、上一集承接信息、下一集边界、Story Memory 和可选 Writer Brief
- 当 `writer_brief` 不为 `null` 时，必须检查剧本是否遵守 Brief 中的允许范围、必写节拍、禁止内容、角色认知、连续性承接、道具证据和结尾要求
- 检查当前剧本是否严格限制在本集大纲范围内
- 检查是否提前展开后续集才应出现的核心事件、关键线索、人物关系反转、身份揭露、证据结果或结局
- 检查角色认知、角色动机、说话方式、行为边界、标志道具、证据、地点和时间线是否与角色设定及 Story Memory 冲突
- 只输出合法 JSON，不包含 Markdown 或解释文字
- 输出必须符合 `QCReport`，`status` 只能是 `pass`、`warning` 或 `fail`

## Showrunner v1

Phase 3.1 使用 `app/prompts/showrunner/v1.py`。Prompt 要求：

- 只输出合法 JSON，不包含 Markdown 或解释文字
- 所有文本内容使用中文，面向中文竖屏短剧
- 根据已有 `story_outline` 和 `character_bibles` 生成整季总控状态
- 不写单集剧本正文，不执行剧本 QC，不新增大纲之外的主要角色
- `episode_plan` 必须正好包含第 1 到第 10 集
- 每个角色的 `episode_beats` 必须正好包含第 1 到第 10 集
- `version` 固定为 `showrunner_v1`
- `source_outline_hash` 和 `source_characters_hash` 必须原样复制输入值；服务层会再次覆盖为本地稳定 SHA-256 结果
- `writer_briefs` 与 `qc_reports` 本阶段固定为空对象

## Showrunner Brief v1

Phase 3.2 使用 `app/prompts/showrunner/brief_v1.py`。Prompt 要求：

- 只输出合法 JSON，不包含 Markdown 或解释文字
- 所有文本内容使用中文
- 只为指定 `episode_number` 生成 Writer Brief，不写剧本正文、不生成场景或对白
- 输入 Showrunner State、当前集 Episode Plan、当前集角色弧线 beat、Story Memory 和目标时长
- Brief 必须明确本集 `allowed_scope`、`required_beats`、`forbidden_content`、角色当前知道/不能知道的信息、连续性承接、道具证据和结尾钩子边界
- 不提前展开后续集的核心事件、关键线索、身份揭露、证据结果、关系反转或结局
- `episode_number` 和 `target_duration_seconds` 必须与请求一致
