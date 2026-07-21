import pytest
from pydantic import ValidationError

from app.schemas.script import EpisodeScript
from tests.fakes import valid_script_data


def validate_script(data: dict, episode_number: int = 1) -> EpisodeScript:
    return EpisodeScript.model_validate(
        data,
        context={
            "expected_episode_number": episode_number,
            "allowed_character_ids": {"lin_feng", "su_yan", "gao_qi"},
        },
    )


def test_episode_script_accepts_common_abbreviations() -> None:
    script = validate_script(valid_script_data(title="AI证据争夺战"))

    assert script.title == "AI证据争夺战"


def test_episode_script_requires_requested_episode_number() -> None:
    with pytest.raises(ValidationError):
        validate_script(valid_script_data(episode_number=2), episode_number=1)


def test_episode_script_requires_continuous_scene_numbers() -> None:
    data = valid_script_data()
    data["scenes"][1]["scene_number"] = 3

    with pytest.raises(ValidationError):
        validate_script(data)


def test_episode_script_rejects_unknown_character_ids() -> None:
    data = valid_script_data()
    data["scenes"][0]["dialogues"][0]["character_id"] = "unknown_person"

    with pytest.raises(ValidationError):
        validate_script(data)


def test_scene_requires_action_or_dialogue() -> None:
    data = valid_script_data()
    data["scenes"][0]["action"] = None
    data["scenes"][0]["dialogues"] = []

    with pytest.raises(ValidationError):
        validate_script(data)
