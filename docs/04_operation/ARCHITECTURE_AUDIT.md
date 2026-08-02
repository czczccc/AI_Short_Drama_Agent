# 架构审计报告（Interview 交付视角）

> 审计日期：2026-08-02
> 审计目标：将本仓库作为完整面试项目交付。不追求企业级复杂度，追求：架构清晰、功能完整、可以演示、可以解释每个模块存在的意义。
> 审计方式：只读分析，未修改任何代码。

---

## 1. 当前项目目录树

```
AI_Short_Drama_Agent/
├── app/                          # 核心后端
│   ├── api/                      # FastAPI 路由层（薄封装）
│   │   ├── main.py               # 应用入口：挂载 5 业务 router + dev router + 异常映射
│   │   ├── projects.py           # 项目创建/查询
│   │   ├── outlines.py           # 大纲生成/查询
│   │   ├── characters.py         # 角色圣经生成/查询/替换
│   │   ├── showrunner.py         # Showrunner State / Writer Brief / QC 报告
│   │   ├── scripts.py            # 单集剧本生成/查询（核心）
│   │   └── dev.py                # 调试台（testbench/日志/单集QC）[周边]
│   ├── agents/                   # LLM Agent 层（每 agent 一个系统提示）
│   │   ├── director.py           # 创意 → 大纲
│   │   ├── character.py          # 大纲 → 角色圣经
│   │   ├── showrunner.py         # 总控 State + Writer Brief
│   │   ├── writer.py             # Brief+记忆 → 单集剧本（含上下文校验重试）
│   │   └── qc.py                 # 剧本 → QC 报告（含 grounding 校验+修正指令重试）
│   ├── services/                 # 业务编排层
│   │   ├── project_service.py    # Project CRUD
│   │   ├── outline_service.py    # 大纲编排
│   │   ├── character_service.py  # 角色圣经编排
│   │   ├── showrunner_service.py # State/Brief 编排 + continuity_contract 构造
│   │   ├── script_service.py     # 剧本生成主循环（Writer→QC→返修→落库）★核心
│   │   ├── qc_grounding.py       # 确定性证据校验（439行，纯函数）★项目亮点
│   │   ├── continuity_qc.py      # 规则型 QC（确定性约束）
│   │   ├── memory_service.py     # Story Memory 存取/构建
│   │   └── qc_service.py         # 独立单集 QC [周边，仅 dev 用]
│   ├── providers/
│   │   ├── llm/                  # LLM 抽象：base Protocol + DeepSeek + factory ★必需
│   │   └── video/                # 视频占位（fake provider）[周边/未接线]
│   ├── schemas/                  # Pydantic 契约（LLM 输出 JSON 校验）★必需
│   ├── models/                   # 唯一 ORM：Project（5 个 JSON 列）
│   ├── database/                 # SQLite 引擎/会话/幂等迁移
│   ├── configs/                  # pydantic-settings 读 .env
│   ├── observability/            # JSONL 结构化日志（request_id 链路）
│   └── prompts/                  # writer_v2/qc_v1/character_v1/director_v1.md
│                                 # showrunner/v1.py + brief_v1.py（内嵌）
├── tools/
│   └── text_eval_runner.py       # 端到端评测驱动器（TestClient 走全链路）[周边]
├── tests/                        # ~33 个测试文件，覆盖全链路
├── docs/                         # PRD/架构/API/数据模型/工作流/任务（治理完善）
├── tasks/                        # 任务治理：plan/todo/queue/execution_log
├── data/app.db                   # SQLite 生产数据 + 3 个 .bak 备份
├── eval_outputs/                 # 历史评测产物（~15MB，含剧本全文/日志）
├── logs/app.jsonl                # 运行日志（2.4MB）
├── requirements.txt / .env.example / AGENTS.md
└── [排除] .venv/ .pytest_cache/ .git/
```

**规模**：`app/` 约 40 个 Python 文件、~4600 行；测试约 33 个文件、190+ 用例全绿。

---

## 2. 完整调用链（创意 → 剧本）

