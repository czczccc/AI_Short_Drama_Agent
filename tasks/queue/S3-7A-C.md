# Task S3-7A-C

`AUTO_CONTINUE: no`

## Goal

围绕 S3-7A-B 的唯一 Request ID，只读核对完整日志链和数据库保存结果，形成可供 Codex 验收的阻塞回归证据。

## Required Context

- `AGENTS.md`
- `docs/02_ai/WORKFLOW.md` 的日志事件与 QC 保存原则
- `tasks/execution_log.md` 中 S3-7A-A、S3-7A-B 的本批记录
- 只读解析项目与日志所需的最少代码

## Allowed Files

- `tasks/execution_log.md`（仅追加）

不得再次调用任何生成 API 或 LLM；不得修改数据库和日志。

## Requirements

1. 只筛选 B 的唯一 Request ID，按时间顺序列出安全事件名、阶段、尝试号、QC 状态、HTTP 状态码和耗时；不复制 Prompt 或正文。
2. 核对 LLM 调用次数、Writer 尝试次数和 QC 尝试次数是否符合 `max_revision_attempts=2` 的上限。
3. 对比 A 的第 2 集基线指纹与当前 Script、Memory、Brief、QC 子树：
   - `200`：正式 Script 和 QC 必须存在；Memory 必须为 QC-approved 且与第 2 集对应；Brief 不应被剧本生成覆盖。
   - `409`/`502`/`503`：不得新增或覆盖正式 Script/Memory；允许保存最近 QC 报告仅限现有流程明确允许的情况；Brief 不应改变。
4. 核对剧本与 Memory 的保存要么同时成功，要么正式内容均保持基线，不接受半保存。
5. 区分业务拒绝、Schema/证据失败、Provider 失败与超时，不把非 200 自动写成代码缺陷。
6. 记录最终判定：`accepted`、`rejected_as_expected` 或 `failed_atomicity`，并注明是否阻塞 S3-7B。

## Verification

```powershell
git diff --check
git diff --name-only -- app tests requirements.txt
```

追加 `S3-7A-C/attempt-1` 后停止整个批次，等待 Codex 复核；不得进入 S3-7B。

