# 后端 API

## 基本信息

- 开发环境基础地址：`http://127.0.0.1:8000/api/v1`
- 请求和响应格式：`application/json`
- Swagger UI：`http://127.0.0.1:8000/docs`
- OpenAPI JSON：`http://127.0.0.1:8000/openapi.json`
- 开发测试页：`http://127.0.0.1:8000/dev/testbench`

所有正式接口统一使用 `/api/v1`。旧的无版本路径暂时保留用于兼容，但不会显示在 OpenAPI 文档中，独立前端不应继续使用旧路径。
`/dev/testbench` 仅用于本地开发验证，不属于正式 API，也不会显示在 OpenAPI 文档中。该页面可通过开发辅助接口读取本地历史项目、已保存大纲、角色圣经、多集剧本和 Story Memory，用于人工检查工作流输出；也可以对当前已保存剧本触发一次 LLM QC v1，返回结构化质检报告但不修改剧本。
开发环境会为每个 HTTP 请求返回 `X-Request-ID` 响应头，并写入本地结构化 JSONL 日志。日志默认路径为 `logs/app.jsonl`，可通过 `.env` 中的 `LOG_FILE_PATH` 覆盖。

## 错误格式

后端主动返回的业务错误使用：

```json
{
  "detail": "Project not found"
}
```

请求参数未通过 Pydantic 校验时返回 FastAPI 标准 `422` JSON，其中 `detail` 为校验问题数组。服务端不会向前端返回 API Key、上游原始响应或异常调用栈。

常见状态码：

- `404`：资源不存在
- `409`：业务前置状态不满足
- `422`：请求参数错误
- `500`：数据库或服务器内部错误
- `502`：LLM 调用、JSON 解析或 Schema 校验失败
- `503`：LLM Provider 或 API Key 配置不可用

## 健康检查

### `GET /api/v1/health`

请求示例：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/health"
```

响应示例：

```json
{
  "status": "ok"
}
```

## 创建项目

### `POST /api/v1/projects`

请求示例：

```json
{
  "name": "逆袭程序员"
}
```

响应：`201 Created`

```json
{
  "id": 1,
  "name": "逆袭程序员",
  "status": "draft",
  "created_at": "2026-07-22T10:00:00",
  "updated_at": "2026-07-22T10:00:00"
}
```

`name` 会去除首尾空格，长度必须为 1 到 200 个字符，额外字段会返回 `422`。

## 查询项目

### `GET /api/v1/projects/{project_id}`

请求示例：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/projects/1"
```

响应示例：

```json
{
  "id": 1,
  "name": "逆袭程序员",
  "status": "outline_ready",
  "created_at": "2026-07-22T10:00:00",
  "updated_at": "2026-07-22T10:01:00"
}
```

项目不存在时返回 `404`。

## 生成故事大纲

### `POST /api/v1/projects/{project_id}/outline`

请求示例：

```json
{
  "idea": "一个被公司开除的程序员发现老板窃取了他的AI成果",
  "episode_count": 10
}
```

响应示例（角色和分集数组仅节选；实际为 3–6 个角色和正好 10 集）：

```json
{
  "project_id": 1,
  "status": "outline_ready",
  "outline": {
    "title": "逆光代码",
    "logline": "被开除的程序员发现老板窃取成果，决定夺回真相。",
    "genre": "都市悬疑",
    "tone": "紧张热血",
    "target_audience": "年轻职场观众",
    "world_setting": "当代中国人工智能创业公司。",
    "core_conflict": "程序员必须在资本封锁下证明成果归属。",
    "themes": ["职场正义", "技术伦理"],
    "characters": [
      {
        "character_id": "lin_feng",
        "name": "林峰",
        "role": "男主角",
        "age": "二十八岁",
        "appearance": "清瘦干练，常穿旧夹克。",
        "personality": "克制执着，善于推理。",
        "motivation": "夺回成果并证明清白。",
        "secret": "保留了算法最早的离线记录。"
      }
    ],
    "episodes": [
      {
        "episode_number": 1,
        "title": "突然解雇",
        "summary": "林峰被突然解雇，并发现自己的成果已被老板署名。",
        "main_conflict": "林峰试图取证，却被保安赶出公司。",
        "ending_hook": "他在旧电脑里发现一条来自内部的匿名警告。"
      }
    ]
  }
}
```

