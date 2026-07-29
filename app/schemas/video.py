from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


VideoTaskStatus = Literal["pending", "running", "succeeded", "failed", "canceled"]
VideoAspectRatio = Literal["9:16", "16:9", "1:1"]
NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class StrictVideoModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class VideoSubmitRequest(StrictVideoModel):
    prompt: NonEmptyText
    duration_seconds: int = Field(default=5, ge=1, le=30)
    aspect_ratio: VideoAspectRatio = "9:16"
    negative_prompt: NonEmptyText | None = None
    reference_image_urls: list[str] = Field(default_factory=list)


class VideoTask(StrictVideoModel):
    provider: NonEmptyText
    provider_task_id: NonEmptyText
    status: VideoTaskStatus
    prompt: NonEmptyText
    duration_seconds: int = Field(ge=1, le=30)
    aspect_ratio: VideoAspectRatio
    video_url: str | None = None
    local_path: str | None = None
    error_message: str | None = None
