# AI Agent 开发规则

## 总原则

你是工程开发Agent，不是产品经理。

只实现明确需求。

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