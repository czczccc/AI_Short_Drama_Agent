# DeepSeek Autonomous Text-MVP Run

## Authority

用户于 2026-08-02 明确授权 DeepSeek 全权负责本项目后续文字端工作。Codex 不再是审批门禁。

## Current Task

先完成 `S3-7B-E4-BriefFix-R1`：执行 `tasks/queue/S3-7B-E4-BriefFix-R1.md`，收窄 Brief Prompt 并补测试，不需要再次真实生成第 4 集。

## After Current Task

通过定向测试、全部 pytest、diff 自审后，DeepSeek应：

1. 向 `tasks/execution_log.md` 追加 execution 和 self-review。
2. 在 `docs/03_development/TASKS.md` 标记该修复及 S3-7B-A3 完成。
3. 自行编写并执行第 5 集任务及第 1–5 集检查点。
4. 按 `tasks/text_backlog.md` 和固定依赖链继续 S3-7B-B、S3-7B-C、S3-7B-D、S3-7C、S3-7D、S3-8、S3-9。

## Autonomous Gates

- 每一集必须 Brief → 单次 Script 请求（QC 开启、最多两次返修）→ Request ID/数据库原子性审计。
- 非 200 时不得重复刷请求；先记录证据并建立最小根因任务。
- 每个检查点运行全部 pytest、更新 TASKS/plan/todo，并提交逻辑清晰的 Git commit。
- 真实 LLM 和项目数据库写入仅用于 TASKS 已列明的文字端验证；不得输出或提交密钥、`.env`、运行数据库或完整敏感日志。
- S3-9 完成后停止，向用户提交最终文字 MVP 报告；不启动 Storyboard、视频或其他非文字任务。
