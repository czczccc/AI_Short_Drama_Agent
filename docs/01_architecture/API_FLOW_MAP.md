# API Flow Map

这份文档用于帮助开发者理解“用户调用一个接口后，后端内部到底发生了什么”。它补充 `API.md`：`API.md` 说明如何调用接口；本文说明接口背后的代码入口、业务方法、Agent、Prompt、数据库读写和日志事件。

## 阅读顺序

建议按真实生产顺序阅读：

```text
创建项目
↓
生成故事大纲
↓
生成角色圣经
↓
生成 Showrunner State
↓
生成 Writer Brief
↓
生成剧本，可选开启 Showrunner QC
↓
查询剧本 / Story Memory / QC 报告 / 日志
```

## 核心数据位置

当前 MVP 仍然只使用 SQLite + SQLAlchemy，主要业务状态都保存在 `Project` 模型的 JSON 字段里：

| 字段 | 作用 | 主要写入方 |
|---|---|---|
| `idea` | 用户原始故事创意 | Outline Service |
| `outline_json` | Director Agent 生成的整季大纲 | Outline Service |
| `characters_json` | Character Agent 生成的角色圣经 | Character Service |
| `showrunner_json` | Showrunner State、Writer Brief、Showrunner QC 报告 | Showrunner Service |
| `scripts_json` | 已正式保存的分集剧本 | Script Service |
| `memory_json` | 已正式保存剧本提取出的 Story Memory | Memory Service / Script Service |

注意：Writer 生成的 draft 在 Showrunner QC 通过前，不会写入 `scripts_json`，也不会更新 `memory_json`。

## 日志事件约定

日志默认写入 `logs/app.jsonl`，也可通过 `/dev/logs` 查询。每条日志是一个 JSON 对象，核心字段包括：

```text
timestamp
level
request_id
event
project_id
episode_number
status
duration_ms
qc_status
issue_count
```

当前业务日志只记录流程元数据，不记录完整 Prompt、完整剧本、完整模型输出或 API Key。

## 正式 API

### `GET /api/v1/health`

作用：健康检查，确认 FastAPI 服务可访问。

| 项目 | 内容 |
|---|---|
| API 入口 | `app/api/main.py:health_check` |
| Service | 无 |
| Agent | 无 |
| Provider | 无 |
| 读取字段 | 无 |
| 写入字段 | 无 |
| 日志事件 | `http.request.completed` |
| 成功结果 | `{"status": "ok"}` |
| 常见失败 | 服务未启动或端口不通 |

### `POST /api/v1/projects`

作用：创建一个新的短剧项目，只保存项目名和初始状态。

| 项目 | 内容 |
|---|---|
| API 入口 | `app/api/projects.py:create_project` |
| Request Schema | `ProjectCreate` |
| Response Schema | `ProjectRead` |
| Service | `app/services/project_service.py:create_project` |
| Agent | 无 |
| Provider | 无 |
| 读取字段 | 无 |
| 写入字段 | `Project.name`、`Project.status = "draft"` |
| 日志事件 | `workflow.project.created`、`http.request.completed` |
| 成功结果 | 返回项目 ID、名称、状态和时间戳 |
| 常见失败 | `422`：项目名为空或有额外字段；`500`：数据库写入失败 |

调用链：

```text
create_project API
↓
project_service.create_project
↓
db.add(Project)
↓
db.commit()
↓
log_event("workflow.project.created")
```

### `GET /api/v1/projects/{project_id}`

作用：查询项目基础信息，不返回大纲、角色、剧本等大型 JSON 字段。

| 项目 | 内容 |
|---|---|
| API 入口 | `app/api/projects.py:get_project` |
| Response Schema | `ProjectRead` |
| Service | `app/services/project_service.py:get_project` |
| Agent | 无 |
| Provider | 无 |
| 读取字段 | `Project.id`、`name`、`status`、`created_at`、`updated_at` |
| 写入字段 | 无 |
| 日志事件 | `http.request.completed` |
| 常见失败 | `404`：项目不存在 |

