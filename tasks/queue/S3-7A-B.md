# Task S3-7A-B

`AUTO_CONTINUE: yes`

## Goal

使用现有正式 API 对项目 16 第 2 集执行恰好一次真实 Writer + Showrunner QC 阻塞回归，允许真实 DeepSeek 费用和预期的数据库写入。

## Authorization

本任务明确授权：

- 调用当前配置的真实 LLM Provider。
- 通过现有 API 写入项目 16 的 SQLite 数据。
- 使用最多两次 Writer 自动返修。

不授权修改 `.env`、生产代码、Prompt、测试、依赖、API、Schema，也不授权重复请求试错。

## Required Context

- `AGENTS.md`
- `docs/01_architecture/API.md` 的剧本生成接口
- `docs/02_ai/WORKFLOW.md` 的 Showrunner QC 保存原则
- `app/api/main.py` 的应用入口

## Allowed Files

- `data/app.db`（只能由现有 API 正常事务写入）
- `logs/app.jsonl`（只能由现有日志系统写入）
- `tasks/execution_log.md`（仅追加）

## Requirements

1. 使用 `TestClient(app)` 或已运行的本地正式 API，向以下端点只发送一次 POST：
   - `/api/v1/projects/16/episodes/2/script`
2. 请求体固定为：

```json
{
  "target_duration_seconds": 90,
  "use_showrunner_brief": true,
  "run_showrunner_qc": true,
  "max_revision_attempts": 2
}
```

3. 显式传入唯一 `X-Request-ID`，格式 `s3-7a-p16-e2-YYYYMMDDHHMMSS`；请求前先确认日志中不存在该 ID。
4. 记录 Request ID、HTTP 状态码、响应头返回的 Request ID、总耗时和安全错误摘要；不得把完整剧本、Prompt、模型响应写入 execution log。
5. `200`、`409`、`502` 或 `503` 都属于一次已完成的回归请求，不得为了得到成功结果再次发送；只要请求已到达应用且 Request ID 可审计，就继续 C。
6. 若请求未到达应用、进程崩溃或 Request ID 不可确定，记录 `blocked` 并停止；仍不得补发第二次请求。

## Verification

```powershell
git diff --check
git diff --name-only -- app tests requirements.txt
```

本任务不判断业务验收是否通过，只记录唯一真实请求的事实结果，并继续 C 做原子性审计。

