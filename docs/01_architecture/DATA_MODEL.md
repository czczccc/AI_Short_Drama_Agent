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
created_at
updated_at

Phase 2C 将项目的角色圣经保存为 `characters_json`，顶层 key 为稳定的 `character_id`。当前不创建 Character 独立数据库表；只有出现跨项目复用、素材版本、多用户协作或复杂单角色查询时才考虑迁移。


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