## 生成角色圣经

### `POST /api/v1/projects/{project_id}/characters/generate`

Character Agent 一次生成项目大纲中的全部主要角色，不会逐角色调用模型。重新生成会整体覆盖旧角色圣经。

请求示例：

```json
{}
```

响应示例（仅展示一个角色；实际返回与大纲完全一致的 3–6 个角色）：

```json
{
  "project_id": 1,
  "status": "characters_ready",
  "characters": {
    "lin_feng": {
      "character_id": "lin_feng",
      "name": "林峰",
      "role": "男主角",
      "age": "二十八岁",
      "background": "曾是人工智能公司的核心程序员，因拒绝配合数据造假而被排挤。",
      "appearance": "清瘦干练，眼神克制，常保持警觉。",
      "personality": "冷静执着，习惯用证据而不是情绪做判断。",
      "motivation": "夺回被窃取的成果并证明清白。",
      "fear": "害怕证据消失后再也无人能够证明真相。",
      "secret": "保留了算法最早的离线记录。",
      "speech_style": "句子短而直接，极少使用夸张表达。",
      "behavior_patterns": ["进入陌生环境时先观察出口和监控位置。"],
      "emotional_triggers": ["发现技术成果被篡改时会明显愤怒。"],
      "behavior_boundaries": ["不会伪造证据，也不会主动伤害无辜者。"],
      "relationships": [
        {
          "target_character_id": "su_yan",
          "relationship_type": "调查盟友",
          "public_attitude": "保持专业距离，不轻易表达信任。",
          "private_attitude": "认可她的正直，但担心把她卷入危险。",
          "conflict": "林峰重视证据安全，苏妍更愿意立即公开真相。"
        }
      ],
      "character_arc": "从独自承担一切，逐渐学会信任同伴并公开面对过去。",
      "visual_identity": {
        "face_features": "面部线条清晰，眼下有轻微疲态。",
        "hair": "黑色短发，日常整理简单。",
        "body_type": "清瘦匀称，动作快速克制。",
        "default_costume": "深色旧夹克搭配简单衬衫。",
        "signature_colors": "深蓝、灰黑。",
        "signature_props": "左手佩戴一块旧机械表。"
      },
      "continuity_rules": {
        "must_keep": ["始终使用冷静克制的表达方式。"],
        "must_avoid": ["不使用网络流行语。"]
      }
    }
  }
}
```

错误状态：项目不存在返回 `404`；项目无有效大纲返回 `409`；LLM 调用或输出无效返回 `502`；Provider 配置不可用返回 `503`。

## 查询角色圣经

### `GET /api/v1/projects/{project_id}/characters`

