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
服务层注入上一集正式记忆生成的 Continuity Contract
↓
Writer Draft
↓
规则型 QC（场景密度、场景角色等确定性约束）
↓
LLM Showrunner QC（分集边界、钩子落地、人物认知、时间地点、道具状态）
↓
确定性证据门禁（Memory Evidence 路径覆盖、场景原文、末场状态、连续性逐条处理）
↓
未通过：可按请求配置把 QC 问题反馈给 Writer，最多返修两次
↓
通过：保存正式剧本，并把 QC 的 `approved_memory` 写入 Story Memory v2

评测 Runner 是调用和记录工具，不承担内容判断；它在质量模式下显式开启 Showrunner QC，并保存最终 QC 报告。

`continuity_contract` 不由 LLM 自由决定。服务层只根据上一集 `source=qc_approved` 的正式 Story Memory 构建：上一集 `ending_state` 固定形成一个第一场承接事项，上一集到期的 `continuity_obligations` 形成其余必处理事项。QC 报告只有逐条给出 `continuity_resolutions`，且证据原文能在指定场景动作、对白或转场中找到，才可能通过。仅有 `source=rule_extracted` 的兼容记忆不会生成强制合同。


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
