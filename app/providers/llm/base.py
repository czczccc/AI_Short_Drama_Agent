from typing import Protocol, TypeVar

from pydantic import BaseModel


SchemaT = TypeVar("SchemaT", bound=BaseModel)


class LLMProvider(Protocol):
    """业务层可依赖的最小结构化生成接口。"""

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: type[SchemaT],
    ) -> SchemaT: ...


class LLMProviderError(Exception):
    """Provider 边界内可安全分类的基础异常。"""


class LLMConfigurationError(LLMProviderError):
    """Provider 或凭据配置无效。"""


class LLMCallError(LLMProviderError):
    """远端 LLM 调用失败。"""


class LLMResponseJSONError(LLMProviderError):
    """LLM 响应不是合法 JSON。"""


class LLMResponseValidationError(LLMProviderError):
    """LLM 响应未通过输出 Schema 校验。"""
