from fastapi import Depends

from app.configs.settings import Settings, get_settings
from app.providers.video.base import VideoProvider, VideoProviderConfigurationError
from app.providers.video.fake_provider import FakeVideoProvider


def get_video_provider(settings: Settings) -> VideoProvider:
    provider_name = settings.video_provider.strip().lower()
    if provider_name == "fake":
        return FakeVideoProvider()
    raise VideoProviderConfigurationError("不支持的 Video Provider 配置")


def get_configured_video_provider(
    settings: Settings = Depends(get_settings),
) -> VideoProvider:
    return get_video_provider(settings)

