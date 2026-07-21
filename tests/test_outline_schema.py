import pytest
from pydantic import ValidationError

from app.schemas.outline import StoryOutline
from tests.fakes import valid_outline_data


def test_story_outline_requires_exactly_ten_episodes() -> None:
    data = valid_outline_data()
    data["episodes"] = data["episodes"][:-1]

    with pytest.raises(ValidationError):
        StoryOutline.model_validate(data)


def test_story_outline_requires_continuous_episode_numbers() -> None:
    data = valid_outline_data()
    data["episodes"][4]["episode_number"] = 7

    with pytest.raises(ValidationError):
        StoryOutline.model_validate(data)


def test_story_outline_rejects_extra_fields() -> None:
    data = valid_outline_data()
    data["unexpected"] = "不允许"

    with pytest.raises(ValidationError):
        StoryOutline.model_validate(data)


def test_story_outline_allows_common_abbreviations_in_chinese_content() -> None:
    data = valid_outline_data()
    data["title"] = "AI逆袭"

    outline = StoryOutline.model_validate(data)

    assert outline.title == "AI逆袭"
