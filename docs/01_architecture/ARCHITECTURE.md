# 系统架构

## 总体流程

用户
↓
API Layer
↓
Workflow Engine
↓
Agents

Agents:
- Director Agent
- Writer Agent
- Character Agent
- Storyboard Agent
- Video Agent
- QC Agent

↓

Render Service

↓

最终视频


## 状态机

draft

outline_ready

characters_ready

script_ready

storyboard_ready

generating

rendering

completed

failed
