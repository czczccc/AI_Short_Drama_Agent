# 开发任务

## 任务治理与当前指针

本文件是项目任务状态的唯一事实来源。`tasks/plan.md` 负责解释当前里程碑的实施顺序，`tasks/todo.md` 只保留当前可执行检查项；三者不得分别维护互相冲突的路线。

当前唯一主线：**Interview Text MVP（面试版文字闭环）**。

当前任务指针：**Phase S3-6.3：后端确定性补全连续性义务**。

## Agent 协作职责

- **总体负责人（Codex）**：维护路线、任务边界、依赖顺序和验收标准；复核代码与测试证据；只有复核通过后才更新本文件、解锁下一任务或安排提交推送。
- **代码执行者（DeepSeek）**：一次只执行 `tasks/todo.md` 中唯一的原子任务；只能修改任务包允许的文件；完成或阻塞后必须向 `tasks/execution_log.md` 追加执行记录；不得自行扩 Phase、调整产品目标、勾选本文件或提前实现后续任务。
- **用户**：确认路线或范围变更；可以把 `tasks/todo.md` 直接交给 DeepSeek 执行，再把执行结果交回 Codex 验收。
- DeepSeek 报告“完成”不等于任务完成；必须由 Codex 核对 diff、测试命令和实际输出后，本文件中的 `[ ]` 才能改为 `[x]`。
- `tasks/execution_log.md` 只保存执行和复核证据，不是任务状态来源；历史记录只能追加，不得覆盖、改写或删除。
- 当前工作区存在未提交改动。任何执行者不得使用 `git reset --hard`、`git checkout --`、批量覆盖或删除用户已有改动；未经用户要求不得 commit、push 或修改 `.env`。

固定依赖顺序：

`S3-6.3 → S3-7A → S3-7B → S3-7C → S3-7D → S3-8 → S3-9`

执行规则：

- 每次编码前必须指出本文件中的当前 Phase 和具体未完成项。
- 只能处理当前 Phase；后续 Phase 不得提前实现。
- 真实测试发现的问题，只有阻塞当前 Phase 验收时才能加入当前 Phase 子任务；其他问题记入“冻结与后续范围”，不得立即扩展代码。
- 新增 Phase、改变验收标准或切换主线必须先获得用户确认，再修改本文件。
- 每个代码 Phase 必须先补失败测试，完成后运行相关测试和全部 pytest，并同步实际 API 文档。
- 每个修复默认只进行一次针对性真实 LLM 复测；仍失败时先记录证据并决定是否调整当前任务，不连续靠 Prompt 试错。
- 临时模型切换、排查日志和人工评测不是新 Phase，不得改变任务指针。
- S3-9 完成前冻结 Storyboard、视频、FFmpeg、前端、部署、用户系统、支付和其他产品扩展。

Interview Text MVP 封板条件：

- 一句话可以通过单一后端入口生成第一集的大纲、角色圣经、Showrunner State、Writer Brief、正式剧本、QC 报告和 Story Memory。
- 最新代码完成三个题材的 10 集整季验收；平均分不低于 80，任一项目不低于 75，且没有致命人物、事实或跨集连续性错误。
- 全部 pytest 与 GitHub Actions 通过，仓库无密钥，README 可以指导面试官在五分钟内启动并理解演示流程。
- S3-9 完成后文字 MVP 封板；除非验收发现致命回归，不再新增文字 Agent 或 QC Phase。

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


## Phase 3 视频（冻结：S3-9 完成后恢复）

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
- [x] Phase S3-6A：Story Memory 场景证据门禁
  - [x] `approved_memory` 每条可持久化事实必须映射到场景原文
  - [x] 后端校验证据场号、原文片段、路径覆盖和末场地点时间
  - [x] 证据校验失败时 QC Agent 最多语义重答一次，仍失败则不保存
- [x] Phase S3-6B：跨集连续性合同
  - [x] Story Memory 保存下一集到期的 `continuity_obligations`
  - [x] Writer Brief 自动注入服务器生成的 `continuity_contract`
  - [x] 上一集末场必须在下一集第一场承接
  - [x] QC 通过前必须逐条输出 `continuity_resolutions` 和场景证据
- [x] Phase S3-6.1：QC 跨集合同输出稳定性修复
  - [x] QC Prompt 增加非空 `continuity_resolutions` 完整示例
  - [x] 明确关系变更数组和连续性义务类型的字段约束
  - [x] Schema 边界有限兼容真实模型已观察到的状态与证据别名
  - [x] 保持缺失场号、冲突别名、未知字段和错误嵌套类型严格失败
- [x] Phase S3-6.2：QC 场景证据清单
  - [x] 从 draft 的动作、对白、动作提示和转场生成可引用证据清单
  - [x] QCAgent 将证据清单加入每次初始与上下文重答输入
  - [x] QCAgent 提供最后一场地点和时间的权威引用
  - [x] Prompt 要求记忆证据和合同处理结果完整复制清单原文
  - [x] 清理无对应路径的辅助证据和完全相同的重复证据
  - [x] 保持后端逐字校验，不增加模糊匹配或自动事实补写

