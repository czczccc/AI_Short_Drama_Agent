import pytest

from app.configs.settings import Settings
from app.providers.video.base import VideoProviderConfigurationError
from app.providers.video.factory import get_video_provider
from app.providers.video.fake_provider import FakeVideoProvider


def test_video_provider_factory_returns_fake_provider_by_default() -> None:
    settings = Settings(_env_file=None)

    provider = get_video_provider(settings)

    assert isinstance(provider, FakeVideoProvider)


def test_video_provider_factory_rejects_unknown_provider() -> None:
    settings = Settings(_env_file=None, video_provider="unknown")

    with pytest.raises(VideoProviderConfigurationError):
        get_video_provider(settings)

