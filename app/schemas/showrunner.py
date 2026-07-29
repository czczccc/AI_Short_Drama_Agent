from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.outline import CharacterId, ChineseText
from app.schemas.qc import QCReport


class StrictShowrunnerModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class StoryBible(StrictShowrunnerModel):
    series_title: ChineseText
    logline: ChineseText
    genre: ChineseText
    tone: ChineseText
    world_rules: list[ChineseText] = Field(min_length=1)
    canon_facts: list[ChineseText] = Field(min_length=1)
    core_conflict: ChineseText
    main_mysteries: list[ChineseText] = Field(min_length=1)
    forbidden_reveals: list[ChineseText] = Field(min_length=1)
    continuity_rules: list[ChineseText] = Field(min_length=1)


class EpisodePlanItem(StrictShowrunnerModel):
    episode_number: int = Field(ge=1, le=10)
    title: ChineseText
    dramatic_function: ChineseText
    must_include: list[ChineseText] = Field(min_length=1)
    must_not_reveal: list[ChineseText] = Field(min_length=1)
    setup: list[ChineseText] = Field(min_length=1)
    payoff: list[ChineseText] = Field(min_length=1)
    ending_hook: ChineseText
    allowed_new_facts: list[ChineseText] = Field(min_length=1)


class CharacterArcBeat(StrictShowrunnerModel):
    episode_number: int = Field(ge=1, le=10)
    emotional_state: ChineseText
    goal: ChineseText
    change: ChineseText
    knowledge_state: ChineseText


class CharacterArcPlan(StrictShowrunnerModel):
    character_id: CharacterId
    character_name: ChineseText
    starting_state: ChineseText
    ending_state: ChineseText
    episode_beats: list[CharacterArcBeat] = Field(min_length=10, max_length=10)

    @model_validator(mode="after")
    def validate_episode_beats_sequence(self) -> "CharacterArcPlan":
        numbers = [beat.episode_number for beat in self.episode_beats]
        if numbers != list(range(1, 11)):
            raise ValueError("character arc episode_number 必须从 1 连续到 10")
        return self


class WriterBriefCharacterState(StrictShowrunnerModel):
    character_id: CharacterId
    character_name: ChineseText
    current_goal: ChineseText
    emotional_state: ChineseText
    knows: list[ChineseText] = Field(min_length=1)
    must_not_know: list[ChineseText] = Field(min_length=1)


class WriterBrief(StrictShowrunnerModel):
    episode_number: int = Field(ge=1, le=10)
    episode_goal: ChineseText
    allowed_scope: list[ChineseText] = Field(min_length=1)
    required_beats: list[ChineseText] = Field(min_length=1)
    forbidden_content: list[ChineseText] = Field(min_length=1)
    character_states: list[WriterBriefCharacterState] = Field(min_length=1)
    continuity_context: list[ChineseText] = Field(min_length=1)
    props_and_evidence: list[ChineseText] = Field(min_length=1)
    ending_requirement: ChineseText
    target_duration_seconds: int = Field(ge=30, le=600)


class ShowrunnerState(StrictShowrunnerModel):
    version: str = Field(pattern=r"^showrunner_v\d+$")
    source_outline_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_characters_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    story_bible: StoryBible
    episode_plan: list[EpisodePlanItem] = Field(min_length=10, max_length=10)
    character_arcs: list[CharacterArcPlan] = Field(min_length=1)
    writer_briefs: dict[str, object] = Field(default_factory=dict)
    qc_reports: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_episode_plan_sequence(self) -> "ShowrunnerState":
        numbers = [episode.episode_number for episode in self.episode_plan]
        if numbers != list(range(1, 11)):
            raise ValueError("episode_plan episode_number 必须从 1 连续到 10")
        return self


class ShowrunnerGenerateRequest(StrictShowrunnerModel):
    force_regenerate: bool = False


class ShowrunnerResponse(StrictShowrunnerModel):
    project_id: int
    showrunner: ShowrunnerState


class WriterBriefGenerateRequest(StrictShowrunnerModel):
    target_duration_seconds: int = Field(default=90, ge=30, le=600)
    force_regenerate: bool = False


class WriterBriefResponse(StrictShowrunnerModel):
    project_id: int
    episode_number: int
    brief: WriterBrief


class ShowrunnerQCResponse(StrictShowrunnerModel):
    project_id: int
    episode_number: int
    report: QCReport
