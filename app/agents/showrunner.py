import json

from app.prompts.showrunner.v1 import SYSTEM_PROMPT
from app.providers.llm.base import LLMProvider
from app.schemas.character import CharacterBibleCollection
from app.schemas.outline import StoryOutline
from app.schemas.showrunner import ShowrunnerState


class ShowrunnerAgent:
    def __init__(self, llm_provider: LLMProvider) -> None:
        self._llm_provider = llm_provider
        self._system_prompt = SYSTEM_PROMPT

    def generate_showrunner_state(
        self,
        outline: StoryOutline,
        characters: CharacterBibleCollection,
        source_outline_hash: str,
        source_characters_hash: str,
    ) -> ShowrunnerState:
        user_prompt = "\n".join(
            [
                f"source_outline_hash: {source_outline_hash}",
                f"source_characters_hash: {source_characters_hash}",
                "story_outline:",
                outline.model_dump_json(),
                "character_bibles:",
                json.dumps(
                    {
                        character_id: bible.model_dump(mode="json")
                        for character_id, bible in characters.characters.items()
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                "请严格按照系统提示输出 Showrunner State JSON。",
            ]
        )
        return self._llm_provider.generate_structured(
            system_prompt=self._system_prompt,
            user_prompt=user_prompt,
            output_schema=ShowrunnerState,
        )

