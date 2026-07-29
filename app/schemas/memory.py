from pydantic import Field

from app.schemas.outline import CharacterId, ChineseText
from app.schemas.script import StrictScriptModel


class CharacterMemoryUpdate(StrictScriptModel):
    appears: bool = True
    knows: list[ChineseText] = Field(default_factory=list)
    current_goal: ChineseText | None = None
    relationship_changes: list[ChineseText] = Field(default_factory=list)


class PropEvidenceMemory(StrictScriptModel):
    name: ChineseText
    owner: ChineseText | None = None
    status: ChineseText
    first_episode: int = Field(ge=1, le=10)


class EpisodeMemory(StrictScriptModel):
    episode_number: int = Field(ge=1, le=10)
    summary: ChineseText
    new_facts: list[ChineseText] = Field(default_factory=list)
    revealed_secrets: list[ChineseText] = Field(default_factory=list)
    unresolved_questions: list[ChineseText] = Field(default_factory=list)
    character_updates: dict[CharacterId, CharacterMemoryUpdate] = Field(
        default_factory=dict
    )
    props_and_evidence: list[PropEvidenceMemory] = Field(default_factory=list)
    ending_hook: ChineseText


class StoryMemory(StrictScriptModel):
    episodes: dict[str, EpisodeMemory] = Field(default_factory=dict)
