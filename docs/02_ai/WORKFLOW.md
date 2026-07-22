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
