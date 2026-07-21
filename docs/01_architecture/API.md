# API设计

POST /projects

创建项目


POST /projects/{project_id}/outline

生成大纲

请求：

```json
{
  "idea": "一个被公司开除的程序员发现老板窃取了他的AI成果",
  "episode_count": 10
}
```

成功响应结构节选（实际响应包含 3 到 6 个角色对象和正好 10 个分集对象）：

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

错误状态：

- `404`：项目不存在
- `422`：请求参数错误
- `502`：LLM 调用、JSON 解析或 Schema 校验失败
- `503`：Provider 或 API Key 配置不可用

错误响应只包含清理后的 `detail`，不返回凭据、请求头、原始响应、上游完整异常或调用栈。


POST /projects/{project_id}/episodes/{episode_number}/script

生成并保存指定单集剧本。

请求：

```json
{
  "target_duration_seconds": 90
}
```

成功响应结构节选：

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
    "scenes": [],
    "ending_hook": "硬盘上的定位灯突然亮起。"
  }
}
```

实际 `scenes` 包含 3 到 8 个完整 `SceneScript` 对象。

错误状态：

- `404`：项目或指定分集不存在
- `409`：项目尚无有效大纲
- `422`：目标时长等请求参数错误
- `502`：Provider 调用、JSON 解析或剧本 Schema 校验失败
- `503`：Provider 或 API Key 配置不可用


GET /projects/{project_id}/episodes/{episode_number}/script

查询已保存的指定单集剧本。项目或剧本不存在时返回 `404`，项目无有效大纲时返回 `409`。


POST /episodes/{id}/storyboard

生成分镜


POST /shots/{id}/generate

生成视频


GET /tasks/{id}

查询任务状态
