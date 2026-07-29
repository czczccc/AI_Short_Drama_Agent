from app.providers.video.base import VideoProviderCallError
from app.schemas.video import VideoSubmitRequest, VideoTask


class FakeVideoProvider:
    """测试用 Video Provider，不调用任何外部视频 API。"""

    provider_name = "fake"

    def __init__(self) -> None:
        self._tasks: dict[str, VideoTask] = {}

    def submit(self, request: VideoSubmitRequest) -> VideoTask:
        provider_task_id = f"fake_video_{len(self._tasks) + 1}"
        task = VideoTask(
            provider=self.provider_name,
            provider_task_id=provider_task_id,
            status="succeeded",
            prompt=request.prompt,
            duration_seconds=request.duration_seconds,
            aspect_ratio=request.aspect_ratio,
            video_url=f"fake://video/{provider_task_id}.mp4",
        )
        self._tasks[provider_task_id] = task
        return task

    def get_status(self, provider_task_id: str) -> VideoTask:
        return self._get_task(provider_task_id)

    def download(self, provider_task_id: str) -> bytes:
        task = self._get_task(provider_task_id)
        return f"FAKE_VIDEO:{task.provider_task_id}".encode()

    def cancel(self, provider_task_id: str) -> VideoTask:
        task = self._get_task(provider_task_id)
        canceled = task.model_copy(update={"status": "canceled"})
        self._tasks[provider_task_id] = canceled
        return canceled

    def _get_task(self, provider_task_id: str) -> VideoTask:
        task = self._tasks.get(provider_task_id)
        if task is None:
            raise VideoProviderCallError("Video task not found")
        return task

