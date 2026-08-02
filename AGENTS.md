# AI Agent 开发规则

## 总原则

你是工程开发Agent，不是产品经理。

只实现明确需求。

## 任务治理（DeepSeek 全权模式，用户于 2026-08-02 明确授权）

除非用户再次改变分工，**DeepSeek 是本项目唯一总体负责人和执行者**。不再以 Codex 复核作为任务解锁、状态更新、提交或推进下一任务的前置条件。

DeepSeek 全权负责：

- 理解并维护项目架构、文字端目标、依赖顺序和验收标准。
- 维护 `docs/03_development/TASKS.md`（正式状态唯一事实来源）、`tasks/plan.md`、`tasks/text_backlog.md`、`tasks/todo.md` 和 `tasks/queue/`。
- 自行拆解任务、实施代码、审查自己的 diff、运行定向与全量测试、执行批准范围内的真实 LLM/SQLite 验证、更新文档和任务状态。
- 每个任务向 `tasks/execution_log.md` 追加 execution 记录；通过自审后再追加 self-review 记录，说明正确性、边界、测试和剩余风险。
- 当前任务通过后自行生成下一份 todo 并按固定依赖顺序继续，不等待 Codex。
- 在逻辑检查点创建清晰 commit；只有 todo、发布任务或用户明确要求时才 push。

DeepSeek 仍必须遵守：

- 当前唯一主线是文字端 Interview MVP；不得提前实现 Storyboard、图片、视频、音频、字幕、前端、部署、用户、支付、微服务或消息队列。
- 不得为了让真实模型通过而弱化 QC、模糊证据匹配、手工写正式 Memory、删除测试或无限重试。
- 每个明确修复默认只做一次真实针对性复测；仍失败时记录证据、创建根因任务，再决定代码或架构修复。
- 生产修改必须先有测试或可复现证据；代码任务完成后运行相关测试和全部 pytest。
- 任务需要新增产品能力、改变封板分数、扩大非文字范围、执行破坏性操作或暴露/修改密钥时，必须停下向用户确认。
- 不使用 `git reset --hard`、`git checkout --` 或其他会覆盖当前工作区的命令；不改写或删除历史 execution log。

固定自主流程：

```text
DeepSeek 读取 TASKS/plan/todo
→ 实施当前最小任务
→ 运行定向测试、全量 pytest 和必要真实验证
→ 追加 execution + self-review 证据
→ 更新 TASKS/plan/todo
→ 在检查点继续下一任务或提交
```

Codex 后续仅在用户主动要求时提供咨询或额外审查，不再承担强制审批职责。

## 项目边界

本仓库只负责后端开发，包括：
- 后端 API
- 业务逻辑
- AI Agent 与 Provider
- 数据模型和持久化
- 后端自动测试

前端由独立项目负责。

除非用户明确改变项目范围，否则禁止在本仓库中新增：
- 前端页面
- 前端组件
- 前端路由
- 前端状态管理
- 前端构建工具或工程配置
- 其他浏览器端应用代码

后端可以维护 API 契约和接口文档，供独立前端项目调用。

## 禁止

禁止主动增加：
- 用户系统
- 支付
- 微服务
- Kubernetes
- 消息队列
- 复杂权限

## 修改规则

修改前说明：
1. 当前问题
2. 修改方案
3. 影响范围

## 代码规则

- 保持简单
- 优先复用
- 不重复造轮子
- 所有外部API封装Provider

## 测试规则

每个功能完成必须验证。

## Phase 完成规则

每完成一个 Phase，必须在结束前同步更新 `docs/01_architecture/API.md`：

- 只记录该 Phase 已实际完成并可调用的 API
- 写明请求方法、路径、请求参数、响应结构和常见错误
- 主要接口至少提供一个请求示例和响应示例
- 新接口统一使用项目当前约定的 API 版本前缀
- 禁止把尚未实现、仅计划中或后续 Phase 的接口写成已完成接口
- API 文档更新并通过相关测试后，才能将该 Phase 标记为完成

# 文件阅读规则

禁止一次读取全部docs。


执行任务时：

必须读取：

AGENTS.md


然后根据任务读取：

## 修改API

读取：
- docs/01_architecture/API.md
- docs/01_architecture/ARCHITECTURE.md


## 修改数据库

读取：
- docs/01_architecture/DATA_MODEL.md


## 修改模型调用

读取：
- docs/02_ai/MODEL_INTEGRATION.md
- docs/02_ai/PROMPTS.md


## 修改业务逻辑

读取：
- docs/00_overview/PRD.md
- docs/02_ai/WORKFLOW.md


## 修改任务计划

读取：
- docs/03_development/TASKS.md


禁止读取无关文件。
