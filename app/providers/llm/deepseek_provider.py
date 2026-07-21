import json
import logging
from typing import Any

from openai import OpenAI
from pydantic import ValidationError

from app.providers.llm.base import (
    LLMCallError,
    LLMResponseJSONError,
    LLMResponseValidationError,
    SchemaT,
)


logger = logging.getLogger(__name__)


class DeepSeekProvider:
    """通过 OpenAI 兼容客户端调用 DeepSeek Chat Completions。"""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        timeout_seconds: float,
        max_tokens: int,
        thinking_enabled: bool,
        client: Any | None = None,
    ) -> None:
        self._model = model
        self._max_tokens = max_tokens
        self._thinking_enabled = thinking_enabled
        self._client = client or OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout_seconds,
        )

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: type[SchemaT],
    ) -> SchemaT:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=self._max_tokens,
                response_format={"type": "json_object"},
                extra_body={
                    "thinking": {
                        "type": "enabled" if self._thinking_enabled else "disabled"
                    }
                },
                stream=False,
            )
            content = response.choices[0].message.content
        except Exception as exc:
            raise LLMCallError("LLM 服务调用失败") from exc

        if not isinstance(content, str) or not content.strip():
            raise LLMResponseJSONError("LLM 返回了空内容")

        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise LLMResponseJSONError("LLM 返回内容不是合法 JSON") from exc

        try:
            return output_schema.model_validate(data)
        except ValidationError as exc:
            issues = [
                {
                    "location": ".".join(str(part) for part in error["loc"]),
                    "type": error["type"],
                }
                for error in exc.errors(
                    include_url=False,
                    include_context=False,
                    include_input=False,
                )
            ]
            logger.warning("LLM response schema validation failed: issues=%s", issues)
            raise LLMResponseValidationError("LLM 返回内容未通过结构校验") from exc
