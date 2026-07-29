from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)

from app.schemas.outline import CharacterId, ChineseText, validate_chinese_text


class StrictScriptModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DialogueLine(StrictScriptModel):
    character_id: CharacterId
    character_name: ChineseText
    emotion: ChineseText
    line: ChineseText
    action_note: str | None

    @field_validator("action_note")
    @classmethod
    def validate_action_note(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return validate_chinese_text(value)


class SceneScript(StrictScriptModel):
    scene_number: int = Field(ge=1, le=8)
    location: ChineseText
    time_of_day: ChineseText
    characters: list[CharacterId] = Field(min_length=1)
    scene_goal: ChineseText
    action: str | None
    dialogues: list[DialogueLine]
    transition: ChineseText

    @model_validator(mode="before")
    @classmethod
    def normalize_llm_dialogue_key(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        if "dialogues" in data or "dialogue" not in data:
            return data
        normalized = dict(data)
        normalized["dialogues"] = normalized.pop("dialogue")
        return normalized

    @field_validator("action")
    @classmethod
    def validate_action(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return validate_chinese_text(value)

    @model_validator(mode="after")
    def require_action_or_dialogue(self) -> "SceneScript":
        if self.action is None and not self.dialogues:
            raise ValueError("每场至少需要动作或对白")
        return self


class EpisodeScript(StrictScriptModel):
    episode_number: int = Field(ge=1, le=10)
    title: ChineseText
    duration_seconds: int = Field(ge=60, le=180)
    episode_goal: ChineseText
    opening_hook: ChineseText
    scenes: list[SceneScript] = Field(min_length=3, max_length=8)
    ending_hook: ChineseText

    @model_validator(mode="after")
    def validate_script_context(self, info: ValidationInfo) -> "EpisodeScript":
        scene_numbers = [scene.scene_number for scene in self.scenes]
        if scene_numbers != list(range(1, len(self.scenes) + 1)):
            raise ValueError("scene_number 必须从 1 连续排列")

        context = info.context or {}
        expected_episode_number = context.get("expected_episode_number")
        if (
            expected_episode_number is not None
            and self.episode_number != expected_episode_number
        ):
            raise ValueError("episode_number 与请求不一致")

        target_duration_seconds = context.get("target_duration_seconds")
        if (
            target_duration_seconds is not None
            and abs(self.duration_seconds - int(target_duration_seconds)) > 3
        ):
            raise ValueError("duration_seconds 与目标时长偏差超过 3 秒")

        allowed_character_ids = context.get("allowed_character_ids")
        if allowed_character_ids is not None:
            used_character_ids = {
                character_id
                for scene in self.scenes
                for character_id in scene.characters
            }
            used_character_ids.update(
                dialogue.character_id
                for scene in self.scenes
                for dialogue in scene.dialogues
            )
            if used_character_ids - set(allowed_character_ids):
                raise ValueError("剧本包含大纲之外的 character_id")

        return self


class ScriptGenerateRequest(StrictScriptModel):
    target_duration_seconds: int = Field(default=90, ge=60, le=180)


class ScriptResponse(StrictScriptModel):
    project_id: int
    episode_number: int
    status: str
    script: EpisodeScript
