import json

from app.prompts.showrunner.v1 import SYSTEM_PROMPT
from app.prompts.showrunner.brief_v1 import SYSTEM_PROMPT as BRIEF_SYSTEM_PROMPT
from app.providers.llm.base import LLMProvider
from app.schemas.character import CharacterBibleCollection
from app.schemas.memory import StoryMemory
from app.schemas.outline import StoryOutline
from app.schemas.showrunner import ShowrunnerState, WriterBrief


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

    def generate_writer_brief(
        self,
        state: ShowrunnerState,
        episode_number: int,
        story_memory: StoryMemory,
        target_duration_seconds: int,
    ) -> WriterBrief:
        current_episode_plan = next(
            episode
            for episode in state.episode_plan
            if episode.episode_number == episode_number
        )
        relevant_character_arcs = []
        for arc in state.character_arcs:
            current_beat = next(
                beat
                for beat in arc.episode_beats
                if beat.episode_number == episode_number
            )
            relevant_character_arcs.append(
                {
                    "character_id": arc.character_id,
                    "character_name": arc.character_name,
                    "starting_state": arc.starting_state,
                    "ending_state": arc.ending_state,
                    "current_episode_beat": current_beat.model_dump(mode="json"),
                }
            )

        user_prompt = "\n".join(
            [
                f"episode_number: {episode_number}",
                f"target_duration_seconds: {target_duration_seconds}",
                "story_bible:",
                state.story_bible.model_dump_json(),
                "current_episode_plan:",
                current_episode_plan.model_dump_json(),
                "relevant_character_arcs:",
                json.dumps(
                    relevant_character_arcs,
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                "story_memory:",
                story_memory.model_dump_json(),
                "请严格按照系统提示输出 Writer Brief JSON。",
            ]
        )
        return self._llm_provider.generate_structured(
            system_prompt=BRIEF_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            output_schema=WriterBrief,
        )
