import pytest

from app.providers.video.base import VideoProviderCallError
from app.providers.video.fake_provider import FakeVideoProvider
from app.schemas.video import VideoSubmitRequest


def test_fake_video_provider_submits_succeeded_task() -> None:
    provider = FakeVideoProvider()
    request = VideoSubmitRequest(
        prompt="一个程序员在深夜机房发现服务器正在自毁。",
        duration_seconds=6,
        aspect_ratio="9:16",
    )

    task = provider.submit(request)

    assert task.provider == "fake"
    assert task.provider_task_id == "fake_video_1"
    assert task.status == "succeeded"
    assert task.video_url == "fake://video/fake_video_1.mp4"
    assert task.prompt == request.prompt


def test_fake_video_provider_get_status_returns_existing_task() -> None:
    provider = FakeVideoProvider()
    task = provider.submit(
        VideoSubmitRequest(prompt="一个程序员在深夜机房发现服务器正在自毁。")
    )

    status = provider.get_status(task.provider_task_id)

    assert status == task


def test_fake_video_provider_cancel_marks_task_canceled() -> None:
    provider = FakeVideoProvider()
    task = provider.submit(
        VideoSubmitRequest(prompt="一个程序员在深夜机房发现服务器正在自毁。")
    )

    canceled = provider.cancel(task.provider_task_id)

    assert canceled.status == "canceled"
    assert provider.get_status(task.provider_task_id).status == "canceled"


def test_fake_video_provider_download_returns_deterministic_bytes() -> None:
    provider = FakeVideoProvider()
    task = provider.submit(
        VideoSubmitRequest(prompt="一个程序员在深夜机房发现服务器正在自毁。")
    )

    content = provider.download(task.provider_task_id)

    assert content.startswith(b"FAKE_VIDEO:")
    assert task.provider_task_id.encode() in content


def test_fake_video_provider_rejects_unknown_task() -> None:
    provider = FakeVideoProvider()

    with pytest.raises(VideoProviderCallError):
        provider.get_status("missing")

