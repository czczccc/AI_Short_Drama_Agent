# 开发任务

## 任务治理与当前指针

本文件是项目任务状态的唯一事实来源。`tasks/plan.md` 负责解释当前里程碑的实施顺序，`tasks/todo.md` 只保留当前单任务或受控批次清单；三者不得分别维护互相冲突的路线。

当前唯一主线：**Interview Text MVP（面试版文字闭环）**。

当前任务指针：**Phase S3-7B：项目 16 完整 10 集连续性验证；当前审查修正 S3-7B-E4-BriefFix-R1**。

## Agent 职责

- **DeepSeek（唯一总体负责人和执行者）**：维护路线、任务包、代码、测试、真实验证、文档、任务状态与 Git 检查点；完成自审后可自行解锁下一任务，不等待 Codex。
- **用户**：只负责确认产品目标、非文字范围扩展、封板标准变化、密钥和破坏性操作等重大决策。
- `tasks/execution_log.md` 保存 execution 与 self-review 证据；正式状态仍只以本文件为准。
- 发现失败时 DeepSeek必须先保护正式数据、记录 Request ID 和根因，再创建最小修复任务；禁止无界 Prompt 试错。
- 当前工作区存在未提交改动。任何执行者不得使用 `git reset --hard`、`git checkout --`、批量覆盖或删除用户已有改动；未经用户要求不得 commit、push 或修改 `.env`。

固定依赖顺序：

`S3-6.3 → S3-7A → S3-7B → S3-7C → S3-7D → S3-8 → S3-9`

执行规则：

- 每次编码前必须指出本文件中的当前 Phase 和具体未完成项。
- 只能处理当前 Phase；后续 Phase 不得提前实现。
- 真实测试发现的问题，只有阻塞当前 Phase 验收时才能加入当前 Phase 子任务；其他问题记入“冻结与后续范围”，不得立即扩展代码。
- DeepSeek可以在文字端既定主线内新增根因/修复原子任务；新增 Phase、改变封板标准或切换到非文字主线必须先获得用户确认。
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

- [x] Phase S3-6.3：后端确定性补全连续性义务
  - [x] S3-6.3-A：第 1–9 集根据 QC 认可的 `unresolved_questions` 补全缺失的下一集义务
  - [x] S3-6.3-B：使用稳定、可重复的义务 ID、来源路径、来源集数和到期集数
  - [x] S3-6.3-C：复用对应未解决问题的场景证据，为后端补全的义务建立 `memory_evidence`
  - [x] S3-6.3-D：保留模型已生成且合法的义务，不重复创建同一来源路径的义务
  - [x] S3-6.3-E：验证第 10 集不生成下一集义务
  - [x] S3-6.3-F：验证不新增 LLM 调用、不使用模糊匹配、不改变正式 API 请求和响应结构
  - [x] S3-6.3-G：运行单元测试、QC 集成测试和全部 pytest，同步 API/工作流/模型文档并关闭 Phase

- [x] Phase S3-7A：项目 16 第 2 集阻塞回归
  - [x] S3-7A-A：只读核对项目 16、当前模型配置、已有第 1 集 Memory/Brief 和测试前数据库状态
  - [x] S3-7A-B：使用 Writer Brief、Showrunner QC 和最多两次返修真实生成第 2 集，只执行一次阻塞回归
  - [x] S3-7A-C：按 Request ID 核对耗时、状态码、关键日志和数据库原子保存结果，形成验收记录

