from typing import Protocol

from app.schemas.video import VideoSubmitRequest, VideoTask


class VideoProvider(Protocol):
    """业务层可依赖的最小视频生成接口。"""

    def submit(self, request: VideoSubmitRequest) -> VideoTask: ...

    def get_status(self, provider_task_id: str) -> VideoTask: ...

    def download(self, provider_task_id: str) -> bytes: ...

    def cancel(self, provider_task_id: str) -> VideoTask: ...


class VideoProviderError(Exception):
    """Video Provider 边界内可安全分类的基础异常。"""


class VideoProviderConfigurationError(VideoProviderError):
    """Provider 或凭据配置无效。"""


class VideoProviderCallError(VideoProviderError):
    """远端视频服务调用失败，或任务状态不可用。"""