请求示例：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/projects/1/characters"
```

成功响应结构与“生成角色圣经”的响应示例相同。项目或角色圣经不存在返回 `404`，项目无有效大纲返回 `409`。

## 整体替换角色圣经

### `PUT /api/v1/projects/{project_id}/characters`

请求体必须提交完整 `characters` 对象，结构与生成接口响应中的 `characters` 字段一致：

```json
{
  "characters": {
    "lin_feng": {
      "character_id": "lin_feng",
      "name": "林峰",
      "role": "男主角",
      "age": "二十八岁",
      "background": "人工智能公司的前核心程序员。",
      "appearance": "清瘦干练，眼神克制。",
      "personality": "冷静执着，重视证据。",
      "motivation": "夺回成果并证明清白。",
      "fear": "害怕真相被永久掩盖。",
      "secret": "保留了算法最早的离线记录。",
      "speech_style": "说话简短冷静，不使用网络流行语。",
      "behavior_patterns": ["行动前先确认关键证据。"],
      "emotional_triggers": ["证据遭到恶意销毁。"],
      "behavior_boundaries": ["不会伪造证据。"],
      "relationships": [
        {
          "target_character_id": "su_yan",
          "relationship_type": "调查盟友",
          "public_attitude": "保持专业距离。",
          "private_attitude": "逐渐建立信任。",
          "conflict": "对公开证据的时机存在分歧。"
        }
      ],
      "character_arc": "逐渐学会信任同伴。",
      "visual_identity": {
        "face_features": "面部线条清晰。",
        "hair": "黑色短发。",
        "body_type": "清瘦匀称。",
        "default_costume": "深色旧夹克。",
        "signature_colors": "深蓝、灰黑。",
        "signature_props": "左手佩戴旧机械表。"
      },
      "continuity_rules": {
        "must_keep": ["保持冷静克制。"],
        "must_avoid": ["不使用网络流行语。"]
      }
    }
  }
}
```

实际请求必须包含大纲中的全部角色；上例为单角色结构节选。成功响应结构与生成接口相同。角色 ID 集合、身份字段或关系引用不合法时返回 `422`。

## 生成并保存单集剧本

### `POST /api/v1/projects/{project_id}/episodes/{episode_number}/script`

请求示例：

```json
{
  "target_duration_seconds": 90,
  "use_showrunner_brief": false,
  "run_showrunner_qc": false,
  "max_revision_attempts": 0
}
```

响应示例（`scenes` 仅节选；实际包含 3–8 场）：

```json
{
  "project_id": 1,
  "episode_number": 1,
  "status": "script_ready",
  "script": {
    "episode_number": 1,
    "title": "AI证据争夺战",
    "duration_seconds": 90,
    "episode_goal": "林峰必须抢在高启之前取得服务器证据。",
    "opening_hook": "林峰的电脑突然开始远程自毁。",
    "scenes": [
      {
        "scene_number": 1,
        "location": "人工智能公司机房",
        "time_of_day": "深夜",
        "characters": ["lin_feng"],
        "scene_goal": "林峰发现服务器正在销毁证据。",
        "action": "红色警报闪烁，林峰冲到服务器前插入硬盘。",
        "dialogues": [
          {
            "character_id": "lin_feng",
            "character_name": "林峰",
            "emotion": "急促",
            "line": "只剩十秒，必须拿到证据！",
            "action_note": "手指飞快敲击键盘。"
          }
        ],
        "transition": "画面切向不断缩短的倒计时。"
      }
    ],
    "ending_hook": "硬盘上的定位灯突然亮起。"
  }
}
```

项目必须已有有效大纲；同一集重新生成会覆盖该集旧剧本，不影响其他集。`use_showrunner_brief` 默认为 `false`，保持旧流程；设置为 `true` 时，系统会读取已保存的当前集 Writer Brief 并传给 Writer Agent，Brief 不存在时返回错误，不会自动生成 Brief。

`run_showrunner_qc` 默认为 `false`；设置为 `true` 时，系统先执行规则型 QC，再执行 LLM Showrunner QC，最后确定性校验正式记忆证据和跨集连续性合同。只有最终 `status=pass`，且 `approved_memory` 每条事实都由 `memory_evidence` 定位到实际场景原文、`continuity_contract` 每项都存在有效 `continuity_resolutions` 时，才保存正式剧本并更新 Story Memory v2。`warning`、`fail` 或证据校验失败都不写入正式剧本和 Story Memory。

调用 LLM QC 前，后端会从当前 draft 的场景动作、对白、动作提示和转场生成内部 `evidence_catalog`，并从最后一场生成 `ending_state_reference`。这些字段只作为模型输入，不改变本接口请求或响应结构。QC 的记忆证据和合同处理证据必须完整复制清单中的场号和原文，正式记忆的最后地点和时间必须复制权威引用。后端会移除不对应正式记忆路径的辅助证据以及完全相同的重复证据，但仍拒绝缺失或冲突的必需证据，并继续逐字校验，不进行模糊匹配。

QC 报告通过后（`status=pass` 且集号小于 10），后端还会确定性补全缺失的连续性义务：若某个 `unresolved_questions.N` 没有对应义务，后端按精确 `source_memory_path` 补一条义务（到期集为当前集加 1），并逐字复用该问题的 `memory_evidence`（场号和场景原文）生成 `continuity_obligations.{index}` 证据；已有合法义务原样保留、同一来源不重复、重复调用幂等。第 10 集不生成下一集义务或义务证据。该过程不新增 LLM 调用、不改变本接口的请求或响应结构，QC 未通过前仍不写入正式 Story Memory。

模型在 `continuity_resolutions` 中使用已知的状态或证据字段别名时，后端会在 Schema 边界归一化；已知但不参与正式结果的 `kind`、`resolution_notes` 会被移除，接口始终以标准的 `obligation_id`、`status`、`scene_number`、`evidence_text` 响应和保存。后端不会推断缺失的场号或证据；别名互相冲突、字段缺失、其他未知额外字段或错误嵌套类型仍按结构响应无效处理。

`max_revision_attempts` 默认为 `0`，范围为 `0–2`，只有 `run_showrunner_qc=true` 时可用。大于 `0` 时，系统把 QC 问题作为 `revision_feedback` 交给 Writer 重新生成，直到通过或达到上限。多次返修会累积并去重此前全部问题，避免修复新问题时重新引入旧错误。被拒绝的 draft 不保存正文；每次尝试只在结构化日志中记录尝试序号、状态和安全问题码。Showrunner State 只保存该集最近一次 QC 报告。

常见错误：

- `404`：项目不存在
- `404`：分集不存在
- `404`：`use_showrunner_brief=true` 但 Showrunner State 尚未生成
- `404`：`use_showrunner_brief=true` 但该集 Writer Brief 尚未生成
- `409`：项目大纲尚未就绪
- `409`：`run_showrunner_qc=true` 但未开启 `use_showrunner_brief`
- `409`：Showrunner QC 未通过，draft 未保存
- `422`：请求参数错误，例如返修次数超过 2，或未启用 QC 却请求自动返修
- `502`：LLM 调用、JSON/Schema 校验失败，或 QC 在一次重答后仍无法提供有效场景证据
- `503`：LLM Provider 或 API Key 配置不可用

## 生成 Showrunner State

### `POST /api/v1/projects/{project_id}/showrunner`

Showrunner Agent 根据当前项目已保存的大纲和角色圣经生成整季总控状态。该接口本身只生成 Story Bible、Episode Plan 和 Character Arc；Writer Brief 和 QC 报告由对应的分集接口按需生成并写回该状态。

请求体：

```json
{}
```

也可以显式提交：

```json
{
  "force_regenerate": false
}
```

当前 `force_regenerate` 为预留字段；调用生成接口会以当前大纲和角色圣经重新生成并覆盖 `showrunner_json`，同时将预留的 `writer_briefs` 和 `qc_reports` 初始化为空对象。

响应示例（数组仅节选；实际 `episode_plan` 为 10 集，每个角色的 `episode_beats` 只记录稀疏关键转折，Prompt 目标通常为 2–4 项）：

```json
{
  "project_id": 1,
  "showrunner": {
    "version": "showrunner_v1",
    "source_outline_hash": "64位sha256字符串",
    "source_characters_hash": "64位sha256字符串",
    "story_bible": {
      "series_title": "逆光代码",
      "logline": "被开除的程序员发现老板窃取成果，决定夺回真相。",
      "genre": "都市悬疑",
      "tone": "紧张热血",
      "world_rules": ["故事发生在当代中国人工智能创业语境中。"],
      "canon_facts": ["林峰被开除后发现老板窃取了他的AI成果。"],
      "core_conflict": "程序员必须在资本封锁下证明成果归属。",
      "main_mysteries": ["关键证据为何被持续销毁。"],
      "forbidden_reveals": ["不得在前期提前确认最终证据结果。"],
      "continuity_rules": ["每集只能展开该集大纲范围内的核心事件。"]
    },
    "episode_plan": [
      {
        "episode_number": 1,
        "title": "突然解雇",
        "dramatic_function": "建立主角危机和整季追证目标。",
        "must_include": ["林峰发现自己的成果被老板署名。"],
        "must_not_reveal": ["不得确认最终证据结果。"],
        "setup": ["旧电脑中出现匿名警告。"],
        "payoff": ["林峰确认成果归属被篡改。"],
        "ending_hook": "他在旧电脑里发现一条来自内部的匿名警告。",
        "allowed_new_facts": ["林峰被开除。"]
      }
    ],
    "character_arcs": [
      {
        "character_id": "lin_feng",
        "character_name": "林峰",
        "starting_state": "被动遭遇背叛，独自追查。",
        "ending_state": "学会信任盟友并公开面对真相。",
        "episode_beats": [
          {
            "episode_number": 1,
            "emotional_state": "震惊但克制",
            "goal": "确认成果是否被窃取。",
            "change": "从被动失业转为主动取证。",
            "knowledge_state": "知道成果署名异常，但不知道完整幕后链条。"
          }
        ]
      }
    ],
    "writer_briefs": {},
    "qc_reports": {}
  }
}
```

哈希说明：`source_outline_hash` 和 `source_characters_hash` 由服务端基于稳定排序后的 JSON 内容计算 SHA-256，不使用 Python 内置 `hash()`。

`episode_beats` 是稀疏关键转折，不要求每集都有一项；字段保留以兼容旧状态。旧的 10 集完整 beat 数据仍可读取。生成 Writer Brief 时，如果当前集没有专属 beat，系统会提供此前最近转折、下一次未来转折以及角色整季起止状态，由模型结合当前集 Episode Plan 推导本集状态；未来转折只作为边界，不会被视为已发生事实。

`must_not_reveal` 在第 1–9 集用于记录不能提前揭示的后续内容；第 10 集没有后续剧情边界时允许为空数组。

常见错误：

- `404`：项目不存在
- `409`：项目大纲尚未就绪
- `409`：角色圣经尚未就绪
- `502`：LLM 调用、JSON 解析或 Schema 校验失败
- `503`：LLM Provider 或 API Key 配置不可用

## 查询 Showrunner State

### `GET /api/v1/projects/{project_id}/showrunner`

请求示例：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/projects/1/showrunner"
```

