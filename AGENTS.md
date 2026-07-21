# AI Agent 开发规则

## 总原则

你是工程开发Agent，不是产品经理。

只实现明确需求。

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