```
用户输入一句创意
↓
POST /api/v1/projects/{id}/outline
│   api/outlines.py:27 → services/outline_service.py:33
└→ DirectorAgent.generate_outline [agents/director.py:15]
      → LLM(director_v1.md → StoryOutline) → 存 outline_json  [status=outline_ready]
↓
POST /api/v1/projects/{id}/characters/generate
│   api/characters.py:60 → services/character_service.py:72
└→ CharacterAgent.generate_character_bibles [agents/character.py:22]
      → LLM(character_v1.md → CharacterBibleCollection) → 存 characters_json  [status=characters_ready]
↓
POST /api/v1/projects/{id}/showrunner
│   api/showrunner.py:82 → services/showrunner_service.py:95
└→ ShowrunnerAgent.generate_showrunner_state [agents/showrunner.py:17]
      → LLM(showrunner/v1.py → ShowrunnerState：story bible + 10集plan + 角色弧) → 存 showrunner_json
↓
POST /api/v1/projects/{id}/episodes/{n}/writer-brief
│   api/showrunner.py:128 → services/showrunner_service.py:213
└→ ShowrunnerAgent.generate_writer_brief [agents/showrunner.py:80]
      → LLM(showrunner/brief_v1.py → WriterBrief)
      → 服务层 build_continuity_contract 覆盖 continuity_contract（非 LLM 自由决定）★设计亮点
↓
POST /api/v1/projects/{id}/episodes/{n}/script      ◀── 核心
│   api/scripts.py:75 → services/script_service.py:80  generate_script()
├→ 循环（≤ max_revision_attempts）：
│   ├→ WriterAgent.generate_script [agents/writer.py:65]
│   │     → LLM(writer_v2.md → EpisodeScript) + 上下文校验（集号/时长/角色ID）失败带issues重试
│   ├→ 规则型 QC [services/continuity_qc.py:9]（确定性约束：场景密度/角色在场）
│   ├→ QCAgent.generate_report [agents/qc.py:73]
│   │     → LLM(qc_v1.md → QCReport)
│   │     → grounding 证据门禁 [services/qc_grounding.py:424]
│   │       （evidence catalog / 补义务 / 归一化 / 逐字对证，失败带修正指令重试）
│   ├→ merge_qc_report + save_showrunner_qc_report
│   ├→ pass? 否 → revision_feedback → Writer 重写；超限 → 409
│   └→ pass? 是 → 跳出
└→ 原子落库：scripts_json[集号] + upsert_episode_memory → memory_json  [status=script_ready]

Provider 层（所有 Agent 仅依赖此接口）：
  LLMProvider.generate_structured(system, user, schema)  [providers/llm/base.py:9]
  └→ DeepSeekProvider.generate_structured [deepseek_provider.py:46]
      （OpenAI兼容 / json_object / 解析失败repair重试×2 / 异常分类→502/503）

数据库：单表 projects（outline/characters/scripts/memory/showrunner 五个 JSON TEXT 列）SQLite
```

---

## 3. 核心模块清单

