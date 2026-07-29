import json
import logging
from pathlib import Path

from pydantic import ValidationError

from app.providers.llm.base import LLMProvider, LLMResponseValidationError
from app.schemas.character import CharacterBible
from app.schemas.memory import StoryMemory
from app.schemas.outline import EpisodeOutline, StoryOutline
from app.schemas.script import EpisodeScript
from app.schemas.showrunner import WriterBrief


PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "writer_v2.md"
logger = logging.getLogger(__name__)


def _find_neighbor_episode(
    story_outline: StoryOutline,
    episode_number: int,
    offset: int,
) -> EpisodeOutline | None:
    target_episode_number = episode_number + offset
    return next(
        (
            episode
            for episode in story_outline.episodes
            if episode.episode_number == target_episode_number
        ),
        None,
    )


def _story_outline_context(
    story_outline: StoryOutline,
    previous_episode: EpisodeOutline | None,
    current_episode: EpisodeOutline,
) -> dict:
    context = story_outline.model_dump(mode="json")
    context["episodes"] = [
        episode.model_dump(mode="json")
        for episode in (previous_episode, current_episode)
        if episode is not None
    ]
    return context


def _future_episode_boundary(episode: EpisodeOutline | None) -> dict | None:
    if episode is None:
        return None
    return {
        "episode_number": episode.episode_number,
        "title": episode.title,
        "reserved_for_future": True,
    }


class WriterAgent:
    def __init__(self, llm_provider: LLMProvider) -> None:
        self._llm_provider = llm_provider
        self._system_prompt = PROMPT_PATH.read_text(encoding="utf-8")

    def generate_script(
        self,
        story_outline: StoryOutline,
        episode_outline: EpisodeOutline,
        target_duration_seconds: int,
        character_bibles: dict[str, CharacterBible] | None = None,
        story_memory: StoryMemory | None = None,
        writer_brief: WriterBrief | None = None,
    ) -> EpisodeScript:
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
            "episode_outline": episode_outline.model_dump(mode="json"),
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
            "writer_brief": (
                writer_brief.model_dump(mode="json")
                if writer_brief is not None
                else None
            ),
            "target_duration_seconds": target_duration_seconds,
        }
        generated_script = self._llm_provider.generate_structured(
            system_prompt=self._system_prompt,
            user_prompt=json.dumps(input_data, ensure_ascii=False),
            output_schema=EpisodeScript,
        )

        try:
            return EpisodeScript.model_validate(
                generated_script.model_dump(mode="json"),
                context={
                    "expected_episode_number": episode_outline.episode_number,
                    "target_duration_seconds": target_duration_seconds,
                    "allowed_character_ids": {
                        character.character_id
                        for character in story_outline.characters
                    },
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
            logger.warning("Writer output context validation failed: issues=%s", issues)
            raise LLMResponseValidationError("LLM 返回剧本与大纲不一致") from exc
