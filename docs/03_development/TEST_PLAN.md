# 测试方案

## 功能测试

创建项目

生成剧情

生成角色

生成分镜

生成视频

## Phase 2B 自动测试

- 单集剧本生成、集号一致和场次连续
- 剧本角色 ID 只能来自整体大纲
- 成功后状态为 `script_ready` 并保存至 `scripts_json`
- 同集重新生成仅覆盖该集，生成其他集不覆盖已保存剧本
- 项目、大纲、分集、Provider 和 Schema 错误状态映射
- pytest 使用 FakeLLMProvider 和临时 SQLite，不调用真实 DeepSeek、不污染正式 `app.db`

## Phase 2C 自动测试

- 角色数量、ID 集合及姓名/年龄/定位与大纲完全一致
- 关系引用合法、不允许自引用，严格禁止额外字段
- 角色圣经生成、`characters_json` 保存、查询和整体替换
- 项目、大纲、Provider、模型输出和用户输入错误状态映射
- Writer 优先读取角色圣经，无角色圣经时保持大纲角色回退
- 已有 SQLite 项目表可幂等增加 `characters_json` 列
- pytest 使用 FakeLLMProvider 和临时 SQLite，不调用真实 DeepSeek、不污染正式 `data/app.db`


## 集成测试

完整流程：

输入故事

输出MP4


## 性能测试

记录：

生成时间

失败率

成本

有效镜头比例
