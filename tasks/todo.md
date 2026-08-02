# Current Execution Packet

## Task ID

`S3-6.3-C`

## Title

锁定后端补全义务时的场景证据复用

## Owner

- 代码执行：DeepSeek
- 复核验收与任务状态更新：Codex

## Goal

增加一个聚焦单元测试，证明 `complete_missing_continuity_obligations()` 为缺失义务补全 `memory_evidence` 时，会逐字复用对应 `unresolved_questions.N` 的场号和场景原文。

当前生产逻辑已经存在；本任务首先补足契约测试。如果新增测试直接通过，不要为了产生代码 diff 而修改生产实现。

## Required Context

按顺序只读取：

1. `AGENTS.md`
2. 本文件
3. `app/services/qc_grounding.py` 中 `complete_missing_continuity_obligations()` 及相邻证据校验函数
4. `tests/test_qc_grounding.py`
5. 如需复用 fixture，再读取 `tests/fakes.py` 中 `valid_qc_pass_report_data()`
6. 完成或阻塞后读取 `tasks/execution_log.md` 的记录规则并追加本次记录

不要一次读取全部 `docs`。

## Allowed Files

默认只允许修改：

- `tests/test_qc_grounding.py`

仅当新增测试证明现有行为不满足验收标准时，才允许最小修改：

- `app/services/qc_grounding.py`

无论完成还是阻塞，都允许且必须仅追加：

- `tasks/execution_log.md`

不得修改其他文件。需要越界时停止并报告。

## Implementation Requirements

新增一个命名清楚的测试，至少覆盖：

1. 构造 `status=pass` 且包含 `unresolved_questions.0` 的 QC Report。
2. 删除模型返回的 `continuity_obligations` 及其义务证据，但保留 `unresolved_questions.0` 的合法场景证据。
3. 调用 `complete_missing_continuity_obligations()`。
4. 断言新增义务对应的 `memory_evidence` 路径为 `continuity_obligations.0`。
5. 断言该证据的 `scene_number` 和 `evidence_text` 与 `unresolved_questions.0` 的证据完全相同。

禁止使用模糊匹配、生成新证据文字或调用 LLM。缺少未解决问题证据时不得伪造证据；该边界不属于本任务的新功能，不要顺手扩写。

## Non-Goals

- 不测试或修改“保留已有合法义务并去重”；它属于 `S3-6.3-D`。
- 不测试第10集；它属于 `S3-6.3-E`。
- 不修改 Prompt、Schema、API、数据库、Provider 或 Story Memory 保存流程。
- 不运行真实 DeepSeek 调用。
- 不更新 `TASKS.md`、`tasks/plan.md` 或本文件的完成状态；只向 `tasks/execution_log.md` 末尾追加本次执行记录。
- 不 commit、不 push、不修改 `.env`。

## Verification Commands

必须运行并原样报告：

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_qc_grounding.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_scripts.py::test_showrunner_qc_completes_missing_unresolved_question_obligation
git diff --check
```

本任务不运行全部 pytest；全量测试统一在 `S3-6.3-G` 执行。

## Acceptance Criteria

- 新测试明确验证义务证据路径、场号和原文逐字复用。
- 两条 pytest 命令均通过，`git diff --check` 无错误。
- 生产代码只有在测试揭示真实缺口时才发生最小修改。
- 没有任何白名单外修改。
- `tasks/execution_log.md` 已按模板追加 `S3-6.3-C/attempt-N`，准确记录修改、方法和测试结果。

## Stop Conditions

出现以下情况立即停止并返回 `blocked`：

- 必须修改白名单外文件才能完成。
- 现有工作区改动与目标代码冲突。
- 测试暴露的是 Schema/API/Prompt 问题，而不是证据复用问题。
- 需要猜测新的业务规则。

## Required Report

```text
TASK_ID: S3-6.3-C
RESULT: completed | blocked
FILES_CHANGED:
- path: purpose
TESTS_RUN:
- exact command
- exact result
ACCEPTANCE_EVIDENCE:
- criterion: evidence
NOT_CHANGED:
- out-of-scope areas preserved
RISKS_OR_BLOCKERS:
- none, or exact blocker
```

把以上报告追加到 `tasks/execution_log.md` 后，再在对话中返回同一内容的简要版本。日志中不得写入 API Key、`.env` 内容、完整 Prompt 或完整模型输出。
