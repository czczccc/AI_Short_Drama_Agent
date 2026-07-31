import json
import logging
import time
from typing import Any

from openai import OpenAI
from pydantic import ValidationError

from app.providers.llm.base import (
    LLMCallError,
    LLMResponseJSONError,
    LLMResponseValidationError,
    SchemaT,
)
from app.observability.logging import duration_ms, log_event


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
        structured_retry_count: int = 2,
    ) -> None:
        self._model = model
        self._max_tokens = max_tokens
        self._thinking_enabled = thinking_enabled
        self._structured_retry_count = structured_retry_count
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
        started_at = time.perf_counter()
        schema_name = output_schema.__name__
        current_user_prompt = user_prompt
        total_attempts = self._structured_retry_count + 1

        for attempt_number in range(1, total_attempts + 1):
            log_event(
                "llm.call.started",
                provider="deepseek",
                model=self._model,
                output_schema=schema_name,
                attempt_number=attempt_number,
                system_chars=len(system_prompt),
                user_chars=len(current_user_prompt),
                max_tokens=self._max_tokens,
                thinking_enabled=self._thinking_enabled,
            )
            try:
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": current_user_prompt},
                    ],
                    max_tokens=self._max_tokens,
                    response_format={"type": "json_object"},
                    extra_body={
                        "thinking": {
                            "type": (
                                "enabled" if self._thinking_enabled else "disabled"
                            )
                        }
                    },
                    stream=False,
                )
                content = response.choices[0].message.content
            except Exception as exc:
                log_event(
                    "llm.call.failed",
                    level="error",
                    provider="deepseek",
                    model=self._model,
                    output_schema=schema_name,
                    attempt_number=attempt_number,
                    failure_stage="remote_call",
                    error_type=type(exc).__name__,
                    duration_ms=duration_ms(started_at),
                )
                raise LLMCallError("LLM 服务调用失败") from exc

            if not isinstance(content, str) or not content.strip():
                issues = [{"location": "$", "type": "empty_response"}]
                if attempt_number < total_attempts:
                    current_user_prompt = self._build_repair_prompt(
                        user_prompt,
                        issues,
                    )
                    self._log_structured_retry(
                        schema_name=schema_name,
                        attempt_number=attempt_number,
                        failure_stage="empty_response",
                        issues=issues,
                    )
                    continue
                log_event(
                    "llm.call.failed",
                    level="error",
                    provider="deepseek",
                    model=self._model,
                    output_schema=schema_name,
                    attempt_number=attempt_number,
                    failure_stage="empty_response",
                    duration_ms=duration_ms(started_at),
                )
                raise LLMResponseJSONError("LLM 返回了空内容")

            try:
                data = json.loads(content)
            except json.JSONDecodeError as exc:
                issues = [{"location": "$", "type": "invalid_json"}]
                if attempt_number < total_attempts:
                    current_user_prompt = self._build_repair_prompt(
                        user_prompt,
                        issues,
                    )
                    self._log_structured_retry(
                        schema_name=schema_name,
                        attempt_number=attempt_number,
                        failure_stage="invalid_json",
                        issues=issues,
                    )
                    continue
                log_event(
                    "llm.call.failed",
                    level="error",
                    provider="deepseek",
                    model=self._model,
                    output_schema=schema_name,
                    attempt_number=attempt_number,
                    failure_stage="invalid_json",
                    response_chars=len(content),
                    duration_ms=duration_ms(started_at),
                )
                raise LLMResponseJSONError("LLM 返回内容不是合法 JSON") from exc

            try:
                result = output_schema.model_validate(data)
            except ValidationError as exc:
                issues = [
                    {
                        "location": ".".join(str(part) for part in error["loc"]),
                        "type": error["type"],
                        "message": error["msg"][:200],
                    }
                    for error in exc.errors(
                        include_url=False,
                        include_context=False,
                        include_input=False,
                    )
                ]
                logger.warning(
                    "LLM response schema validation failed: issues=%s",
                    issues,
                )
                if attempt_number < total_attempts:
                    current_user_prompt = self._build_repair_prompt(
                        user_prompt,
                        issues,
                    )
                    self._log_structured_retry(
                        schema_name=schema_name,
                        attempt_number=attempt_number,
                        failure_stage="schema_validation",
                        issues=issues,
                    )
                    continue
                log_event(
                    "llm.call.failed",
                    level="error",
                    provider="deepseek",
                    model=self._model,
                    output_schema=schema_name,
                    attempt_number=attempt_number,
                    failure_stage="schema_validation",
                    issue_count=len(issues),
                    response_chars=len(content),
                    duration_ms=duration_ms(started_at),
                )
                raise LLMResponseValidationError(
                    "LLM 返回内容未通过结构校验"
                ) from exc

            log_event(
                "llm.call.completed",
                provider="deepseek",
                model=self._model,
                output_schema=schema_name,
                attempt_number=attempt_number,
                response_chars=len(content),
                duration_ms=duration_ms(started_at),
            )
            return result

        raise RuntimeError("structured generation attempts exhausted")

    @staticmethod
    def _build_repair_prompt(
        original_user_prompt: str,
        issues: list[dict[str, str]],
    ) -> str:
        return "\n".join(
            [
                original_user_prompt,
                "",
                "上一次输出未通过结构校验。请重新输出完整 JSON，不要只输出修补片段。",
                "validation_issues:",
                json.dumps(
                    issues,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
            ]
        )

    def _log_structured_retry(
        self,
        *,
        schema_name: str,
        attempt_number: int,
        failure_stage: str,
        issues: list[dict[str, str]],
    ) -> None:
        log_event(
            "llm.call.retrying",
            level="warning",
            provider="deepseek",
            model=self._model,
            output_schema=schema_name,
            attempt_number=attempt_number,
            next_attempt_number=attempt_number + 1,
            failure_stage=failure_stage,
            issue_count=len(issues),
            issues=issues,
        )
