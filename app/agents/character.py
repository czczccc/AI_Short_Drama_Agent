import json
import logging
from pathlib import Path

from pydantic import ValidationError

from app.observability.logging import log_event
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
        original_user_prompt = json.dumps(input_data, ensure_ascii=False)
        current_user_prompt = original_user_prompt
        for attempt_number in range(1, 3):
            generated = self._llm_provider.generate_structured(
                system_prompt=self._system_prompt,
                user_prompt=current_user_prompt,
                output_schema=CharacterBibleCollection,
            )

            try:
                return CharacterBibleCollection.model_validate(
                    generated.model_dump(mode="json"),
                    context={"outline_characters": story_outline.characters},
                )
            except ValidationError as exc:
                issues = self._build_context_issues(generated, story_outline)
                if attempt_number == 1:
                    log_event(
                        "workflow.characters.context_retrying",
                        level="warning",
                        attempt_number=attempt_number,
                        next_attempt_number=attempt_number + 1,
                        issues=issues,
                    )
                    current_user_prompt = "\n".join(
                        [
                            original_user_prompt,
                            "",
                            "上一次角色圣经与大纲不一致。请重新输出完整 JSON，不要只输出修补片段。",
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
                    "Character output context validation failed: issues=%s",
                    issues,
                )
                raise LLMResponseValidationError(
                    "LLM 返回角色圣经与大纲不一致"
                ) from exc

        raise RuntimeError("character generation attempts exhausted")

    @staticmethod
    def _build_context_issues(
        generated: CharacterBibleCollection,
        story_outline: StoryOutline,
    ) -> list[dict]:
        expected = {
            character.character_id: character
            for character in story_outline.characters
        }
        actual_ids = set(generated.characters)
        expected_ids = set(expected)
        issues: list[dict] = []

        missing_ids = sorted(expected_ids - actual_ids)
        unexpected_ids = sorted(actual_ids - expected_ids)
        if missing_ids or unexpected_ids:
            issues.append(
                {
                    "type": "character_id_set_mismatch",
                    "missing_character_ids": missing_ids,
                    "unexpected_character_ids": unexpected_ids,
                }
            )

        for character_id in sorted(expected_ids & actual_ids):
            concept = expected[character_id]
            bible = generated.characters[character_id]
            mismatched_fields = [
                field_name
                for field_name in ("name", "role", "age")
                if getattr(bible, field_name) != getattr(concept, field_name)
            ]
            if mismatched_fields:
                issues.append(
                    {
                        "type": "character_identity_mismatch",
                        "character_id": character_id,
                        "fields": mismatched_fields,
                    }
                )

        return issues or [{"type": "character_context_mismatch"}]
