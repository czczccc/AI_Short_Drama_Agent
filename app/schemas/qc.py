from typing import Literal, get_args

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)

from app.schemas.outline import ChineseText
from app.schemas.memory import EpisodeMemory


QCIssueCode = Literal[
    "future_boundary_risk",
    "future_reveal",
    "outline_scope_violation",
    "required_beat_missing",
    "forbidden_content",
    "previous_ending_not_continued",
    "opening_hook_not_realized",
    "ending_hook_not_realized",
    "character_knowledge_conflict",
    "character_behavior_conflict",
    "prop_state_conflict",
    "prop_appeared_too_early",
    "timeline_discontinuity",
    "episode_overloaded",
    "scene_character_mismatch",
    "storyboard_structure_risk",
    "other",
]
KNOWN_QC_ISSUE_CODES = frozenset(get_args(QCIssueCode))


class StrictQCModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class QCIssue(StrictQCModel):
    episode_number: int = Field(ge=1, le=10)
    severity: Literal["info", "warning", "error"]
    code: QCIssueCode
    message: ChineseText
    suggestion: ChineseText | None = None

    @field_validator("code", mode="before")
    @classmethod
    def normalize_unknown_code(cls, value: object) -> object:
        if isinstance(value, str) and value not in KNOWN_QC_ISSUE_CODES:
            return "other"
        return value


class MemoryEvidence(StrictQCModel):
    memory_path: str = Field(min_length=1, max_length=200)
    scene_number: int = Field(ge=1, le=8)
    evidence_text: ChineseText


class ContinuityResolution(StrictQCModel):
    obligation_id: str = Field(min_length=1, max_length=100)
    status: Literal["resolved", "carried_forward"]
    scene_number: int = Field(ge=1, le=8)
    evidence_text: ChineseText

    @model_validator(mode="before")
    @classmethod
    def normalize_observed_aliases(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        data = dict(value)
        evidence_aliases = ("resolution_evidence", "evidence")
        evidence_values = [
            data[key]
            for key in evidence_aliases
            if key in data and isinstance(data[key], str)
        ]
        if evidence_values:
            first_evidence = evidence_values[0]
            if any(item != first_evidence for item in evidence_values[1:]):
                raise ValueError("continuity resolution 证据别名内容冲突")
            if (
                "evidence_text" in data
                and data["evidence_text"] != first_evidence
            ):
                raise ValueError("evidence_text 与证据别名内容冲突")
            data.setdefault("evidence_text", first_evidence)
        for key in evidence_aliases:
            if key in data and isinstance(data[key], str):
                data.pop(key)

        status_aliases = (
            ("resolved", "resolved"),
            ("carried_to_next_episode", "carried_forward"),
            ("carries_forward", "carried_forward"),
        )
        inferred_statuses = [
            status
            for key, status in status_aliases
            if data.get(key) is True
        ]
        if len(set(inferred_statuses)) > 1:
            raise ValueError("continuity resolution 状态别名互相冲突")
        if inferred_statuses:
            inferred_status = inferred_statuses[0]
            if "status" in data and data["status"] != inferred_status:
                raise ValueError("status 与状态别名内容冲突")
            data.setdefault("status", inferred_status)
        for key, _ in status_aliases:
            if key in data and isinstance(data[key], bool):
                data.pop(key)

        for key in ("kind", "resolution_notes"):
            if key in data and isinstance(data[key], str):
                data.pop(key)

        return data


class QCReport(StrictQCModel):
    episode_number: int = Field(ge=1, le=10)
    status: Literal["pass", "warning", "fail"]
    summary: ChineseText
    issues: list[QCIssue] = Field(default_factory=list)
    approved_memory: EpisodeMemory | None = None
    memory_evidence: list[MemoryEvidence] = Field(default_factory=list)
    continuity_resolutions: list[ContinuityResolution] = Field(
        default_factory=list
    )

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

        if any(issue.severity == "error" for issue in self.issues):
            expected_status = "fail"
        elif self.issues:
            expected_status = "warning"
        else:
            expected_status = "pass"
        if self.status != expected_status:
            raise ValueError(
                f"status 必须与 issues 严重级别一致，当前应为 {expected_status}"
            )

        if (
            self.approved_memory is not None
            and self.approved_memory.episode_number != self.episode_number
        ):
            raise ValueError("approved_memory 必须与报告集号一致")
        if (
            self.approved_memory is not None
            and self.approved_memory.source != "qc_approved"
        ):
            raise ValueError("approved_memory 的 source 必须为 qc_approved")
        if self.status != "pass" and self.approved_memory is not None:
            raise ValueError("只有通过的 QC 报告可以包含 approved_memory")
        require_approved_memory = (info.context or {}).get(
            "require_approved_memory",
            False,
        )
        if (
            require_approved_memory
            and self.status == "pass"
            and self.approved_memory is None
        ):
            raise ValueError("QC 通过时必须提供 approved_memory")
        if (
            require_approved_memory
            and self.status == "pass"
            and self.approved_memory is not None
            and self.approved_memory.ending_state is None
        ):
            raise ValueError("QC 通过时 approved_memory 必须包含 ending_state")
        return self