成功响应结构与“生成 Showrunner State”的响应示例相同。

常见错误：

- `404`：项目不存在
- `404`：Showrunner State 尚未生成

## 生成 Writer Brief

### `POST /api/v1/projects/{project_id}/episodes/{episode_number}/writer-brief`

Showrunner Agent 根据已保存的 Showrunner State、指定集 Episode Plan、角色弧线和 Story Memory，为第 N 集生成并保存写作 Brief。生成剧本时可用 `use_showrunner_brief=true` 将该 Brief 交给 Writer，并可同时开启 Showrunner QC。

请求示例：

```json
{
  "target_duration_seconds": 90,
  "force_regenerate": false
}
```

当前 `force_regenerate` 为预留字段；调用生成接口会重新生成并覆盖当前集 Brief，不影响其他集 Brief。

响应示例：

```json
{
  "project_id": 1,
  "episode_number": 1,
  "brief": {
    "episode_number": 1,
    "episode_goal": "第1集必须建立林峰被夺走成果后的追证目标。",
    "allowed_scope": ["只展开第1集大纲中的失业、发现署名异常和初步取证。"],
    "required_beats": [
      "林峰确认成果被老板署名。",
      "林峰遭遇第一次取证阻碍。",
      "结尾出现匿名警告。"
    ],
    "forbidden_content": ["不得确认最终证据结果。"],
    "character_states": [
      {
        "character_id": "lin_feng",
        "character_name": "林峰",
        "current_goal": "确认成果是否被窃取。",
        "emotional_state": "震惊但克制",
        "knows": ["知道自己被突然解雇。"],
        "must_not_know": ["不知道完整幕后链条。"]
      }
    ],
    "continuity_context": ["只能承接此前正式剧本中已经发生的事实。"],
    "continuity_contract": null,
    "props_and_evidence": ["旧电脑、服务器记录可以作为线索。"],
    "ending_requirement": "结尾制造下一步追查悬念，但不得解答下一集核心问题。",
    "target_duration_seconds": 90
  }
}
```

