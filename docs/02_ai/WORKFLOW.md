# 工作流设计

## 剧本流程

创意输入

↓

Director Agent

↓

Story Bible

↓

Character Agent

↓

Character Bible

↓

Writer Agent

↓

Episode Script

Phase 2B 每次只处理一个指定 `episode_number`：从 Project 的 `outline_json` 读取整体大纲和对应分集，Writer Agent 生成结构化剧本，经 Pydantic 校验后按集号合并保存到 `scripts_json`。同集重新生成会覆盖旧值，不影响其他集。

Phase 2C 的 Character Agent 一次读取完整故事大纲并生成全部主要角色圣经，经 Pydantic 和大纲上下文校验后，以 `character_id` 为 key 保存到 `Project.characters_json`。用户可以查询或整体替换角色圣经。Writer 生成新剧本时优先读取角色圣经；旧项目没有角色圣经时继续使用 `StoryOutline.characters`。

Phase 2D-1 增加 Story Memory v1：每集剧本生成并校验成功后，系统从 `EpisodeScript` 中提取本集摘要、新增场景事实、出场角色状态和结尾钩子，保存到 `Project.memory_json`。角色状态按该角色实际出场场景提取：`knows` 保存该角色参与场景的 scene goal，`current_goal` 保存该角色最后一次出场场景目标。之后生成后续集时，Writer 会收到此前已保存的 `story_memory`，用于承接前文。重生成第 N 集时会覆盖第 N 集 memory，并删除第 N 集之后的旧 memory，避免后续上下文基于过期剧本。

LLM QC v1 是剧本生成后的人工确认辅助步骤：对已保存的第 N 集剧本读取 Story Outline、Character Bible、Story Memory 和当前剧本，调用 QC Agent 生成结构化质检报告。v1 只返回问题清单、严重级别和修改建议，不自动改写剧本、不覆盖已保存剧本。确认 QC 报告后，再由人工决定是否重生成或手动编辑剧本。

↓

Storyboard Agent

↓

Shot List


## 视频流程

Shot

↓

Prompt Adapter

↓

Video Provider

↓

任务轮询

↓

素材保存

↓

FFmpeg合成
