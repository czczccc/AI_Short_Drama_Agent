import pytest
from pydantic import ValidationError

from app.schemas.character import CharacterBibleCollection
from app.schemas.outline import StoryOutline
from tests.fakes import valid_character_bibles_data, valid_outline_data


def validate_collection(characters: dict) -> CharacterBibleCollection:
    outline = StoryOutline.model_validate(valid_outline_data())
    return CharacterBibleCollection.model_validate(
        {"characters": characters},
        context={"outline_characters": outline.characters},
    )


def test_character_bible_accepts_complete_outline_character_set() -> None:
    collection = validate_collection(valid_character_bibles_data())

    assert set(collection.characters) == {"lin_feng", "su_yan", "gao_qi"}
    assert collection.characters["lin_feng"].speech_style
    assert collection.characters["lin_feng"].behavior_boundaries
    assert collection.characters["lin_feng"].continuity_rules.must_keep


def test_character_bible_rejects_added_character() -> None:
    characters = valid_character_bibles_data()
    characters["new_person"] = {
        **characters["lin_feng"],
        "character_id": "new_person",
        "name": "新增人物",
    }

    with pytest.raises(ValidationError):
        validate_collection(characters)


def test_character_bible_rejects_missing_character() -> None:
    characters = valid_character_bibles_data()
    characters.pop("su_yan")

    with pytest.raises(ValidationError):
        validate_collection(characters)


def test_character_bible_rejects_unknown_relationship_target() -> None:
    characters = valid_character_bibles_data()
    characters["lin_feng"]["relationships"][0]["target_character_id"] = (
        "unknown_person"
    )

    with pytest.raises(ValidationError):
        validate_collection(characters)


def test_character_bible_rejects_self_relationship() -> None:
    characters = valid_character_bibles_data()
    characters["lin_feng"]["relationships"][0]["target_character_id"] = "lin_feng"

    with pytest.raises(ValidationError):
        validate_collection(characters)


def test_character_bible_rejects_changed_outline_identity() -> None:
    characters = valid_character_bibles_data()
    characters["lin_feng"]["role"] = "无关配角"

    with pytest.raises(ValidationError):
        validate_collection(characters)


def test_character_bible_rejects_extra_fields() -> None:
    characters = valid_character_bibles_data()
    characters["lin_feng"]["mbti"] = "不需要"

    with pytest.raises(ValidationError):
        validate_collection(characters)
