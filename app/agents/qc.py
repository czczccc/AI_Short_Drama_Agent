import json
import logging
from pathlib import Path

from pydantic import ValidationError

from app.agents.writer import (
    _find_neighbor_episode,
    _future_episode_boundary,
    _story_outline_context,
)
from app.observability.logging import log_event
from app.providers.llm.base import LLMProvider, LLMResponseValidationError
from app.schemas.character import CharacterBible
from app.schemas.memory import StoryMemory
from app.schemas.outline import EpisodeOutline, StoryOutline
from app.schemas.qc import QCIssue, QCReport
from app.schemas.script import EpisodeScript
from app.schemas.showrunner import WriterBrief
from app.services.qc_grounding import (
    QCReportGroundingError,
    build_scene_evidence_catalog,
    complete_missing_continuity_obligations,
    normalize_surplus_memory_evidence,
    validate_qc_report_grounding,
)


PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "qc_v1.md"
logger = logging.getLogger(__name__)


class QCAgent:
    def __init__(self, llm_provider: LLMProvider) -> None:
        self._llm_provider = llm_provider
        self._system_prompt = PROMPT_PATH.read_text(encoding="utf-8")

    def generate_report(
        self,
        story_outline: StoryOutline,
        episode_outline: EpisodeOutline,
        script: EpisodeScript,
        character_bibles: dict[str, CharacterBible] | None = None,
        story_memory: StoryMemory | None = None,
        writer_brief: WriterBrief | None = None,
        rule_issues: list[QCIssue] | None = None,
    ) -> QCReport:
        characters = (
            [bible.model_dump(mode="json") for bible in character_bibles.values()]
            if character_bibles is not None
            else [
                character.model_dump(mode="json")
                for character in story_outline.characters
            ]
        )
        previous_episode = _find_neighbor_episode(
            story_outline,
            episode_outline.episode_number,
            -1,
        )
        next_episode = _find_neighbor_episode(
            story_outline,
            episode_outline.episode_number,
            1,
        )
        input_data = {
            "story_outline": _story_outline_context(
                story_outline,
                previous_episode,
                episode_outline,
            ),
            "character_source": (
                "character_bible" if character_bibles is not None else "outline"
            ),
            "characters": characters,
            "previous_episode_outline": (
                previous_episode.model_dump(mode="json") if previous_episode else None
            ),
            "current_episode_outline": episode_outline.model_dump(mode="json"),
            "next_episode_outline": _future_episode_boundary(next_episode),
            "story_memory": (
                story_memory.model_dump(mode="json")
                if story_memory is not None
                else StoryMemory().model_dump(mode="json")
            ),
            "script": script.model_dump(mode="json"),
            "evidence_catalog": build_scene_evidence_catalog(script),
            "ending_state_reference": {
                "scene_number": script.scenes[-1].scene_number,
                "location": script.scenes[-1].location,
                "time_of_day": script.scenes[-1].time_of_day,
            },
            "writer_brief": (
                writer_brief.model_dump(mode="json")
                if writer_brief is not None
                else None
            ),
            "rule_issues": [
                issue.model_dump(mode="json") for issue in (rule_issues or [])
            ],
        }
        original_user_prompt = json.dumps(input_data, ensure_ascii=False)
        current_user_prompt = original_user_prompt
        for attempt_number in range(1, 3):
            generated_report = self._llm_provider.generate_structured(
                system_prompt=self._system_prompt,
                user_prompt=current_user_prompt,
                output_schema=QCReport,
            )

            try:
                validated_report = QCReport.model_validate(
                    generated_report.model_dump(mode="json"),
                    context={
                        "expected_episode_number": episode_outline.episode_number,
                        "require_approved_memory": True,
                    },
                )
                validated_report = complete_missing_continuity_obligations(
                    validated_report
                )
                validated_report = normalize_surplus_memory_evidence(
                    validated_report
                )
                validate_qc_report_grounding(
                    validated_report,
                    script,
                    writer_brief,
                )
                return validated_report
            except (ValidationError, QCReportGroundingError) as exc:
                issues = self._safe_validation_issues(exc)
                failure_reasons = sorted({issue["type"] for issue in issues})
                if attempt_number == 1:
                    log_event(
                        "workflow.qc.context_retrying",
                        level="warning",
                        episode_number=episode_outline.episode_number,
                        attempt_number=attempt_number,
                        next_attempt_number=attempt_number + 1,
                        failure_reasons=failure_reasons,
                    )
                    current_user_prompt = "\n".join(
                        [
                            original_user_prompt,
                            "",
                            "上一次 QC 报告未通过后端证据与连续性校验。"
                            "请重新输出完整 JSON，不要只输出修补片段。",
                            "context_issues:",
                            json.dumps(
                                issues,
                                ensure_ascii=False,
                                sort_keys=True,
                                separators=(",", ":"),
                            ),
                        ]
                    )
                    continue

                logger.warning(
                    "QC output context validation failed: issues=%s",
                    issues,
                )
                log_event(
                    "workflow.qc.validation_failed",
                    level="error",
                    episode_number=episode_outline.episode_number,
                    attempt_number=attempt_number,
                    failure_reasons=failure_reasons,
                )
                raise LLMResponseValidationError(
                    "LLM 返回 QC 报告与请求不一致"
                ) from exc

        raise RuntimeError("QC context validation attempts exhausted")

    @staticmethod
    def _safe_validation_issues(
        exc: ValidationError | QCReportGroundingError,
    ) -> list[dict]:
        if isinstance(exc, QCReportGroundingError):
            return exc.issues
        return [
            {
                "location": ".".join(str(part) for part in error["loc"]),
                "type": error["type"],
            }
            for error in exc.errors(
                include_url=False,
                include_context=False,
                include_input=False,
            )
        ]
