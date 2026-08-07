# 前端接口速查（精简版）

> 给前端开发者：按页面/操作组织，聚焦你需要知道的字段和调用顺序。
> 完整契约见 [API.md](./API.md)，流程导航见 [API_FLOW_MAP.md](./API_FLOW_MAP.md)。

## 0. 基础信息

- **Base URL**：`http://127.0.0.1:8000`（生产按部署环境替换）
- **API 前缀**：`/api/v1`
- **Swagger 自文档**：`GET /docs`（联调时实时可查）
- **CORS**：已允许 `localhost:3000 / localhost:5173`（前端开发服务器默认端口可直接调）
- **数据格式**：全部 JSON；请求/响应字段名用 `snake_case`

### 通用错误格式

```json
{ "detail": "错误信息" }
```

### 常见状态码

| 码 | 含义 | 前端处理 |
|---|---|---|
| `404` | 资源不存在 / 前置未生成 | 提示"请先完成上一步" |
| `409` | 业务前置状态不满足 / QC 未通过 | 显示 QC 报告中的问题列表 |
| `422` | 请求参数错误 | 提示参数问题 |
| `500` | 服务器内部错误 | 通用错误提示 |
| `502` | LLM 调用/解析失败 | 提示"生成失败，请重试"（可自动重试一次） |
| `503` | LLM Provider 或 Key 不可用 | 提示"服务未配置好" |

---

## 1. 项目状态机（前端页面编排依据）

```
draft → outline_ready → characters_ready → script_ready
```

- 项目状态决定哪些按钮可用（下一步没解锁就禁用）
- 生成剧本的集号范围：`1 ~ 10`

---

## 2. 页面 A：创建/选择项目

### 创建项目
`POST /api/v1/projects`

```json
{ "name": "我的短剧" }
```

响应：
```json
{ "id": 1, "name": "我的短剧", "status": "draft", "created_at": "...", "updated_at": "..." }
```

### 查询项目
`GET /api/v1/projects/{project_id}`

响应（含全部生成内容，JSON 字符串字段）：
```json
{
  "id": 1, "name": "我的短剧", "status": "script_ready",
  "outline_json": null, "characters_json": null,
  "showrunner_json": null, "scripts_json": null, "memory_json": null
}
```

> **前端注意**：5 个 `*_json` 是 JSON 字符串，需 `JSON.parse` 后再用。

---

## 3. 页面 B：生成大纲

`POST /api/v1/projects/{project_id}/outline`

```json
{ "idea": "一个程序员被公司陷害后逆袭创业", "episode_count": 10 }
```

- `episode_count` 固定 10（后端约束 ≥10）
- 耗时：约 15~60s（LLM 调用），需要 loading
- 响应含 `outline_json`；查询大纲：`GET /api/v1/projects/{project_id}/outline`

---

## 4. 页面 C：生成角色圣经

`POST /api/v1/projects/{project_id}/characters/generate`

- 无请求体；耗时约 20~60s
- 查询：`GET /api/v1/projects/{project_id}/characters`
- 整体替换：`PUT /api/v1/projects/{project_id}/characters`（body 为完整角色集合）

---

## 5. 页面 D：生成 Showrunner State（可选步骤）

`POST /api/v1/projects/{project_id}/showrunner`

- 无请求体；生成整季规划（story bible + 10 集 plan + 角色弧）
- 查询：`GET /api/v1/projects/{project_id}/showrunner`
- **前端**：这步可跳过（生成剧本不强制），但做了会提升后续剧本质量

---

## 6. 页面 E：生成剧本（核心，逐集操作）

### 第 1 步：生成 Writer Brief（本集任务书）
`POST /api/v1/projects/{project_id}/episodes/{episode_number}/writer-brief`

- 无请求体；耗时约 5~30s
- 查询：`GET /api/v1/projects/{project_id}/episodes/{episode_number}/writer-brief`

### 第 2 步：生成剧本
`POST /api/v1/projects/{project_id}/episodes/{episode_number}/script`

```json
{
  "target_duration_seconds": 90,
  "use_showrunner_brief": true,
  "run_showrunner_qc": true,
  "max_revision_attempts": 2
}
```

| 参数 | 默认 | 说明 |
|---|---|---|
| `target_duration_seconds` | 90 | 目标时长（60-180） |
| `use_showrunner_brief` | false | true=用已保存的 Brief；未生成 Brief 会 404 |
| `run_showrunner_qc` | false | true=启用完整质检（规则 QC + LLM QC + 证据门禁） |
| `max_revision_attempts` | 0 | QC 不过时自动返修次数（0-2；**仅当 run_showrunner_qc=true**） |

> **前端注意**：
> - 耗时 30~120s，必须做 loading/进度提示，**不能按普通请求超时处理**（建议 180s+ 超时）
> - 同一集重复调用会**覆盖**旧剧本，不影响其他集
> - `run_showrunner_qc=true` 时：`pass` 才落库；`warning`/`fail` 会返回 409
> - 409 时 body 里有 QC 报告，可展示问题列表让用户知道为什么失败

### 查询已保存剧本
`GET /api/v1/projects/{project_id}/episodes/{episode_number}/script`

响应（剧本结构）：
```json
{
  "episode_number": 1, "title": "第1集标题", "duration_seconds": 90,
  "episode_goal": "本集目标", "opening_hook": "开场钩子",
  "scenes": [
    {
      "scene_number": 1, "location": "场景地点", "time_of_day": "深夜",
      "characters": ["角色id"], "scene_goal": "场景目标",
      "action": "舞台动作描述",
      "dialogues": [
        { "character_id": "角色id", "character_name": "角色名",
          "emotion": "情绪", "line": "台词", "action_note": "动作备注" }
      ],
      "transition": "转场"
    }
  ],
  "ending_hook": "结尾钩子"
}
```

---

## 7. 页面 F：查看 QC 报告

`GET /api/v1/projects/{project_id}/episodes/{episode_number}/showrunner-qc`

- 只读，不触发 LLM
- 响应：
```json
{
  "project_id": 1, "episode_number": 1,
  "report": {
    "status": "pass", "summary": "总结",
    "issues": [
      { "episode_number": 1, "severity": "error|warning",
        "code": "future_reveal", "message": "问题描述", "suggestion": "修改建议" }
    ]
  }
}
```

- `status`：`pass` / `warning` / `fail`
- `issues[].severity`：`error`（必须改）/ `warning`（建议改）

---

## 8. 推荐调用流程（前端完整演示）

```
1. POST /projects                    → 创建项目，拿 id
2. POST /projects/{id}/outline       → 生成大纲（loading）
3. POST /projects/{id}/characters/generate → 生成角色（loading）
4. （可选）POST /projects/{id}/showrunner → 整季规划（loading）
5. 循环 episode = 1..10：
   a. POST /projects/{id}/episodes/{ep}/writer-brief （loading）
   b. POST /projects/{id}/episodes/{ep}/script
      {"use_showrunner_brief": true, "run_showrunner_qc": true,
       "max_revision_attempts": 2}                     （loading，长）
   c. 失败（409/502）→ 提示 + 可选重试
6. GET /projects/{id} → 展示最终状态（status=script_ready）
```

---

## 9. 开发辅助接口（一般不需要前端调用）

- `GET /dev/logs`：结构化日志
- `POST /dev/projects/{id}/episodes/{n}/qc`：独立 QC（LLM QC v1）
- 这些带 `/dev` 前缀的接口 `include_in_schema=False`，Swagger 里不显示
