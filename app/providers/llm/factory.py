from fastapi import Depends

from app.configs.settings import Settings, get_settings
from app.providers.llm.base import LLMConfigurationError, LLMProvider
from app.providers.llm.deepseek_provider import DeepSeekProvider


def get_llm_provider(settings: Settings) -> LLMProvider:
    provider_name = settings.llm_provider.strip().lower()
    if provider_name != "deepseek":
        raise LLMConfigurationError("不支持的 LLM Provider 配置")
    if not settings.deepseek_api_key.strip():
        raise LLMConfigurationError("DeepSeek API Key 未配置")

    return DeepSeekProvider(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        model=settings.deepseek_model,
        timeout_seconds=settings.deepseek_timeout_seconds,
        max_tokens=settings.deepseek_max_tokens,
        thinking_enabled=settings.deepseek_thinking_enabled,
    )


def get_configured_llm_provider(
    settings: Settings = Depends(get_settings),
) -> LLMProvider:
    return get_llm_provider(settings)