常见错误：

- `404`：项目不存在
- `404`：Showrunner State 尚未生成
- `404`：Showrunner Episode Plan 中不存在该集
- `422`：请求参数错误，例如目标时长不在允许范围
- `502`：LLM 调用、JSON 解析或 Schema 校验失败
- `503`：LLM Provider 或 API Key 配置不可用

## 查询 Writer Brief

### `GET /api/v1/projects/{project_id}/episodes/{episode_number}/writer-brief`

请求示例：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/projects/1/episodes/1/writer-brief"
```

成功响应结构与“生成 Writer Brief”的响应示例相同。

角色状态中的 `knows` 和 `must_not_know` 只记录有明确依据的认知边界；确实没有相应信息时允许为空数组，系统不会要求模型编造占位事实。

`continuity_context` 只允许引用正式 Story Memory；第 1 集或没有可承接事实时允许为空数组。

`continuity_contract` 由服务端在 Brief 保存前根据上一集 `source=qc_approved` 的正式 Story Memory 生成，LLM 输出不能覆盖。第 1 集、上一集只有兼容性的 `source=rule_extracted` 记忆，或上一集没有正式 `ending_state` 时为 `null`；否则结构如下：

```json
{
  "previous_episode_number": 1,
  "previous_ending_state": {
    "location": "人工智能公司机房",
    "time_of_day": "深夜",
    "situation": "林峰看到文件中出现苏妍父亲的名字。"
  },
  "must_continue": [
    {
      "obligation_id": "episode_1_ending_state",
      "kind": "ending_state",
      "description": "承接上一集末场地点、时间和人物处境。",
      "source_episode_number": 1,
      "due_episode_number": 2,
      "source_memory_path": "ending_state"
    }
  ]
}
```

`kind=ending_state` 的事项必须在当前集第一场承接。上一集 QC 保存的其他到期 `continuity_obligations` 也会出现在 `must_continue`。

常见错误：

- `404`：项目不存在
- `404`：Showrunner State 尚未生成
- `404`：Showrunner Episode Plan 中不存在该集
- `404`：该集 Writer Brief 尚未生成

## 查询 Showrunner QC 报告

### `GET /api/v1/projects/{project_id}/episodes/{episode_number}/showrunner-qc`

查询最近一次由 `run_showrunner_qc=true` 的剧本生成流程保存的 Showrunner QC 报告。该接口只读，不触发新的 LLM 调用。

请求示例：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/projects/1/episodes/1/showrunner-qc"
```

