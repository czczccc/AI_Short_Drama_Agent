import re
from typing import Annotated

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)


def validate_chinese_text(value: str) -> str:
    value = value.strip()
    if not re.search(r"[\u3400-\u9fff]", value):
        raise ValueError("文本内容必须使用中文")
    return value


ChineseText = Annotated[
    str,
    StringConstraints(min_length=1),
    AfterValidator(validate_chinese_text),
]
CharacterId = Annotated[str, StringConstraints(pattern=r"^[a-z]+(?:_[a-z]+)*$")]


class StrictOutlineModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CharacterConcept(StrictOutlineModel):
    character_id: CharacterId
    name: ChineseText
    role: ChineseText
    age: ChineseText
    appearance: ChineseText
    personality: ChineseText
    motivation: ChineseText
    secret: ChineseText


class EpisodeOutline(StrictOutlineModel):
    episode_number: int = Field(ge=1, le=10)
    title: ChineseText
    summary: ChineseText
    main_conflict: ChineseText
    ending_hook: ChineseText


class StoryOutline(StrictOutlineModel):
    title: ChineseText
    logline: ChineseText
    genre: ChineseText
    tone: ChineseText
    target_audience: ChineseText
    world_setting: ChineseText
    core_conflict: ChineseText
    themes: list[ChineseText] = Field(min_length=1)
    characters: list[CharacterConcept] = Field(min_length=3, max_length=6)
    episodes: list[EpisodeOutline] = Field(min_length=10, max_length=10)

    @model_validator(mode="after")
    def validate_episode_sequence(self) -> "StoryOutline":
        numbers = [episode.episode_number for episode in self.episodes]
        if numbers != list(range(1, 11)):
            raise ValueError("episode_number 必须从 1 连续到 10")
        return self


class OutlineGenerateRequest(StrictOutlineModel):
    idea: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    episode_count: int = Field(default=10, ge=10, le=10)


class OutlineGenerateResponse(StrictOutlineModel):
    project_id: int
    status: str
    outline: StoryOutline
