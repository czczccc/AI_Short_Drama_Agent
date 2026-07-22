import json
import logging
from pathlib import Path

from pydantic import ValidationError

from app.providers.llm.base import LLMProvider, LLMResponseValidationError
from app.schemas.character import CharacterBible
from app.schemas.outline import EpisodeOutline, StoryOutline
from app.schemas.script import EpisodeScript


PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "writer_v1.md"
logger = logging.getLogger(__name__)


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
    ) -> EpisodeScript:
        characters = (
            [bible.model_dump(mode="json") for bible in character_bibles.values()]
            if character_bibles is not None
            else [
                character.model_dump(mode="json")
                for character in story_outline.characters
            ]
        )
        input_data = {
            "story_outline": story_outline.model_dump(mode="json"),
            "character_source": (
                "character_bible" if character_bibles is not None else "outline"
            ),
            "characters": characters,
            "episode_outline": episode_outline.model_dump(mode="json"),
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
