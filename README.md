# AI Short Drama Agent

AI 短剧生产系统：从创意输入到视频成片形成自动化工作流。

## 核心原则

- MVP 优先
- 模块化
- 模型可替换
- 数据可追踪
- Agent 可长期维护

## 技术栈

- 后端：Python 3.12 + FastAPI
- 数据库：SQLite（SQLAlchemy）
- 配置：pydantic-settings + .env
- 当前 LLM Provider：DeepSeek V4 Pro（可替换 Provider 设计）
- 未来计划 LLM Provider：OpenAI
- （后续 Phase）视频模型：Seedance / 豆包 / Kling / Veo；FFmpeg 合成

## 目录结构

- `app/api` —— FastAPI 入口与路由
- `app/configs` —— 配置读取
- `app/database` —— 数据库连接与基类
- `app/models` —— SQLAlchemy 模型
- `app/schemas` —— Pydantic 模型
- `app/services` —— 业务逻辑
- `app/providers/llm` —— 通用 LLM Provider 与 DeepSeek 适配器
- `app/agents` —— Director、Character、Writer、QC 与 Showrunner Agent
- `app/prompts` —— 版本化 Prompt
- `app/observability` —— 本地结构化日志与请求链路追踪
- `data/` —— 本地 SQLite 数据库和数据库备份
- `logs/` —— 本地运行日志（默认忽略提交）
- `tests/` —— 测试
- `docs/` —— 产品与设计文档

## 快速启动（Windows PowerShell）

> 前置条件：本机已安装 Python 3.12（本项目统一使用 Python 3.12）。

1. 创建虚拟环境并安装依赖

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. 复制环境变量

   ```powershell
   copy .env.example .env
   ```

3. 启动服务（首次启动会自动创建 SQLite 数据库 `data/app.db`）

   ```powershell
   uvicorn app.api.main:app --reload
   ```

4. 验证

   - API 基础地址： http://127.0.0.1:8000/api/v1
   - 健康检查： http://127.0.0.1:8000/api/v1/health
   - 交互式 API 文档： http://127.0.0.1:8000/docs
   - OpenAPI JSON： http://127.0.0.1:8000/openapi.json

独立前端允许访问的来源由 `.env` 中的 `CORS_ALLOWED_ORIGINS` 配置。开发环境默认示例包含本机 `3000` 和 `5173` 端口；生产环境应替换为实际前端域名，不要使用 `*`。

## 本地日志

服务会为每个 HTTP 请求返回 `X-Request-ID`，并把请求和关键工作流事件写入本地 JSONL 日志，默认路径为 `logs/app.jsonl`。可以在 `.env` 中用 `LOG_FILE_PATH` 覆盖。

查看最近日志：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/dev/logs?limit=50"
```

按项目过滤：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/dev/logs?project_id=$($project.id)&limit=50"
```

日志只记录 `event`、`request_id`、`project_id`、`episode_number`、状态码和耗时等元数据，不记录 API Key、完整 Prompt 或完整剧本正文。

## Phase 2A：生成 10 集大纲

先创建项目：

```powershell
$project = Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/api/v1/projects" `
  -ContentType "application/json" `
  -Body (@{ name = "逆袭程序员" } | ConvertTo-Json)
```

再生成结构化大纲：

```powershell
$body = @{
  idea = "一个被公司开除的程序员发现老板窃取了他的AI成果"
  episode_count = 10
} | ConvertTo-Json

Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/api/v1/projects/$($project.id)/outline" `
  -ContentType "application/json" `
  -Body $body
```

## 开发环境数据库重建

Phase 2A 直接给 `Project` 增加字段，没有引入 Alembic。已有开发库需要在服务停止后重建；如有需要请先自行备份：

```powershell
Remove-Item -LiteralPath .\data\app.db
uvicorn app.api.main:app --reload
```

应用启动时会重新创建 `data/app.db`。测试始终使用临时 SQLite 数据库，不会写入正式数据库。

Phase 2C 启动时会为已有 SQLite `projects` 表幂等增加 `characters_json` 字段，无需删除已有开发库。

Phase 3.1 启动时会为已有 SQLite `projects` 表幂等增加 `showrunner_json` 字段，无需删除已有开发库。Showrunner State 需要在大纲和角色圣经生成后创建：

```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/api/v1/projects/$($project.id)/showrunner" `
  -ContentType "application/json" `
  -Body "{}"
```

查询已保存的 Showrunner State：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/projects/$($project.id)/showrunner"
```

当前 Showrunner 已完成 State、Writer Brief、Writer 接入、QC 门禁、Story Memory v2、有限自动返修、场景证据门禁和跨集连续性合同。

Phase 3.2 可为指定集生成 Writer Brief：

```powershell
$briefBody = @{
  target_duration_seconds = 90
  force_regenerate = $false
} | ConvertTo-Json

Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/api/v1/projects/$($project.id)/episodes/1/writer-brief" `
  -ContentType "application/json" `
  -Body $briefBody
```

查询已保存的 Writer Brief：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/projects/$($project.id)/episodes/1/writer-brief"
```

生成剧本时可选择使用已保存 Writer Brief：

```powershell
$scriptBody = @{
  target_duration_seconds = 90
  use_showrunner_brief = $true
} | ConvertTo-Json

Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/api/v1/projects/$($project.id)/episodes/1/script" `
  -ContentType "application/json" `
  -Body $scriptBody
```

`use_showrunner_brief` 默认为 `$false`。开启后系统只读取已保存 Brief，不会自动生成 Brief。

如需开启 Showrunner QC 门禁，让剧本先作为 draft 接受审核：

```powershell
$scriptBody = @{
  target_duration_seconds = 90
  use_showrunner_brief = $true
  run_showrunner_qc = $true
  max_revision_attempts = 1
} | ConvertTo-Json

Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/api/v1/projects/$($project.id)/episodes/1/script" `
  -ContentType "application/json" `
  -Body $scriptBody
```

系统先执行规则型 QC，再执行 LLM Showrunner QC，最后由后端确定性校验 `memory_evidence` 和 `continuity_resolutions`。QC 只有 `pass` 且所有正式记忆都能定位到场景原文、上一集连续性合同逐条处理完成时，才会保存正式剧本，并用审核后的 `approved_memory` 更新 Story Memory v2；`warning` 或 `fail` 会触发最多 `max_revision_attempts` 次返修，达到上限仍未通过则阻断保存。QC 报告仍可查询：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/projects/$($project.id)/episodes/1/showrunner-qc"
```

## 运行测试

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## 文档

前端调用契约见 `docs/01_architecture/API.md`；如果想理解每个接口背后的调用链、读写字段、Agent 和日志事件，见 `docs/01_architecture/API_FLOW_MAP.md`；其他产品与设计文档见 `docs/` 目录。
