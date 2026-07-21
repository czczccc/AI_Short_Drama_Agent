# 数据模型

## Project

项目基本信息。

字段：
id
name
description
status
created_at


## Character

角色信息。

字段：
id
project_id
name
appearance
personality
reference_images


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
