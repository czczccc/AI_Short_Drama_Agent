import pytest

from app.configs.settings import Settings
from app.providers.llm.base import LLMConfigurationError
from app.providers.llm.factory import get_llm_provider


def test_provider_factory_rejects_unknown_provider() -> None:
    settings = Settings(
        _env_file=None,
        llm_provider="unknown",
        deepseek_api_key="test-key",
    )

    with pytest.raises(LLMConfigurationError):
        get_llm_provider(settings)


def test_provider_factory_rejects_missing_api_key() -> None:
    settings = Settings(
        _env_file=None,
        llm_provider="deepseek",
        deepseek_api_key="",
    )

    with pytest.raises(LLMConfigurationError):
        get_llm_provider(settings)
