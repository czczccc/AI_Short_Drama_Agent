# Task S3-7A-A

`AUTO_CONTINUE: yes`

## Goal

在真实模型调用前，以只读方式建立项目 16、模型配置和第 2 集持久化状态基线。

## Required Context

- `AGENTS.md`
- `docs/03_development/TASKS.md` 中 S3-7A
- `docs/02_ai/MODEL_INTEGRATION.md`
- `app/configs/settings.py`
- `app/models/project.py`
- 只读查询所需的最少数据库与 Schema 文件

禁止读取或输出 `.env` 内容。只可报告 Provider、模型名、Base URL 是否配置、API Key 是否存在（true/false）。

## Allowed Files

- `tasks/execution_log.md`（仅追加）

## Requirements

1. 只读确认项目 16 的名称、状态、目标集数，以及 Outline、Characters、Showrunner State、Scripts、Memory 的存在性和可解析性。
2. 确认第 1 集正式 Script、Memory、Writer Brief、QC 报告是否存在。
3. 确认第 2 集 Script、Memory、Writer Brief、QC 报告是否存在，并对对应 JSON 子树计算稳定 SHA-256；缺失项记为 `absent`。
4. 确认 Showrunner 来源哈希存在、Episode Plan 覆盖第 2 集。
5. 只读获取当前生效 Provider 与模型配置，不泄露任何密钥或完整 URL 凭据。
6. 查询前后记录 `data/app.db` 的长度、最后修改时间和 SHA-256，证明检查没有写库。

## Verification

```powershell
git diff --check
git diff --name-only -- app tests requirements.txt
```

只有全部前置条件齐全、数据库查询前后指纹一致，才可记录 `completed` 并继续 B；否则记录 `blocked` 并停止批次。

