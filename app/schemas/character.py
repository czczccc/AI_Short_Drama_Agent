from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, model_validator

from app.schemas.outline import CharacterConcept, CharacterId, ChineseText


class StrictCharacterModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class VisualIdentity(StrictCharacterModel):
    face_features: ChineseText
    hair: ChineseText
    body_type: ChineseText
    default_costume: ChineseText
    signature_colors: ChineseText
    signature_props: ChineseText


class CharacterRelationship(StrictCharacterModel):
    target_character_id: CharacterId
    relationship_type: ChineseText
    public_attitude: ChineseText
    private_attitude: ChineseText
    conflict: ChineseText


class ContinuityRules(StrictCharacterModel):
    must_keep: list[ChineseText] = Field(min_length=1)
    must_avoid: list[ChineseText] = Field(min_length=1)


class CharacterBible(StrictCharacterModel):
    character_id: CharacterId
    name: ChineseText
    role: ChineseText
    age: ChineseText
    background: ChineseText
    appearance: ChineseText
    personality: ChineseText
    motivation: ChineseText
    fear: ChineseText
    secret: ChineseText
    speech_style: ChineseText
    behavior_patterns: list[ChineseText] = Field(min_length=1)
    emotional_triggers: list[ChineseText] = Field(min_length=1)
    behavior_boundaries: list[ChineseText] = Field(min_length=1)
    relationships: list[CharacterRelationship] = Field(min_length=1)
    character_arc: ChineseText
    visual_identity: VisualIdentity
    continuity_rules: ContinuityRules


class CharacterBibleCollection(StrictCharacterModel):
    characters: dict[CharacterId, CharacterBible] = Field(min_length=3, max_length=6)

    @model_validator(mode="after")
    def validate_character_context(
        self, info: ValidationInfo
    ) -> "CharacterBibleCollection":
        character_ids = set(self.characters)
        value_ids = [bible.character_id for bible in self.characters.values()]

        if len(value_ids) != len(set(value_ids)):
            raise ValueError("character_id 不允许重复")
        if any(key != bible.character_id for key, bible in self.characters.items()):
            raise ValueError("characters 的 key 必须与 character_id 一致")

        for source_id, bible in self.characters.items():
            for relationship in bible.relationships:
                target_id = relationship.target_character_id
                if target_id == source_id:
                    raise ValueError("角色关系不允许引用自己")
                if target_id not in character_ids:
                    raise ValueError("角色关系引用了不存在的 character_id")

        outline_characters: list[CharacterConcept] | None = (info.context or {}).get(
            "outline_characters"
        )
        if outline_characters is None:
            return self

        expected = {
            character.character_id: character for character in outline_characters
        }
        if character_ids != set(expected):
            raise ValueError("角色ID集合必须与故事大纲完全一致")

        for character_id, bible in self.characters.items():
            concept = expected[character_id]
            if (bible.name, bible.role, bible.age) != (
                concept.name,
                concept.role,
                concept.age,
            ):
                raise ValueError("角色姓名、年龄和定位不得与故事大纲冲突")

        return self


class CharacterGenerateRequest(StrictCharacterModel):
    pass


class CharacterBibleUpdateRequest(CharacterBibleCollection):
    pass


class CharacterBibleResponse(StrictCharacterModel):
    project_id: int
    status: str
    characters: dict[CharacterId, CharacterBible]