### `POST /api/v1/projects/{project_id}/outline`

作用：根据用户故事创意生成整季结构化大纲。

| 项目 | 内容 |
|---|---|
| API 入口 | `app/api/outlines.py:create_outline` |
| Request Schema | `OutlineGenerateRequest` |
| Response Schema | `OutlineGenerateResponse` |
| Service | `app/services/outline_service.py:generate_outline` |
| Agent | `app/agents/director.py:DirectorAgent.generate_outline` |
| Prompt | `app/prompts/director_v1.md` |
| Provider | `LLMProvider.generate_structured`，当前配置通常为 DeepSeek Provider |
| 读取字段 | `Project.id` |
| 写入字段 | `Project.idea`、`Project.outline_json`、`Project.status = "outline_ready"` |
| 日志事件 | `workflow.outline.started`、`workflow.outline.generated`、`http.request.completed` |
| 常见失败 | `404`：项目不存在；`422`：创意或集数非法；`502`：LLM 输出 JSON 或 Schema 无效；`503`：Provider 配置不可用 |

调用链：

```text
create_outline API
↓
outline_service.generate_outline
↓
project_service.get_project
↓
DirectorAgent.generate_outline
↓
LLMProvider.generate_structured(..., schema=StoryOutline)
↓
保存 idea / outline_json / outline_ready
```

### `POST /api/v1/projects/{project_id}/characters/generate`

作用：根据已保存大纲一次性生成所有主要角色的角色圣经。

| 项目 | 内容 |
|---|---|
| API 入口 | `app/api/characters.py:create_character_bibles` |
| Response Schema | `CharacterBibleResponse` |
| Service | `app/services/character_service.py:generate_character_bibles` |
| Agent | `app/agents/character.py:CharacterAgent.generate_character_bibles` |
| Prompt | `app/prompts/character_v1.md` |
| Provider | `LLMProvider.generate_structured`，当前配置通常为 DeepSeek Provider |
| 读取字段 | `Project.outline_json` |
| 写入字段 | `Project.characters_json`、`Project.status = "characters_ready"` |
| 日志事件 | `workflow.characters.started`、`workflow.characters.saved`、`http.request.completed` |
| 常见失败 | `404`：项目不存在；`409`：大纲尚未生成；`502`：LLM 输出无效；`503`：Provider 配置不可用 |

关键校验：

```text
生成出的 character_id 必须与大纲中的角色匹配。
角色关系引用必须指向有效 character_id。
```

### `GET /api/v1/projects/{project_id}/characters`

作用：读取已保存的角色圣经。

| 项目 | 内容 |
|---|---|
| API 入口 | `app/api/characters.py:read_character_bibles` |
| Response Schema | `CharacterBibleResponse` |
| Service | `app/services/character_service.py:get_character_bibles` |
| Agent | 无 |
| 读取字段 | `Project.outline_json`、`Project.characters_json` |
| 写入字段 | 无 |
| 日志事件 | `http.request.completed` |
| 常见失败 | `404`：项目或角色圣经不存在；`409`：大纲尚未就绪 |

### `PUT /api/v1/projects/{project_id}/characters`

作用：整体替换角色圣经，用于人工修订角色设定。

| 项目 | 内容 |
|---|---|
| API 入口 | `app/api/characters.py:update_character_bibles` |
| Request Schema | `CharacterBibleUpdateRequest` |
| Response Schema | `CharacterBibleResponse` |
| Service | `app/services/character_service.py:replace_character_bibles` |
| Agent | 无 |
| 读取字段 | `Project.outline_json` |
| 写入字段 | `Project.characters_json`、`Project.status = "characters_ready"` |
| 日志事件 | `workflow.characters.saved`、`http.request.completed` |
| 常见失败 | `404`：项目不存在；`409`：大纲尚未就绪；`422`：角色 ID、身份字段或关系引用非法 |

