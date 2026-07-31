import logging
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.providers.llm.base import (
    LLMResponseJSONError,
    LLMResponseValidationError,
)
from app.providers.llm.deepseek_provider import DeepSeekProvider
from app.observability.logging import configure_logging, read_recent_logs
from app.schemas.outline import StoryOutline
from app.schemas.qc import QCReport
from tests.fakes import (
    valid_outline_data,
    valid_qc_pass_report_data,
    valid_qc_report_data,
)


class FakeCompletions:
    def __init__(self, content: str) -> None:
        self.content = content
        self.kwargs: dict | None = None
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.kwargs = kwargs
        self.calls.append(kwargs)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.content))]
        )


class SequencedFakeCompletions:
    def __init__(self, contents: list[str]) -> None:
        self.contents = iter(contents)
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=next(self.contents))
                )
            ]
        )


def make_client(content: str):
    completions = FakeCompletions(content)
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    return client, completions


def test_deepseek_provider_retries_once_after_schema_validation_error() -> None:
    import json

    invalid = valid_outline_data()
    invalid["episodes"] = invalid["episodes"][:-1]
    completions = SequencedFakeCompletions(
        [json.dumps(invalid), json.dumps(valid_outline_data())]
    )
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
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

    assert len(result.episodes) == 10
    assert len(completions.calls) == 2
    repair_prompt = completions.calls[1]["messages"][1]["content"]
    assert "episodes" in repair_prompt
    assert "too_short" in repair_prompt


def test_deepseek_provider_repair_prompt_explains_root_validation_error() -> None:
    import json

    invalid = valid_qc_report_data()
    invalid["status"] = "pass"
    completions = SequencedFakeCompletions(
        [json.dumps(invalid), json.dumps(valid_qc_pass_report_data())]
    )
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    provider = DeepSeekProvider(
        api_key="test-key",
        base_url="https://api.deepseek.com",
        model="configured-model",
        timeout_seconds=120,
        max_tokens=12000,
        thinking_enabled=False,
        client=client,
    )

    result = provider.generate_structured("输出JSON", "审核剧本", QCReport)

    assert result.status == "pass"
    repair_prompt = completions.calls[1]["messages"][1]["content"]
    assert "status 必须与 issues 严重级别一致" in repair_prompt


def test_deepseek_provider_can_use_two_structured_repairs() -> None:
    import json

    invalid = valid_outline_data()
    invalid["episodes"] = invalid["episodes"][:-1]
    completions = SequencedFakeCompletions(
        [
            json.dumps(invalid),
            json.dumps(invalid),
            json.dumps(valid_outline_data()),
        ]
    )
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
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

    assert len(result.episodes) == 10
    assert len(completions.calls) == 3


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


def test_deepseek_provider_emits_structured_call_logs(tmp_path: Path) -> None:
    import json

    log_file = tmp_path / "app.jsonl"
    configure_logging(str(log_file))
    client, _ = make_client(json.dumps(valid_outline_data()))
    provider = DeepSeekProvider(
        api_key="test-key",
        base_url="https://api.deepseek.com",
        model="configured-model",
        timeout_seconds=120,
        max_tokens=12000,
        thinking_enabled=False,
        client=client,
    )

    provider.generate_structured("输出JSON", "生成大纲", StoryOutline)

    records = read_recent_logs(log_file_path=str(log_file))
    events = [record["event"] for record in records]
    assert "llm.call.started" in events
    assert "llm.call.completed" in events
    started = next(record for record in records if record["event"] == "llm.call.started")
    completed = next(
        record for record in records if record["event"] == "llm.call.completed"
    )
    assert started["provider"] == "deepseek"
    assert started["output_schema"] == "StoryOutline"
    assert started["user_chars"] == len("生成大纲")
    assert completed["duration_ms"] >= 0
    assert "test-key" not in log_file.read_text(encoding="utf-8")


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


def test_deepseek_provider_emits_failed_call_log(tmp_path: Path) -> None:
    log_file = tmp_path / "app.jsonl"
    configure_logging(str(log_file))
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

    records = read_recent_logs(log_file_path=str(log_file))
    failed = next(record for record in records if record["event"] == "llm.call.failed")
    assert failed["failure_stage"] == "invalid_json"
    assert failed["output_schema"] == "StoryOutline"


def test_deepseek_provider_logs_only_safe_schema_error_metadata(caplog) -> None:
    import json

    invalid = valid_outline_data()
    invalid["episodes"] = invalid["episodes"][:-1]
    invalid["title"] = "不可泄露的原始标题"
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

    caplog.set_level(logging.WARNING)

    with pytest.raises(LLMResponseValidationError):
        provider.generate_structured("输出JSON", "生成大纲", StoryOutline)

    assert "episodes" in caplog.text
    assert "too_short" in caplog.text
    assert "不可泄露的原始标题" not in caplog.text
    assert "test-key" not in caplog.text
