from types import SimpleNamespace

import pytest

from app.providers.llm.base import (
    LLMResponseJSONError,
    LLMResponseValidationError,
)
from app.providers.llm.deepseek_provider import DeepSeekProvider
from app.schemas.outline import StoryOutline
from tests.fakes import valid_outline_data


class FakeCompletions:
    def __init__(self, content: str) -> None:
        self.content = content
        self.kwargs: dict | None = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.content))]
        )


def make_client(content: str):
    completions = FakeCompletions(content)
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    return client, completions


def test_deepseek_provider_parses_and_validates_json() -> None:
    import json

    client, completions = make_client(json.dumps(valid_outline_data()))
    provider = DeepSeekProvider(
        api_key="test-key",
        base_url="https://api.deepseek.com",
        model="configured-model",
        timeout_seconds=120,
        max_tokens=12000,
        thinking_enabled=False,
        client=client,
    )

    result = provider.generate_structured("输出JSON", "生成大纲", StoryOutline)

    assert isinstance(result, StoryOutline)
    assert len(result.episodes) == 10
    assert completions.kwargs["model"] == "configured-model"
    assert completions.kwargs["response_format"] == {"type": "json_object"}
    assert completions.kwargs["extra_body"] == {"thinking": {"type": "disabled"}}


def test_deepseek_provider_converts_invalid_json_to_clean_error() -> None:
    client, _ = make_client("not-json")
    provider = DeepSeekProvider(
        api_key="test-key",
        base_url="https://api.deepseek.com",
        model="configured-model",
        timeout_seconds=120,
        max_tokens=12000,
        thinking_enabled=False,
        client=client,
    )

    with pytest.raises(LLMResponseJSONError):
        provider.generate_structured("输出JSON", "生成大纲", StoryOutline)


def test_deepseek_provider_converts_schema_error_to_clean_error() -> None:
    import json

    invalid = valid_outline_data()
    invalid["episodes"] = invalid["episodes"][:-1]
    client, _ = make_client(json.dumps(invalid))
    provider = DeepSeekProvider(
        api_key="test-key",
        base_url="https://api.deepseek.com",
        model="configured-model",
        timeout_seconds=120,
        max_tokens=12000,
        thinking_enabled=False,
        client=client,
    )

    with pytest.raises(LLMResponseValidationError):
        provider.generate_structured("输出JSON", "生成大纲", StoryOutline)