### `POST /api/v1/projects/{project_id}/showrunner`

作用：生成整季 Showrunner State。它是长期一致性的总控状态，不直接写剧本。

| 项目 | 内容 |
|---|---|
| API 入口 | `app/api/showrunner.py:create_showrunner_state` |
| Request Schema | `ShowrunnerGenerateRequest` |
| Response Schema | `ShowrunnerResponse` |
| Service | `app/services/showrunner_service.py:generate_showrunner_state` |
| Agent | `app/agents/showrunner.py:ShowrunnerAgent.generate_showrunner_state` |
| Prompt | `app/prompts/showrunner/v1.py` |
| Provider | `LLMProvider.generate_structured` |
| 读取字段 | `Project.outline_json`、`Project.characters_json` |
| 写入字段 | `Project.showrunner_json` |
| 日志事件 | `workflow.showrunner.started`、`workflow.showrunner.generated`、`http.request.completed` |
| 常见失败 | `404`：项目不存在；`409`：大纲或角色圣经尚未就绪；`502`：LLM 输出无效；`503`：Provider 配置不可用 |

生成结果包含：

```text
version
source_outline_hash
source_characters_hash
story_bible
episode_plan
character_arcs
writer_briefs = {}
qc_reports = {}
```

哈希由 `stable_json_sha256` 基于稳定排序 JSON 计算，不使用 Python 内置 `hash()`。

### `GET /api/v1/projects/{project_id}/showrunner`

作用：读取已保存的 Showrunner State。

| 项目 | 内容 |
|---|---|
| API 入口 | `app/api/showrunner.py:read_showrunner_state` |
| Response Schema | `ShowrunnerResponse` |
| Service | `app/services/showrunner_service.py:get_showrunner_state` |
| Agent | 无 |
| 读取字段 | `Project.showrunner_json` |
| 写入字段 | 无 |
| 日志事件 | `http.request.completed` |
| 常见失败 | `404`：项目或 Showrunner State 不存在 |

### `POST /api/v1/projects/{project_id}/episodes/{episode_number}/writer-brief`

作用：Showrunner 为第 N 集生成 Writer Brief，给 Writer 明确本集边界、必写内容、禁写内容、角色当前状态和结尾要求。

| 项目 | 内容 |
|---|---|
| API 入口 | `app/api/showrunner.py:create_writer_brief` |
| Request Schema | `WriterBriefGenerateRequest` |
| Response Schema | `WriterBriefResponse` |
| Service | `app/services/showrunner_service.py:generate_writer_brief` |
| Agent | `app/agents/showrunner.py:ShowrunnerAgent.generate_writer_brief` |
| Prompt | `app/prompts/showrunner/brief_v1.py` |
| Provider | `LLMProvider.generate_structured` |
| 读取字段 | `Project.showrunner_json`、`Project.memory_json` |
| 写入字段 | `Project.showrunner_json.writer_briefs[N]` |
| 日志事件 | `workflow.writer_brief.started`、`workflow.writer_brief.generated`、`http.request.completed` |
| 常见失败 | `404`：项目、Showrunner State 或 Episode Plan 不存在；`422`：目标时长非法；`502`：LLM 输出无效；`503`：Provider 配置不可用 |

调用链：

```text
create_writer_brief API
↓
showrunner_service.generate_writer_brief
↓
load_showrunner_state
↓
_ensure_episode_in_plan
↓
load_story_memory
↓
ShowrunnerAgent.generate_writer_brief
↓
保存到 showrunner_json.writer_briefs[N]
```

### `GET /api/v1/projects/{project_id}/episodes/{episode_number}/writer-brief`

作用：读取已保存的第 N 集 Writer Brief。

