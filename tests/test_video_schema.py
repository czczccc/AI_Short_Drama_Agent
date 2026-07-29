import pytest
from pydantic import ValidationError

from app.schemas.video import VideoSubmitRequest, VideoTask


def test_video_submit_request_accepts_minimal_prompt() -> None:
    request = VideoSubmitRequest(prompt="一个程序员在深夜机房发现服务器正在自毁。")

    assert request.prompt == "一个程序员在深夜机房发现服务器正在自毁。"
    assert request.duration_seconds == 5
    assert request.aspect_ratio == "9:16"
    assert request.reference_image_urls == []


def test_video_submit_request_rejects_invalid_duration() -> None:
    with pytest.raises(ValidationError):
        VideoSubmitRequest(
            prompt="一个程序员在深夜机房发现服务器正在自毁。",
            duration_seconds=0,
        )


def test_video_submit_request_rejects_blank_prompt() -> None:
    with pytest.raises(ValidationError):
        VideoSubmitRequest(prompt="   ")


def test_video_task_rejects_unknown_status() -> None:
    with pytest.raises(ValidationError):
        VideoTask(
            provider="fake",
            provider_task_id="task_1",
            status="done",
            prompt="一个程序员在深夜机房发现服务器正在自毁。",
            duration_seconds=5,
            aspect_ratio="9:16",
        )


def test_video_task_forbids_extra_fields() -> None:
    with pytest.raises(ValidationError):
        VideoTask(
            provider="fake",
            provider_task_id="task_1",
            status="pending",
            prompt="一个程序员在深夜机房发现服务器正在自毁。",
            duration_seconds=5,
            aspect_ratio="9:16",
            unexpected=True,
        )
