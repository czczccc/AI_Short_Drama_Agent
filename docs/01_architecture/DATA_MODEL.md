# 数据模型

## Project

项目基本信息。

字段：
id
name
status
idea
outline_json
characters_json
scripts_json
memory_json
showrunner_json
created_at
updated_at

Phase 2C 将项目的角色圣经保存为 `characters_json`，顶层 key 为稳定的 `character_id`。当前不创建 Character 独立数据库表；只有出现跨项目复用、素材版本、多用户协作或复杂单角色查询时才考虑迁移。

Story Memory v2 保存到 `memory_json`，顶层包含 `version=story_memory_v2` 和按集号组织的 `episodes`。每集记录 `source`、实际新增事实、人物认知变化、关键道具状态、未解决问题和 `ending_state`（末场地点、时间、人物处境）。Showrunner QC 通过时使用其 `approved_memory`，`source=qc_approved`；兼容未启用 QC 的旧流程时使用 `source=rule_extracted` 的保守回退摘要。

Phase S3-6 在每集记忆中增加可选 `continuity_obligations`。每项包含稳定 ID、类型、说明、来源集、到期集和来源记忆路径。旧 `memory_json` 没有该字段时按空数组读取，不需要 SQLite 字段迁移。

Phase S3-6.3 起，后端在 QC 报告 `status=pass` 且集号小于 10 时确定性补全缺失义务：对没有义务来源的 `unresolved_questions.N`，按精确 `source_memory_path` 补一条义务并逐字复用其证据（场号和原文）；已有义务原样保留、同来源不重复、重复调用幂等。第 10 集不生成下一集义务。该行为是纯后端逻辑，不新增 LLM 调用，也不改变 API 请求/响应结构。

人物没有明确当前目标时，`character_updates.current_goal` 保存为 `null`；LLM 偶发返回的空白字符串会在 Schema 边界规范化为 `null`。

生成或重生成第 N 集时，系统会重建第 N 集 memory，并丢弃第 N 集之后的旧 memory，避免后续上下文依赖过期剧本。`ending_hook` 只表示未解决悬念，不能单独证明其中描述的事件已经在场景中发生。

Showrunner 总控状态保存为 `showrunner_json`，包含 `version`、基于稳定排序 JSON 计算的 `source_outline_hash` / `source_characters_hash`、`story_bible`、`episode_plan`、`character_arcs`、`writer_briefs` 与 `qc_reports`。`writer_briefs[N].continuity_contract` 由服务层根据上一集正式记忆生成；`qc_reports[N]` 保存该集最近一次 QC 报告，通过报告还包含 `approved_memory`、`memory_evidence` 和 `continuity_resolutions`。旧 Brief 和旧 QC 报告缺少这些新增字段时按 `null` 或空数组读取。当前不创建 Showrunner 独立数据库表；只有出现多版本、长篇、多用户协作或复杂查询时才考虑迁移。


## Episode

字段：
id
project_id
number
outline
script


## Shot

字段：
id
episode_id
number
scene
camera
action
dialogue
prompt
status
video_path


## GenerationTask

记录AI任务。

字段：
provider
task_id
status
cost
error