| 项目 | 内容 |
|---|---|
| API 入口 | `app/api/showrunner.py:read_writer_brief` |
| Response Schema | `WriterBriefResponse` |
| Service | `app/services/showrunner_service.py:get_writer_brief` |
| Agent | 无 |
| 读取字段 | `Project.showrunner_json.writer_briefs[N]` |
| 写入字段 | 无 |
| 日志事件 | `http.request.completed` |
| 常见失败 | `404`：项目、Showrunner State、Episode Plan 或 Writer Brief 不存在 |

### `POST /api/v1/projects/{project_id}/episodes/{episode_number}/script`

作用：生成并保存第 N 集剧本。默认保持旧流程；如果开启 Showrunner Brief 和 Showrunner QC，则先生成 draft，通过 QC 后才正式保存并更新 Story Memory。

| 项目 | 内容 |
|---|---|
| API 入口 | `app/api/scripts.py:create_script` |
| Request Schema | `ScriptGenerateRequest` |
| Response Schema | `ScriptResponse` |
| Service | `app/services/script_service.py:generate_script` |
| Agent | `WriterAgent.generate_script`；开启 QC 时还会调用 `QCAgent.generate_report` |
| Prompt | `app/prompts/writer_v2.md`；开启 QC 时使用 `app/prompts/qc_v1.md` |
| Provider | `LLMProvider.generate_structured` |
| 读取字段 | `Project.outline_json`、`Project.characters_json`、`Project.memory_json`、可选 `Project.showrunner_json.writer_briefs[N]` |
| 写入字段 | QC 通过或未开启 QC 时写 `Project.scripts_json[N]` 和 `Project.memory_json`；开启 QC 时总是写 `Project.showrunner_json.qc_reports[N]` |
| 日志事件 | `workflow.script.started`、`workflow.script.draft_generated`、可选 `workflow.showrunner_qc.saved`、`workflow.showrunner_qc.passed` 或 `workflow.showrunner_qc.blocked`、成功保存时 `workflow.script.saved`、`http.request.completed` |
| 常见失败 | `404`：项目、分集、Brief 不存在；`409`：大纲未就绪、QC 未开启 Brief、QC 未通过；`422`：请求参数非法；`502`：LLM 输出无效；`503`：Provider 配置不可用 |

正常无 QC 流程：

```text
create_script API
↓
script_service.generate_script
↓
load_outline
↓
_find_episode
↓
load_character_bibles
↓
load_story_memory
↓
WriterAgent.generate_script
↓
保存 scripts_json[N]
↓
upsert_episode_memory
↓
status = script_ready
```

开启 Showrunner QC 流程：

```text
create_script API
↓
script_service.generate_script
↓
读取 Writer Brief
↓
WriterAgent.generate_script 生成 draft
↓
QCAgent.generate_report
↓
save_showrunner_qc_report
↓
if QC pass:
    保存 scripts_json[N]
    upsert_episode_memory
    status = script_ready
else:
    commit QC report
    raise ShowrunnerQCNotPassedError
```

最重要的判断：

```text
看到 workflow.script.saved
=> 正式剧本已经保存，Story Memory 已更新。

看到 workflow.showrunner_qc.blocked
=> QC 拦截，draft 未保存，Story Memory 未更新。
```

### `GET /api/v1/projects/{project_id}/episodes/{episode_number}/script`

作用：读取已正式保存的第 N 集剧本。不会返回 Writer draft。

| 项目 | 内容 |
|---|---|
| API 入口 | `app/api/scripts.py:read_script` |
| Response Schema | `ScriptResponse` |
| Service | `app/services/script_service.py:get_script` |
| Agent | 无 |
| 读取字段 | `Project.outline_json`、`Project.scripts_json[N]` |
| 写入字段 | 无 |
| 日志事件 | `http.request.completed` |
| 常见失败 | `404`：项目、分集或正式剧本不存在；`409`：大纲未就绪 |

### `GET /api/v1/projects/{project_id}/episodes/{episode_number}/showrunner-qc`

作用：读取最近一次由剧本生成流程保存的 Showrunner QC 报告。它只读，不重新调用 LLM。

