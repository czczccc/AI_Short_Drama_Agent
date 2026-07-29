from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, model_validator

from app.schemas.outline import ChineseText


class StrictQCModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class QCIssue(StrictQCModel):
    episode_number: int = Field(ge=1, le=10)
    severity: Literal["info", "warning", "error"]
    code: str = Field(min_length=1)
    message: ChineseText
    suggestion: ChineseText | None = None


class QCReport(StrictQCModel):
    episode_number: int = Field(ge=1, le=10)
    status: Literal["pass", "warning", "fail"]
    summary: ChineseText
    issues: list[QCIssue] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_report_context(self, info: ValidationInfo) -> "QCReport":
        expected_episode_number = (info.context or {}).get("expected_episode_number")
        if (
            expected_episode_number is not None
            and self.episode_number != expected_episode_number
        ):
            raise ValueError("episode_number 与请求不一致")
        mismatched_issues = [
            issue
            for issue in self.issues
            if issue.episode_number != self.episode_number
        ]
        if mismatched_issues:
            raise ValueError("issues 中的 episode_number 必须与报告一致")
        return self