| 模块 | 作用 | 被谁调用 | MVP 必需 |
|---|---|---|---|
| `api/main.py` | 应用入口、路由挂载、异常→HTTP 映射 | uvicorn / 测试 / eval_runner | ✅ |
| `api/scripts.py` + `script_service.py` | **剧本生成主循环**（Writer→QC→返修→落库） | 用户核心请求 | ✅ |
| `api/showrunner.py` + `showrunner_service.py` | State/Brief 编排 + continuity_contract 构造 | 剧本前置 | ✅ |
| `agents/writer.py` | 单集剧本生成 + 上下文校验 | script_service | ✅ |
| `agents/qc.py` | QC 报告生成 + grounding 校验重试 | script_service | ✅ |
| `agents/director.py` / `character.py` / `showrunner.py` | 大纲/角色/总控三个上游生成 | 对应 service | ✅ |
| `services/qc_grounding.py` | 确定性证据门禁（**项目差异化亮点**） | agents/qc | ✅ |
| `services/continuity_qc.py` | 规则型 QC（纯代码确定性约束） | script_service | ✅ |
| `services/memory_service.py` | Story Memory 存取/构建 | script_service 等 | ✅ |
| `providers/llm/*` | LLM 抽象 + DeepSeek 实现 + 工厂 | 所有 agent | ✅ |
| `schemas/*`（除 video） | Pydantic 契约，LLM 输出强校验 | agents/services/api | ✅ |
| `models/` `database/` `configs/` | 数据层 + 配置 | 全部 service | ✅ |
| `observability/` | JSONL 链路日志（演示时可追踪） | 全局 | ✅（演示卖点） |
| `prompts/*` | 各 Agent 系统提示 | 对应 agent | ✅ |
| `api/projects/outlines/characters` | 前置四步路由 | 用户 | ✅ |
| `api/dev.py` + `qc_service.py` | 调试台、独立单集 QC | 仅开发调试 | ⚠️ 演示可省 |
| `providers/video/*` + `schemas/video.py` | 视频占位（fake） | **无任何业务调用** | ❌ 未接线 |
| `tools/text_eval_runner.py` | 端到端评测驱动器 | 离线 CLI | ❌ 工具 |
| `eval_outputs/` `data/*.bak` `logs/` | 产物/备份/日志 | — | ❌ 非代码 |

---

## 4. 模块标签

### 🟢 A — 必须保留（架构骨架，全部在文本主链路上）

`api/` 六个业务路由、`services/` 全部（除 qc_service）、`agents/` 全部、`providers/llm/`、`schemas/`（除 video）、`models/`、`database/`、`configs/`、`observability/`、`prompts/`（除 writer_v1）、`tests/`

### 🟡 B — 保留但简化

- **`api/dev.py` + `services/qc_service.py`**：调试功能对面试演示"可追踪性"有加分，但可裁掉 testbench HTML 等花活，只留一个日志查看端点
- **`agents/showrunner.py` 的 Showrunner State**：当前是"story bible + 10 集 plan + 角色弧"三个 LLM 产物合一。面试场景可解释为"总控规划层"，保留；若想减负可只保留 brief 路径（见下）
- **`showrunner_service.generate_showrunner_state`**：同上，与 brief 相比它是"可选前置"。**注意**：`run_showrunner_qc` 模式强制要求 brief，State 本身非强制——可把 State 降为"演示时可跳过"的增强项

### 🟠 C — 暂时冻结（保留代码，不进演示主线，面试时一句话带过）

- **`providers/video/` 全部 + `schemas/video.py`**：PRD 写了视频是 MVP，但当前是"提交任务即 succeeded"的 fake 占位、零调用者。冻结，面试时定位为"为 Phase 2 视频生成的预留 Provider 接口"
- **`tools/text_eval_runner.py`**：好工具但非产品功能，冻结为"开发期评测工具"
- **`api/dev.py` 若不想精简**：整组冻结也可接受

### 🔴 D — 删除候选

- **`app/prompts/writer_v1.md`**：grep 确认**无任何代码引用**（agent 全部用 writer_v2），纯遗留死文件 → 删除
- **`data/app.before-memory-rebuild.*.db`、`data/app.db.phase2b/2c.*.bak`**：3 个历史备份，非当前数据 → 移出仓库或删除
- **`eval_outputs/`（~15MB）**：历史评测产物含剧本全文，体积大；建议整体移出仓库（gitignore）或只留 `SCORE_REPORT.md` 之类汇总
- **`logs/app.jsonl`（2.4MB）**：运行时产物 → gitignore

---

## 5. 总结

**架构很干净，分层教科书级**（API→Service→Agent→Provider→DB，Provider 抽象让所有 Agent 只依赖一个 `generate_structured` 接口），**最大差异化卖点是 `qc_grounding.py` 的确定性证据门禁 + 服务层强制注入 `continuity_contract`**——这两点面试时能讲出"LLM 自由发挥 vs 工程约束"的故事。

**该砍的极少**：1 个死 prompt 文件、几个备份、评测产物；**该冻的明确**：video provider 整块。主链路无需大改，可以直接作为面试项目交付。