| 项目 | 内容 |
|---|---|
| API 入口 | `app/api/showrunner.py:read_showrunner_qc_report` |
| Response Schema | `ShowrunnerQCResponse` |
| Service | `app/services/showrunner_service.py:get_showrunner_qc_report` |
| Agent | 无 |
| 读取字段 | `Project.showrunner_json.qc_reports[N]` |
| 写入字段 | 无 |
| 日志事件 | `http.request.completed` |
| 常见失败 | `404`：项目、Showrunner State、Episode Plan 或 QC 报告不存在 |

## 开发辅助接口

### `GET /dev/testbench`

作用：返回本地开发测试页 HTML，方便人工从浏览器测试工作流。

| 项目 | 内容 |
|---|---|
| API 入口 | `app/api/dev.py:get_testbench` |
| Service | 无 |
| 读取字段 | `app/dev/testbench.html` |
| 写入字段 | 无 |
| 日志事件 | `http.request.completed` |
| OpenAPI | 不显示 |

### `GET /dev/projects`

作用：列出最近本地项目，供测试页加载历史项目。

| 项目 | 内容 |
|---|---|
| API 入口 | `app/api/dev.py:list_dev_projects` |
| Service | 无 |
| 读取字段 | `Project.id`、`name`、`status`、`idea`、`scripts_json`、时间戳 |
| 写入字段 | 无 |
| 日志事件 | `http.request.completed` |
| OpenAPI | 不显示 |

### `GET /dev/projects/{project_id}/state`

作用：一次性查看项目当前所有关键 JSON 状态，适合人工排查。

| 项目 | 内容 |
|---|---|
| API 入口 | `app/api/dev.py:get_dev_project_state` |
| Service | 调用 `load_story_memory` 组装 Memory |
| 读取字段 | `outline_json`、`characters_json`、`scripts_json`、`memory_json` |
| 写入字段 | 无 |
| 日志事件 | `http.request.completed` |
| OpenAPI | 不显示 |

注意：该接口是开发辅助，不是正式产品接口。独立前端不要依赖它作为生产 API。

### `DELETE /dev/projects/{project_id}`

作用：删除本地开发项目，方便清理测试数据。

| 项目 | 内容 |
|---|---|
| API 入口 | `app/api/dev.py:delete_dev_project` |
| Service | 无 |
| 读取字段 | `Project.id` |
| 写入字段 | 删除整条 Project 记录 |
| 日志事件 | `http.request.completed` |
| OpenAPI | 不显示 |
| 常见失败 | `404`：项目不存在 |

### `POST /dev/projects/{project_id}/episodes/{episode_number}/qc`

作用：对已正式保存的剧本执行一次人工辅助 QC。它只返回报告，不保存报告，不改剧本，不改 Story Memory。

| 项目 | 内容 |
|---|---|
| API 入口 | `app/api/dev.py:generate_dev_episode_qc` |
| Service | `app/services/qc_service.py:generate_episode_qc` |
| Agent | `app/agents/qc.py:QCAgent.generate_report` |
| Prompt | `app/prompts/qc_v1.md` |
| 读取字段 | `Project.outline_json`、`characters_json`、`memory_json`、`scripts_json[N]` |
| 写入字段 | 无 |
| 日志事件 | `http.request.completed` |
| OpenAPI | 不显示 |
| 常见失败 | `404`：项目、分集或剧本不存在；`409`：大纲未就绪；`502`/`503`：LLM 问题 |

### `GET /dev/logs`

作用：读取本地 JSONL 日志，帮助复盘接口和工作流实际发生了什么。

| 项目 | 内容 |
|---|---|
| API 入口 | `app/api/dev.py:list_dev_logs` |
| Service | `app/observability/logging.py:read_recent_logs` |
| 读取字段 | `logs/app.jsonl` |
| 写入字段 | 无 |
| 查询参数 | `project_id`、`limit` |
| OpenAPI | 不显示 |

