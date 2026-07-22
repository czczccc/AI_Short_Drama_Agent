from pydantic import BaseModel, ConfigDict


class ErrorResponse(BaseModel):
    """由后端主动返回的安全错误结构。"""

    model_config = ConfigDict(extra="forbid")

    detail: str
