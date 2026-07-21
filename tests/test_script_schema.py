import pytest
from pydantic import ValidationError

from app.schemas.script import EpisodeScript


def valid_script_data(episode_number: int = 1) -> dict:
    return {
        "episode_number": episode_number,
        "title": "AI证据争夺战",
        "duration_seconds": 90,
        "episode_goal": "林峰必须抢在高启之前取得服务器证据。",
        "opening_hook": "开场五秒内，林峰的电脑突然开始远程自毁。",
        "scenes": [
            {
                "scene_number": number,
                "location": "人工智能公司机房",
                "time_of_day": "深夜",
                "characters": ["lin_feng", "su_yan"],
                "scene_goal": f"完成第{number}步取证。",
                "action": "警报声逼近，林峰迅速复制关键文件。",
                "dialogues": [
                    {
                        "character_id": "lin_feng",
                        "character_name": "林峰",
                        "emotion": "紧张",
                        "line": "只剩十秒，必须拿到证据！",
                        "action_note": "手指飞快敲击键盘。",
                    }
                ],
                "transition": "画面切向不断缩短的倒计时。",
            }
            for number in range(1, 4)
        ],
        "ending_hook": "文件打开后，屏幕上竟出现苏妍父亲的名字。",
    }


def validate_script(data: dict, episode_number: int = 1) -> EpisodeScript:
    return EpisodeScript.model_validate(
        data,
        context={
            "expected_episode_number": episode_number,
            "allowed_character_ids": {"lin_feng", "su_yan", "gao_qi"},
        },
    )


def test_episode_script_accepts_common_abbreviations() -> None:
    script = validate_script(valid_script_data())

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
