from typing import Literal

from pydantic import Field, field_validator

from app.schemas.outline import CharacterId, ChineseText
from app.schemas.script import StrictScriptModel


class CharacterMemoryUpdate(StrictScriptModel):
    appears: bool = True
    knows: list[ChineseText] = Field(default_factory=list)
    current_goal: ChineseText | None = None
    relationship_changes: list[ChineseText] = Field(default_factory=list)

    @field_validator("current_goal", mode="before")
    @classmethod
    def normalize_blank_current_goal(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value


class PropEvidenceMemory(StrictScriptModel):
    name: ChineseText
    owner: ChineseText | None = None
    status: ChineseText
    first_episode: int = Field(ge=1, le=10)


class EpisodeEndingState(StrictScriptModel):
    location: ChineseText
    time_of_day: ChineseText
    situation: ChineseText


class ContinuityObligation(StrictScriptModel):
    obligation_id: str = Field(min_length=1, max_length=100)
    kind: Literal[
        "ending_state",
        "active_crisis",
        "promise",
        "prop_or_evidence",
    ]
    description: ChineseText
    source_episode_number: int = Field(ge=1, le=10)
    due_episode_number: int = Field(ge=1, le=10)
    source_memory_path: str = Field(min_length=1, max_length=200)


class EpisodeMemory(StrictScriptModel):
    episode_number: int = Field(ge=1, le=10)
    source: Literal["rule_extracted", "qc_approved"] = "rule_extracted"
    summary: ChineseText
    new_facts: list[ChineseText] = Field(default_factory=list)
    revealed_secrets: list[ChineseText] = Field(default_factory=list)
    unresolved_questions: list[ChineseText] = Field(default_factory=list)
    character_updates: dict[CharacterId, CharacterMemoryUpdate] = Field(
        default_factory=dict
    )
    props_and_evidence: list[PropEvidenceMemory] = Field(default_factory=list)
    ending_state: EpisodeEndingState | None = None
    ending_hook: ChineseText
    continuity_obligations: list[ContinuityObligation] = Field(
        default_factory=list
    )


class StoryMemory(StrictScriptModel):
    version: Literal["story_memory_v2"] = "story_memory_v2"
    episodes: dict[str, EpisodeMemory] = Field(default_factory=dict)
