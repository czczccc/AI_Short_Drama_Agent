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
