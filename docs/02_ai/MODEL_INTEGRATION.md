# 模型接入规范

## LLM

职责：
- 剧本
- 分镜
- Prompt生成


## Video Provider

统一接口：

submit()

get_status()

download()

cancel()


## Provider模式

业务层不知道具体模型。

支持：

Seedance

Kling

Veo


## 必须记录

- 请求参数
- 返回结果
- 消耗
- 失败原因