响应示例：

```json
{
  "project_id": 1,
  "episode_number": 1,
  "report": {
    "episode_number": 1,
    "status": "fail",
    "summary": "剧本提前揭示了后续集才应确认的关键答案。",
    "issues": [
      {
        "episode_number": 1,
        "severity": "error",
        "code": "future_reveal",
        "message": "草稿提前确认最终证据结果，违反本集 Brief。",
        "suggestion": "删除最终答案，只保留触发下一步追查的悬念。"
      }
    ],
    "approved_memory": null,
    "memory_evidence": [],
    "continuity_resolutions": []
  }
}
```

QC 通过时 `issues` 为空，`approved_memory` 包含从实际场景审核得到的本集事实、人物认知、道具状态、末场状态和下一集到期的 `continuity_obligations`，其 `source` 固定为 `qc_approved`。`memory_evidence` 中每个 `memory_path` 必须恰好覆盖一条可持久化事实，`evidence_text` 必须能在指定场景的动作、对白、动作提示或转场中逐字找到。当 Brief 中存在 `continuity_contract` 时，`continuity_resolutions` 必须逐条标记 `resolved` 或 `carried_forward` 并提供场景证据；带到下一集的事项还必须继续写入本集 `approved_memory.continuity_obligations`。`warning` 或 `fail` 时 `approved_memory` 为 `null`。

QC 通过报告中的新增结构示例：

