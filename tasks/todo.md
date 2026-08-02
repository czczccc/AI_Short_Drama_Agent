# Current Execution Packet

## Task ID

`S3-6.3-D`

## Title

保留已有合法义务并避免同来源重复

## Owner

- 代码执行：DeepSeek
- 复核验收与任务状态更新：Codex

## Goal

增加聚焦单元测试，证明 `complete_missing_continuity_obligations()` 会保留模型已经生成的合法义务，不会为同一个 `source_memory_path` 再创建后端义务，并且重复调用保持幂等。

当前生产逻辑已经存在；优先补足契约测试。若测试直接通过，不要为了制造代码改动而修改生产实现。

## Required Context

按顺序只读取：

1. `AGENTS.md`
2. 本文件
3. `app/services/qc_grounding.py` 中 `complete_missing_continuity_obligations()`
4. `tests/test_qc_grounding.py`
5. 如需 fixture，只读取 `tests/fakes.py` 中 `valid_qc_pass_report_data()`
6. 完成或阻塞后读取 `tasks/execution_log.md` 并追加本次记录

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

1. 构造第1集 `status=pass` 的 QC Report，其中 `unresolved_questions.0` 已经有一条字段合法的模型义务和对应 `continuity_obligations.0` 证据。
2. 记录调用前义务和证据的完整 `model_dump(mode="json")` 数据。
3. 调用 `complete_missing_continuity_obligations()`，断言义务数量仍为1、原义务内容不变、没有同来源路径重复项、义务证据没有重复。
4. 对第一次结果再次调用该函数，断言第二次结果与第一次结果的完整 JSON 数据相同，证明幂等。

判断“同一义务”只使用精确的 `source_memory_path`，不得增加模糊文本匹配。

## Non-Goals

- 不测试第10集；它属于 `S3-6.3-E`。
- 不修改 Prompt、Schema、API、数据库、Provider 或 Story Memory 保存流程。
- 不引入义务合并、描述改写或模糊去重规则。
- 不运行真实 LLM。
- 不更新 `TASKS.md`、`tasks/plan.md` 或本文件状态；只追加执行日志。
- 不 commit、不 push、不修改 `.env`。

## Verification Commands

必须运行并原样报告：

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_qc_grounding.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_scripts.py::test_showrunner_qc_completes_missing_unresolved_question_obligation
git diff --check
```

全量 pytest 留到 `S3-6.3-G`。

## Acceptance Criteria

- 新测试证明已有合法义务及其证据保持不变。
- 同一 `source_memory_path` 不产生第二条义务，重复调用结果幂等。
- 两条 pytest 命令通过，`git diff --check` 无错误。
- 没有白名单外修改；生产代码只在测试揭示真实缺口时最小修改。
- `tasks/execution_log.md` 已追加 `S3-6.3-D/attempt-N`。

## Stop Conditions

出现以下情况立即停止并返回 `blocked`：

- 需要修改白名单外文件。
- 需要引入模糊匹配、Schema/API/Prompt 变化或新业务规则。
- 当前工作区改动与目标文件冲突。
- 指定测试外出现不属于本任务的失败。

## Required Report

```text
TASK_ID: S3-6.3-D
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

把以上报告追加到 `tasks/execution_log.md` 后，再在对话中返回摘要。禁止记录 API Key、`.env` 内容、完整 Prompt 或完整模型输出。
