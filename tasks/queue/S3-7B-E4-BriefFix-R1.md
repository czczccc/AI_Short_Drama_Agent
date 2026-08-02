# Task S3-7B-E4-BriefFix-R1

`AUTO_CONTINUE: no`

## Goal

收窄 Brief Prompt 的“一致性自检 2”：不得禁止的是 `continuity_contract` 要求在本集发生的承接动作本身；但 `forbidden_content` 仍可且应限制错误角色获知、秘密公开、未来事件提前发生或本集提前解决尚未到期的问题。

## Allowed Files

- `app/prompts/showrunner/brief_v1.py`
- `tests/test_showrunner.py`
- `tasks/execution_log.md`（仅追加）

## Requirements

1. 删除或改写“上一集已发生的事实不得被列入本集禁止内容”这一过宽表述。
2. 明确 `forbidden_content` 不得直接禁止合同要求的承接动作、末场状态承接或到期义务处理。
3. 明确仍可禁止：某角色在无依据时获知事实、秘密被提前公开、后续集事件提前发生、只需延续的义务被本集提前彻底解决。
4. `required_beats` 必须为合同义务留下可执行节拍，但不得因此扩大角色认知或揭密范围。
5. 更新测试，同时断言“允许承接”和“继续保护认知/秘密/未来边界”两面规则，不能只检查旧关键字。
6. 不修改其他 Prompt、Agent、Schema、Service、API 或数据库。

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_showrunner.py
.\.venv\Scripts\python.exe -m pytest -q
git diff --check
```

完成后停止；不调用真实 LLM、不执行第 5 集。