```json
{
  "approved_memory": {
    "episode_number": 2,
    "source": "qc_approved",
    "summary": "林峰承接机房危机并追查异常名字。",
    "new_facts": ["林峰开始追查异常名字。"],
    "revealed_secrets": [],
    "unresolved_questions": [],
    "character_updates": {},
    "props_and_evidence": [],
    "ending_state": {
      "location": "人工智能公司机房",
      "time_of_day": "深夜",
      "situation": "林峰锁定下一步调查方向。"
    },
    "ending_hook": "新的调查方向指向谁。",
    "continuity_obligations": []
  },
  "memory_evidence": [
    {
      "memory_path": "new_facts.0",
      "scene_number": 1,
      "evidence_text": "我现在就查这个名字"
    }
  ],
  "continuity_resolutions": [
    {
      "obligation_id": "episode_1_ending_state",
      "status": "resolved",
      "scene_number": 1,
      "evidence_text": "屏幕上的名字还在闪烁"
    }
  ]
}
```

上例只展示新增字段关系；真实 `memory_evidence` 会同时覆盖 `summary`、`ending_state`、`ending_hook` 等全部必需路径。

常见错误：

- `404`：项目不存在
- `404`：Showrunner State 尚未生成
- `404`：Showrunner Episode Plan 中不存在该集
- `404`：该集 Showrunner QC 报告尚未生成

## 查询已保存的单集剧本

### `GET /api/v1/projects/{project_id}/episodes/{episode_number}/script`

请求示例：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/projects/1/episodes/1/script"
```

成功响应与生成剧本接口的响应结构相同。项目、分集或剧本不存在时返回 `404`；项目没有有效大纲时返回 `409`。

## 开发辅助：LLM QC v1

以下接口只服务 `/dev/testbench` 本地验证，不属于正式 `/api/v1`，不会显示在 OpenAPI 文档中，独立前端不应依赖它作为产品接口。

### `POST /dev/projects/{project_id}/episodes/{episode_number}/qc`

对当前项目已保存的第 N 集剧本执行一次 LLM QC v1。该接口只返回结构化质检报告，不自动改写剧本、不覆盖 `scripts_json`，也不持久化 QC 结果。

请求体：无。

请求示例：

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/dev/projects/1/episodes/1/qc"
```

响应示例：

```json
{
  "project_id": 1,
  "episode_number": 1,
  "report": {
    "episode_number": 1,
    "status": "warning",
    "summary": "整体可用，但存在一个可能提前展开后续线索的问题。",
    "issues": [
      {
        "episode_number": 1,
        "severity": "warning",
        "code": "future_boundary_risk",
        "message": "剧本结尾可能提前揭示后续集才应确认的关键证据结果。",
        "suggestion": "保留发现证据的悬念，不要在本集确认最终结论。"
      }
    ]
  }
}
```

常见错误：

- `404`：项目、分集或已保存剧本不存在
- `409`：项目大纲尚未就绪
- `502`：LLM 调用、JSON 解析或 Schema 校验失败
- `503`：LLM Provider 或 API Key 配置不可用

## 开发辅助：查询结构化日志

以下接口只服务本地开发排查，不属于正式 `/api/v1`，不会显示在 OpenAPI 文档中。

### `GET /dev/logs`

读取最近的本地 JSONL 日志。日志只记录请求和工作流元数据，例如 `event`、`request_id`、`project_id`、`episode_number`、状态码、耗时和安全的失败原因码；不会记录 API Key、完整 Prompt 或完整剧本正文。

查询参数：

- `project_id`：可选，只返回指定项目相关日志
- `limit`：可选，默认 `200`，范围 `1–1000`

请求示例：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/dev/logs?project_id=1&limit=50"
```

响应示例：

```json
{
  "logs": [
    {
      "timestamp": "2026-07-30T10:00:00.000000+00:00",
      "level": "info",
      "logger": "ai_short_drama",
      "request_id": "manual-request-id",
      "event": "workflow.script.saved",
      "project_id": 1,
      "episode_number": 1,
      "status": "script_ready"
    }
  ]
}
```

## 当前未提供的接口

当前业务尚未实现项目列表、项目更新、项目删除、Storyboard、视频生成和任务队列，因此 `/api/v1` 不提供这些接口。Phase 3-1 只完成了内部 Video Provider 抽象接口和 Fake Provider，不新增正式 HTTP API。