## 内部模块职责

### API Layer

API Layer 只负责：

```text
接收请求
校验 Pydantic schema
注入数据库 Session
注入 LLM Provider
调用 Service
把业务异常转换为 HTTP 错误
返回响应 schema
```

它不应该直接写复杂业务逻辑。

### Service Layer

Service Layer 负责主要业务流程：

```text
检查 Project 是否存在
读取和校验 Project JSON 字段
调用 Agent
合并/覆盖 JSON 字段
提交数据库事务
发出业务日志事件
```

当前核心 Service：

| Service | 作用 |
|---|---|
| `project_service` | 创建和读取项目基础信息 |
| `outline_service` | 生成和读取 Story Outline |
| `character_service` | 生成、读取、替换 Character Bible |
| `showrunner_service` | 生成 Showrunner State、Writer Brief、保存/读取 QC 报告 |
| `script_service` | 生成/读取正式剧本，执行可选 QC 门禁 |
| `memory_service` | 从正式剧本构建和更新 Story Memory |
| `qc_service` | 开发辅助 QC，不持久化报告 |

### Agent Layer

Agent Layer 负责构造模型输入并调用 LLM Provider：

| Agent | 作用 | Prompt |
|---|---|---|
| `DirectorAgent` | 根据故事创意生成整季大纲 | `director_v1.md` |
| `CharacterAgent` | 根据大纲生成角色圣经 | `character_v1.md` |
| `ShowrunnerAgent` | 生成 Showrunner State 和 Writer Brief | `showrunner/v1.py`、`showrunner/brief_v1.py` |
| `WriterAgent` | 生成单集剧本 | `writer_v2.md` |
| `QCAgent` | 对剧本进行结构化 QC | `qc_v1.md` |

Agent 不直接写数据库。

### Provider Layer

Provider Layer 封装外部模型调用：

```text
LLMProvider.generate_structured
↓
DeepSeekProvider.generate_structured
```

业务代码依赖抽象 `LLMProvider`，不直接绑定 DeepSeek。以后替换 OpenAI 或其他模型时，应主要新增 Provider，而不是改 Service 业务流程。

### Observability

日志系统由 `app/observability/logging.py` 提供：

| 方法 | 作用 |
|---|---|
| `configure_logging` | 配置 JSONL 文件输出 |
| `set_request_id` / `reset_request_id` | 在一次请求上下文中保存 request_id |
| `log_event` | 写一条结构化业务事件 |
| `read_recent_logs` | 读取最近日志，供 `/dev/logs` 使用 |

FastAPI middleware 会为每个请求生成或继承 `X-Request-ID`，并在响应头返回同一个 ID。

## 如何用日志判断一次操作是否成功

### 判断大纲是否保存

```text
出现 workflow.outline.generated
并且 status = outline_ready
```

### 判断角色圣经是否保存

```text
出现 workflow.characters.saved
并且 status = characters_ready
```

### 判断 Showrunner State 是否保存

```text
出现 workflow.showrunner.generated
```

### 判断 Writer Brief 是否保存

```text
出现 workflow.writer_brief.generated
```

### 判断剧本是否正式保存

```text
出现 workflow.script.saved
并且 status = script_ready
```

### 判断 QC 是否拦截

```text
出现 workflow.showrunner_qc.blocked
并且没有 workflow.script.saved
```

### 判断 Story Memory 是否更新

```text
当前实现中，Story Memory 更新发生在 workflow.script.saved 之前的同一事务中。
所以出现 workflow.script.saved，表示正式剧本已保存，Story Memory 也已更新。
```

## 当前边界

当前还没有实现：

```text
Storyboard 生成 API
视频任务提交 API
视频任务轮询 API
字幕 / 音频 / FFmpeg 合成 API
```

Video Provider 抽象和 Fake Provider 已存在，但尚未接入正式 HTTP 工作流。
