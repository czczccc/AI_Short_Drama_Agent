# Implementation Plan: Phase 2C Character Agent

## Overview

将 `StoryOutline.characters` 深化为项目级角色圣经，保存到 `Project.characters_json`，提供生成、查询和整体替换 API，并让 Writer 在角色圣经存在时优先使用，不存在时保持兼容。

## Architecture Decisions

- 一次 LLM 调用生成当前项目全部角色，保证人物关系一致并控制费用。
- 使用 `characters_json` 保存以 `character_id` 为键的对象，不创建 Character 表。
- Character Bible 经过结构校验和大纲上下文二次校验后才能保存。
- PUT 采用整体替换；用户输入无效返回 `422`，模型输出无效返回 `502`。
- 为已有 SQLite 项目库增加最小列升级逻辑，不引入迁移框架。

## Task List

### Foundation

- [x] 定义 Character Bible Schema 与跨角色校验
- [x] 给 Project 增加 `characters_json` 并兼容升级已有 SQLite

### Character Workflow

- [x] 实现 Character Agent 和 `character_v1.md`
- [x] 实现生成、查询、整体替换 Service/API
- [x] 使用 FakeLLMProvider 覆盖成功与失败路径

### Writer Integration

- [x] 有角色圣经时 Writer 优先使用
- [x] 无角色圣经时继续使用大纲角色概念

### Completion

- [x] 更新 API、数据模型、Prompt、工作流、任务和测试文档
- [x] 全量测试通过且正式数据库不被 pytest 污染
- [x] 有有效 Key 时仅真实生成一次角色圣经

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| 模型新增、遗漏或篡改角色 | 高 | 使用大纲上下文做 ID 集合及姓名/年龄/定位二次校验 |
| 非法或自引用关系 | 高 | Collection `model_validator` 统一校验 |
| 旧 SQLite 缺少新列 | 高 | 启动时只对 SQLite 执行幂等列检查与添加 |
| Writer 集成破坏旧项目 | 高 | `characters_json` 缺失时保留现有角色概念输入 |

## Open Questions

- 无阻塞问题；字段类型按确认后的实现假设落地。
