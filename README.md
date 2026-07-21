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
- （后续 Phase）视频模型：Seedance / 豆包 / Kling / Veo；FFmpeg 合成

## 目录结构

- `app/api` —— FastAPI 入口与路由
- `app/configs` —— 配置读取
- `app/database` —— 数据库连接与基类
- `app/models` —— SQLAlchemy 模型
- `app/schemas` —— Pydantic 模型
- `app/services` —— 业务逻辑
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

3. 启动服务（首次启动会自动创建 SQLite 数据库 `app.db`）

   ```powershell
   uvicorn app.api.main:app --reload
   ```

4. 验证

   - 健康检查： http://127.0.0.1:8000/health
   - 交互式 API 文档： http://127.0.0.1:8000/docs

## 运行测试

```powershell
pytest -q
```

## 文档

完整产品与设计文档见 `docs/` 目录（PRD、ARCHITECTURE、TASKS 等）。
