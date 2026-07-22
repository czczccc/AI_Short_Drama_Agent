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
- `app/agents` —— Director Agent
- `app/prompts` —— 版本化 Prompt
- `data/` —— 本地 SQLite 数据库和数据库备份
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

## 运行测试

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## 文档

前端调用契约见 `docs/01_architecture/API.md`；其他产品与设计文档见 `docs/` 目录。
