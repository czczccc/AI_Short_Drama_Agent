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

## 剧本文字门禁

Showrunner State
↓
Writer Brief
↓
Writer Draft
↓
规则型 QC（场景密度、场景角色等确定性约束）
↓
LLM Showrunner QC（分集边界、钩子落地、人物认知、时间地点、道具状态）
↓
未通过：可按请求配置把 QC 问题反馈给 Writer，最多返修两次
↓
通过：保存正式剧本，并把 QC 的 `approved_memory` 写入 Story Memory v2

评测 Runner 是调用和记录工具，不承担内容判断；它在质量模式下显式开启 Showrunner QC，并保存最终 QC 报告。


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