- [ ] Phase S3-7B：项目 16 完整 10 集连续性验证（当前 Phase）
  - [ ] S3-7B-A：连续生成第 3–5 集并完成第一次 Memory/合同检查点（当前检查点）
    - [x] S3-7B-A1：只读建立第 3–5 集基线并验证第 2 集连续性义务
    - [x] S3-7B-A2：生成并审计第 3 集
      - [x] S3-7B-A2-R1：只读分析三轮 draft 的问题迁移、Brief 边界、累计返修反馈和最终 QC 报告
      - [x] S3-7B-A2-R2：实现并测试 Brief Prompt 的最小边界一致性修复
      - [x] S3-7B-A2-R3：第 3 集针对性真实复测 HTTP 200、QC pass 且原子保存
    - [ ] S3-7B-A3：生成并审计第 4 集（首次真实请求 502，证据门禁正确拒绝）
      - [x] S3-7B-A3-R1：确认 QC Prompt 缺少 carried-forward 义务必须写回正式 Memory 的显式契约
      - [x] S3-7B-A3-R2：补充 carried-forward 写回规则、完整字段约束和 Prompt 回归测试
      - [x] S3-7B-A3-R3：第 4 集单次真实复测完成并安全失败（502，无正式数据污染）
      - [x] S3-7B-A3-R4：把 grounding 错误码转换为带具体 ID/路径的明确 QC 重答修正指令
      - [x] S3-7B-A3-R5：用户授权诊断与 Brief 重生成后，第 4 集 HTTP 200、QC pass 且原子保存（执行过程非标准单次复测）
      - [ ] S3-7B-E4-BriefFix-R1：收窄 Brief 一致性规则，保留角色认知、秘密揭示和未来边界限制
    - [ ] S3-7B-A4：生成并审计第 5 集
    - [ ] S3-7B-A5：核对第 1–5 集 Memory、合同与数据库原子性检查点
  - [ ] S3-7B-B：连续生成第 6–8 集并完成第二次 Memory/合同检查点
    - [ ] S3-7B-B1：只读建立第 6–8 集基线并验证第 5 集连续性义务
    - [ ] S3-7B-B2：生成并审计第 6 集
    - [ ] S3-7B-B3：生成并审计第 7 集
    - [ ] S3-7B-B4：生成并审计第 8 集
    - [ ] S3-7B-B5：核对第 1–8 集 Memory、合同和历史数据稳定性
  - [ ] S3-7B-C：连续生成第 9–10 集，验证结局回收且第 10 集不产生下一集义务
    - [ ] S3-7B-C1：只读建立第 9–10 集基线并验证第 8 集连续性义务
    - [ ] S3-7B-C2：生成并审计第 9 集
    - [ ] S3-7B-C3：生成并审计第 10 集
    - [ ] S3-7B-C4：核对第 10 集完成 Episode Plan 结局且不生成第 11 集义务
  - [ ] S3-7B-D：导出可阅读的 10 集剧本、Story Memory、QC 报告和请求日志索引
    - [ ] S3-7B-D1：导出项目 16 的大纲、角色、Showrunner 与 10 集剧本阅读稿
    - [ ] S3-7B-D2：导出逐集 Memory、QC、连续性义务与 Request ID 索引
    - [ ] S3-7B-D3：运行完整季结构审计和全部 pytest，关闭项目 16 验证
  - [ ] 全程不跳集、不手工补写正式 Memory；明确区分 `409`、`502` 和外部服务错误

- [ ] Phase S3-7C：三个题材的最新流程整季复验
  - [ ] S3-7C-P1：锁定三个测试 idea、模型配置、生成参数、输出目录和失败停止规则
  - [ ] S3-7C-A：复仇/逆袭题材最新流程整季复验
    - [ ] S3-7C-A1：创建项目并生成大纲、角色和 Showrunner State
    - [ ] S3-7C-A2：生成第 1–5 集并完成中期连续性检查点
    - [ ] S3-7C-A3：生成第 6–10 集并完成终局检查点
    - [ ] S3-7C-A4：导出完整阅读稿、Memory、QC 和日志索引
  - [ ] S3-7C-B：甜宠/爱情题材最新流程整季复验
    - [ ] S3-7C-B1：创建项目并生成大纲、角色和 Showrunner State
    - [ ] S3-7C-B2：生成第 1–5 集并完成中期连续性检查点
    - [ ] S3-7C-B3：生成第 6–10 集并完成终局检查点
    - [ ] S3-7C-B4：导出完整阅读稿、Memory、QC 和日志索引
  - [ ] S3-7C-C：悬疑/反转题材最新流程整季复验
    - [ ] S3-7C-C1：创建项目并生成大纲、角色和 Showrunner State
    - [ ] S3-7C-C2：生成第 1–5 集并完成中期连续性检查点
    - [ ] S3-7C-C3：生成第 6–10 集并完成终局检查点
    - [ ] S3-7C-C4：导出完整阅读稿、Memory、QC 和日志索引
  - [ ] S3-7C-D：统一整理三个最新项目的大纲、角色、剧本、Memory、QC、连续性矩阵和请求日志
  - [ ] 旧项目 13–15 可作历史基线，但不得代替最新代码和当前模型的验收结果

