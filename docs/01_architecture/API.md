# 后端 API

## 基本信息

- 开发环境基础地址：`http://127.0.0.1:8000/api/v1`
- 请求和响应格式：`application/json`
- Swagger UI：`http://127.0.0.1:8000/docs`
- OpenAPI JSON：`http://127.0.0.1:8000/openapi.json`

所有正式接口统一使用 `/api/v1`。旧的无版本路径暂时保留用于兼容，但不会显示在 OpenAPI 文档中，独立前端不应继续使用旧路径。

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
  "target_duration_seconds": 90
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

项目必须已有有效大纲；同一集重新生成会覆盖该集旧剧本，不影响其他集。

## 查询已保存的单集剧本

### `GET /api/v1/projects/{project_id}/episodes/{episode_number}/script`

请求示例：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/projects/1/episodes/1/script"
```

成功响应与生成剧本接口的响应结构相同。项目、分集或剧本不存在时返回 `404`；项目没有有效大纲时返回 `409`。

## 当前未提供的接口

当前业务尚未实现项目列表、项目更新、项目删除、Storyboard、视频生成和任务队列，因此 `/api/v1` 不提供这些接口。
