import json
import logging
from pathlib import Path

from pydantic import ValidationError

from app.providers.llm.base import LLMProvider, LLMResponseValidationError
from app.schemas.character import CharacterBibleCollection
from app.schemas.outline import StoryOutline


PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "character_v1.md"
logger = logging.getLogger(__name__)


class CharacterAgent:
    def __init__(self, llm_provider: LLMProvider) -> None:
        self._llm_provider = llm_provider
        self._system_prompt = PROMPT_PATH.read_text(encoding="utf-8")

    def generate_character_bibles(
        self, story_outline: StoryOutline
    ) -> CharacterBibleCollection:
        input_data = {
            "story_outline": story_outline.model_dump(mode="json"),
            "existing_character_concepts": [
                character.model_dump(mode="json")
                for character in story_outline.characters
            ],
            "world_setting": story_outline.world_setting,
            "core_conflict": story_outline.core_conflict,
            "episode_outlines": [
                episode.model_dump(mode="json") for episode in story_outline.episodes
            ],
        }
        generated = self._llm_provider.generate_structured(
            system_prompt=self._system_prompt,
            user_prompt=json.dumps(input_data, ensure_ascii=False),
            output_schema=CharacterBibleCollection,
        )

        try:
            return CharacterBibleCollection.model_validate(
                generated.model_dump(mode="json"),
                context={"outline_characters": story_outline.characters},
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
            logger.warning("Character output context validation failed: issues=%s", issues)
            raise LLMResponseValidationError("LLM 返回角色圣经与大纲不一致") from exc