- [ ] Phase S3-7D：固定评分表封板
  - [ ] S3-7D-A1：冻结 100 分评分表、证据引用格式和致命错误定义
  - [ ] S3-7D-A2：评分复仇/逆袭完整季并记录逐项证据
  - [ ] S3-7D-A3：评分甜宠/爱情完整季并记录逐项证据
  - [ ] S3-7D-A4：评分悬疑/反转完整季并记录逐项证据
  - [ ] S3-7D-B1：汇总平均分、最低分、第 10 集结局完成度与致命错误
  - [ ] S3-7D-B2：未达标时只按失败评分项创建最小修复任务，禁止泛化改 Prompt
  - [ ] S3-7D-C：平均分 80、单项目 75 且无致命错误后封板剧情质量
  - [ ] 固定评分：大纲执行 20、人物一致性 20、跨集连续性 20、冲突节奏 15、钩子 10、台词 10、格式可拍 5

- [ ] Phase S3-8：一句话生成第一集
  - [ ] S3-8-A1：设计并确认一句话编排 API 请求、响应、阶段状态和错误契约
  - [ ] S3-8-A2：定义幂等键、重复请求、阶段失败和安全重试语义
  - [ ] S3-8-A3：补齐正式 `GET /api/v1/projects/{id}/outline` 查询契约
  - [ ] S3-8-B1：新增编排请求/响应 Schema 和阶段结果类型
  - [ ] S3-8-B2：复用现有 Service 实现创意到正式第一集的同步编排服务
  - [ ] S3-8-B3：新增单一正式 API，并保持各阶段现有 API 兼容
  - [ ] S3-8-B4：实现正式大纲查询接口，不增加第二套存储逻辑
  - [ ] S3-8-C1：补充 Fake Provider 成功全流程和响应契约测试
  - [ ] S3-8-C2：补充各阶段失败、幂等重复和正式数据原子性测试
  - [ ] S3-8-C3：补充 Request ID 全链路日志与敏感信息门禁测试
  - [ ] S3-8-D1：运行一次真实模型的一句话生成第一集演示
  - [ ] S3-8-D2：运行全部 pytest，同步 API、架构、数据模型、Prompt 和工作流文档
  - [ ] 输入只包含项目名、故事创意和目标时长；不引入队列、Redis、微服务、用户系统或前端代码

- [ ] Phase S3-9：面试交付封板
  - [ ] S3-9-A1：增加 GitHub Actions，在干净环境安装依赖并运行全部 pytest
  - [ ] S3-9-A2：验证 CI 失败可见性、缓存非必需性和无密钥运行
  - [ ] S3-9-B1：完善 README 五分钟启动、配置说明和常见错误
  - [ ] S3-9-B2：补充三分钟演示脚本、文字端架构图和关键设计取舍
  - [ ] S3-9-C1：准备稳定演示 idea、Fake 成功输出和真实成功输出索引
  - [ ] S3-9-C2：整理三季评分结果、Request ID 日志样例和能力边界
  - [ ] S3-9-D1：生成只读冗余清单，区分使用中、兼容层、开发工具和冻结视频代码
  - [ ] S3-9-D2：只清理已证明未使用且不影响兼容的文字端冗余，并运行回归
  - [ ] S3-9-E1：扫描密钥、`.env`、数据库、日志、评测正文和未跟踪运行时文件
  - [ ] S3-9-E2：从全新克隆完成安装、全部 pytest、Fake 一句话演示和文档校验
  - [ ] S3-9-F1：核对 API.md 与 OpenAPI、TASKS 完成状态和最终 Git diff
  - [ ] S3-9-F2：按逻辑拆分提交并推送，打文字 MVP 面试版标签
  - [ ] S3-9-F3：输出已完成能力、已知限制和后续非文字路线，但不自动启动 Storyboard


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