- [ ] Phase S3-6.3：后端确定性补全连续性义务（当前任务）
  - [x] S3-6.3-A：第 1–9 集根据 QC 认可的 `unresolved_questions` 补全缺失的下一集义务
  - [x] S3-6.3-B：使用稳定、可重复的义务 ID、来源路径、来源集数和到期集数
  - [x] S3-6.3-C：复用对应未解决问题的场景证据，为后端补全的义务建立 `memory_evidence`
  - [ ] S3-6.3-D：保留模型已生成且合法的义务，不重复创建同一来源路径的义务（当前原子任务）
  - [ ] S3-6.3-E：验证第 10 集不生成下一集义务
  - [ ] S3-6.3-F：验证不新增 LLM 调用、不使用模糊匹配、不改变正式 API 请求和响应结构
  - [ ] S3-6.3-G：运行单元测试、QC 集成测试和全部 pytest，同步 API/工作流/模型文档并关闭 Phase

- [ ] Phase S3-7A：项目 16 第 2 集阻塞回归
  - [ ] S3-7A-A：只读核对项目 16、当前模型配置、已有第 1 集 Memory/Brief 和测试前数据库状态
  - [ ] S3-7A-B：使用 Writer Brief、Showrunner QC 和最多两次返修真实生成第 2 集，只执行一次阻塞回归
  - [ ] S3-7A-C：按 Request ID 核对耗时、状态码、关键日志和数据库原子保存结果，形成验收记录

- [ ] Phase S3-7B：项目 16 完整 10 集连续性验证
  - [ ] S3-7B-A：连续生成第 3–5 集并完成第一次 Memory/合同检查点
  - [ ] S3-7B-B：连续生成第 6–8 集并完成第二次 Memory/合同检查点
  - [ ] S3-7B-C：连续生成第 9–10 集，验证结局回收且第 10 集不产生下一集义务
  - [ ] S3-7B-D：导出可阅读的 10 集剧本、Story Memory、QC 报告和请求日志索引
  - [ ] 全程不跳集、不手工补写正式 Memory；明确区分 `409`、`502` 和外部服务错误

- [ ] Phase S3-7C：三个题材的最新流程整季复验
  - [ ] S3-7C-A：复仇/逆袭题材生成或重验 10 集
  - [ ] S3-7C-B：甜宠/爱情题材生成或重验 10 集
  - [ ] S3-7C-C：悬疑/反转题材生成或重验 10 集
  - [ ] S3-7C-D：统一整理三项目的大纲、角色圣经、剧本、最终 Memory、QC 和请求日志
  - [ ] 旧项目 13–15 可作历史基线，但不得代替最新代码和当前模型的验收结果

- [ ] Phase S3-7D：固定评分表封板
  - [ ] S3-7D-A：按固定 100 分表分别评分三个完整项目并记录逐项证据
  - [ ] S3-7D-B：汇总平均分、最低分和致命错误检查，第 10 集必须完成大纲结局
  - [ ] S3-7D-C：达到平均分 80、单项目 75 且无致命错误后封板；未达标只创建对应评分项的修复任务
  - [ ] 固定评分：大纲执行 20、人物一致性 20、跨集连续性 20、冲突节奏 15、钩子 10、台词 10、格式可拍 5

- [ ] Phase S3-8：一句话生成第一集
  - [ ] S3-8-A：先设计并确认单一后端编排接口契约、失败阶段和幂等/重试语义
  - [ ] S3-8-B：复用现有 Service 实现一句话到正式第一集的同步编排，不复制 Agent 业务逻辑
  - [ ] S3-8-C：补充 API、Fake Provider 全流程和失败原子性测试
  - [ ] S3-8-D：运行一次真实模型演示、全部 pytest，并同步 API/架构/工作流文档
  - [ ] 输入只包含项目名、故事创意和目标时长；不引入队列、Redis、微服务、用户系统或前端代码

- [ ] Phase S3-9：面试交付封板
  - [ ] S3-9-A：增加 GitHub Actions，在干净环境自动运行全部 pytest
  - [ ] S3-9-B：完善 README 的五分钟启动、三分钟演示、架构图、设计取舍和能力边界
  - [ ] S3-9-C：准备稳定演示输入、完整成功输出、评分结果和 Request ID 日志样例
  - [ ] S3-9-D：执行面试封板瘦身审查，只清理已确认未使用内容并说明视频/旧 API/开发工具状态
  - [ ] S3-9-E：检查密钥、`.env`、运行时数据库和未提交改动；从全新克隆完成安装、pytest 和 Fake 演示
  - [ ] S3-9-F：按逻辑拆分提交并推送，文字 MVP 封板后再把任务指针更新为 Phase 3-2 Storyboard


## Phase 4 后处理（冻结：S3-9 完成后评估）

- [ ] FFmpeg
- [ ] 字幕
- [ ] 音频


## 冻结与后续范围

- [ ] Phase 3-2 Storyboard 文本结构：S3-9 完成后恢复
- [ ] Phase 3-3～3-5 视频任务与真实供应商：Storyboard 验收后恢复
- [ ] Phase 4 FFmpeg、字幕和音频：视频任务闭环后恢复
- [ ] 整季一键生成：第一集编排和长耗时策略验证后再立项
- [ ] 前端、部署、用户系统和商业能力：不属于当前后端面试 MVP
