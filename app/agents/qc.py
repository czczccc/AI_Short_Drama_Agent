import json
import logging
from pathlib import Path

from pydantic import ValidationError

from app.agents.writer import (
    _find_neighbor_episode,
    _future_episode_boundary,
    _story_outline_context,
)
from app.providers.llm.base import LLMProvider, LLMResponseValidationError
from app.schemas.character import CharacterBible
from app.schemas.memory import StoryMemory
from app.schemas.outline import EpisodeOutline, StoryOutline
from app.schemas.qc import QCReport
from app.schemas.script import EpisodeScript


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
        }
        generated_report = self._llm_provider.generate_structured(
            system_prompt=self._system_prompt,
            user_prompt=json.dumps(input_data, ensure_ascii=False),
            output_schema=QCReport,
        )

        try:
            return QCReport.model_validate(
                generated_report.model_dump(mode="json"),
                context={
                    "expected_episode_number": episode_outline.episode_number,
                },
            )
        except ValidationError as exc:
            issues = [
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
            logger.warning("QC output context validation failed: issues=%s", issues)
            raise LLMResponseValidationError("LLM 返回 QC 报告与请求不一致") from exc

