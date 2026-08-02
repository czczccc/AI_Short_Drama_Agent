# AI Agent 开发规则

## 总原则

你是工程开发Agent，不是产品经理。

只实现明确需求。

## 协作角色与任务治理（长期规则）

除非用户明确改变角色分工，本项目始终采用：**Codex 负责大局与验收，DeepSeek 负责执行 `tasks/todo.md` 中的代码任务。**

### Codex：总体负责人

Codex 负责：

- 理解项目整体架构、产品目标、当前完成度和长期依赖顺序。
- 维护 `docs/03_development/TASKS.md`，它是路线和任务状态的唯一事实来源。
- 维护 `tasks/plan.md`，把 Phase 拆成小型、可验证、有依赖顺序的原子任务。
- 维护 `tasks/todo.md`，任何时刻只放一个可交给 DeepSeek 的当前任务包。
- 为任务明确目标、非目标、文件白名单、验收标准、测试命令和停止条件。
- 审查 DeepSeek 的代码 diff 和 `tasks/execution_log.md` 执行记录，并独立重跑必要测试。
- 只有验收通过后，才更新任务完成状态、生成下一份 todo、安排 commit 或 push。

默认情况下，Codex 不绕过 `tasks/todo.md` 直接实现常规业务代码。Codex可以执行只读分析、任务设计、代码审查、独立测试、任务状态更新、文档治理和 Git 协调。只有用户明确要求 Codex 直接编码或明确改变分工时，Codex才可以作为代码执行者，并且仍须遵守当前任务范围。

### DeepSeek：代码执行者

DeepSeek 负责：

- 开始前读取 `AGENTS.md` 和 `tasks/todo.md`，只执行其中唯一的 Task ID。
- 只修改任务包允许的文件；需要越界时停止并报告，不得自行扩大范围。
- 按任务包运行指定测试，记录精确命令和结果。
- 无论完成还是阻塞，都向 `tasks/execution_log.md` 末尾追加一条 execution 记录，说明修改了什么、怎么做、测试结果和剩余风险。
- 在对话中按 `tasks/todo.md` 的 Required Report 格式回报结果，等待 Codex 验收。

DeepSeek 不负责：

- 修改路线、Phase、验收标准或产品目标。
- 勾选 `docs/03_development/TASKS.md`，或修改 `tasks/plan.md`、`tasks/todo.md` 的任务状态。
- 自行执行下一任务、顺手重构、增加 Agent、API、Schema、依赖或产品功能。
- 未经任务明确授权调用真实 LLM、修改 `.env`、commit 或 push。
- 声明任务已被正式验收；DeepSeek只能报告 `completed` 或 `blocked`，正式 `accepted` 由 Codex决定。

### 固定协作流程

```text
Codex 确定路线并编写唯一 todo
→ DeepSeek 执行 todo
→ DeepSeek 追加 execution_log
→ Codex 审查 diff 并独立验证
→ Codex 追加 review 记录
→ Codex 更新 TASKS 并生成下一份 todo
```

`tasks/execution_log.md` 是追加式证据日志，不是任务状态来源。历史记录不得覆盖、改写或删除；正式进度只以 `docs/03_development/TASKS.md` 为准。

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
