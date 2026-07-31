# 开发任务

## Phase 1 基础

- [x] 初始化项目
- [x] FastAPI
- [x] 数据库
- [x] 配置系统


## Phase 2 AI文本

- [x] 通用 LLM Provider 接口
- [x] DeepSeek Provider
- [x] Director Agent
- [x] 结构化故事设定与 10 集大纲
- [x] 大纲 Pydantic 校验、Project 持久化与 `outline_ready` 状态
- [x] Writer Agent
- [x] 单集结构化剧本生成与 Pydantic 校验
- [x] `scripts_json` 按集保存、覆盖与查询 API
- [x] Character Agent
- [x] 项目级角色圣经生成、校验与 `characters_json` 持久化
- [x] 角色圣经查询、整体替换 API 与 Writer 优先读取
- [x] Writer Prompt v2：限制单集剧本严格展开当前集大纲范围
- [x] Writer 生成时携带上一集、当前集和下一集边界上下文
- [x] Story Memory v1：从已保存剧本提取前文事实、出场角色和结尾钩子
- [x] Story Memory 持久化到 `Project.memory_json`
- [x] 重生成第 N 集时更新第 N 集 memory，并清理后续过期 memory
- [x] LLM QC v1：对已保存单集剧本生成结构化质检报告
- [x] LLM QC v1 只返回报告，不自动改写、不覆盖剧本


## 开发验证工具

- [x] 本地开发测试页 `/dev/testbench`
- [x] 测试页可创建项目、生成大纲、生成角色圣经、生成单集剧本
- [x] 测试页可加载历史项目并查看已保存多集剧本
- [x] 测试页可查看大纲 JSON、角色 JSON、剧本 JSON 和 Story Memory JSON
- [x] 测试页可对当前集触发 LLM QC v1 并查看 QC Report JSON
- [x] 测试页可删除本地历史项目
- [x] 本地结构化 JSONL 日志 `logs/app.jsonl`
- [x] HTTP `X-Request-ID` 请求关联
- [x] 开发辅助日志查询接口 `/dev/logs`


## Phase 3 视频

- [x] Phase 3-1：Video Provider 抽象接口
  - [x] 定义 `submit()`、`get_status()`、`download()`、`cancel()` 统一接口
  - [x] 定义视频任务状态枚举：`pending`、`running`、`succeeded`、`failed`、`canceled`
  - [x] 定义视频提交输入和任务结果 Schema
  - [x] 增加 Fake Video Provider，用于无真实视频 API 的自动测试
  - [x] 增加 Provider factory 配置入口，但默认不调用真实供应商
- [ ] Phase 3-2：Shot / Storyboard 文本结构
  - [ ] 定义单集 Storyboard / Shot List Schema
  - [ ] Storyboard Agent 根据已保存剧本生成镜头清单
  - [ ] Storyboard 输出保存到项目持久化字段
  - [ ] 增加生成和查询 Storyboard API
- [ ] Phase 3-3：视频任务提交
  - [ ] 将 Shot List 中的单个镜头提交给 Video Provider
  - [ ] 保存供应商任务 ID、镜头状态和错误信息
  - [ ] 增加提交单镜头视频任务 API
- [ ] Phase 3-4：任务轮询
  - [ ] 查询单镜头视频任务状态
  - [ ] 成功后保存远程视频 URL 或本地文件引用
  - [ ] 失败时保存安全错误，不暴露供应商原始异常
- [ ] Phase 3-5：接入第一个真实视频模型
  - [ ] 选择第一个供应商
  - [ ] 在 Provider 封装供应商认证、请求、状态映射和错误清洗
  - [ ] 使用同一业务接口替换 Fake Provider 进行集成验证


## Showrunner

- [x] Phase S3-1：Showrunner State MVP
  - [x] `Project.showrunner_json` 持久化字段与 SQLite 幂等迁移
  - [x] Story Bible、Episode Plan、Character Arc Schema
  - [x] Showrunner Agent 根据大纲和角色圣经生成整季总控状态
  - [x] 生成和查询 Showrunner State API
  - [x] 基于稳定排序 JSON 内容计算 SHA-256 来源哈希
- [x] Phase S3-2：Writer Brief MVP
  - [x] Writer Brief Schema
  - [x] Showrunner Agent 为指定集生成 Writer Brief
  - [x] Writer Brief 保存到 `showrunner_json.writer_briefs`
  - [x] 生成和查询 Writer Brief API
  - [x] 重新生成某集 Brief 只覆盖该集，不影响其他集
- [x] Phase S3-3：Writer 接入 Writer Brief
  - [x] Writer 生成请求可选择使用已保存 Brief
  - [x] Writer Prompt 接收 Brief 并优先遵守本集边界
  - [x] 默认不使用 Brief，保持旧剧本生成流程兼容
- [x] Phase S3-4：Showrunner QC
  - [x] 对 Writer draft 按 Brief、Story Bible、Episode Plan、Character Arc 和 Story Memory 审核
  - [x] QC 通过后再保存正式剧本并更新正式 Story Memory
  - [x] QC 不通过时不写入正式 Story Memory
  - [x] QC 报告保存到 `showrunner_json.qc_reports`
  - [x] 查询已保存 Showrunner QC 报告 API
- [x] Phase S3-5：QC v2 与 Story Memory v2
  - [x] 规则型 QC 检查场景密度和场景角色一致性
  - [x] LLM QC 检查钩子落地、末场承接、人物认知和道具状态
  - [x] QC 通过时输出并保存 `approved_memory`
  - [x] Story Memory 记录事实来源、道具状态和末场状态
  - [x] 剧本生成支持最多两次显式自动返修
  - [x] 多轮返修累积历史 QC 问题，避免修新问题时回归旧错误
  - [x] 评测 Runner 默认开启 Showrunner QC 并整理最终 QC 报告


## Phase 4 后处理

- [ ] FFmpeg
- [ ] 字幕
- [ ] 音频


## Phase 5 完整测试

- [ ] 一键生成第一集
