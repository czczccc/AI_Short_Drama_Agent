from app.services.memory_service import build_episode_memory
from app.schemas.script import EpisodeScript
from tests.fakes import valid_script_data


def test_build_episode_memory_keeps_character_updates_scene_specific() -> None:
    script_data = valid_script_data()
    script_data["episode_goal"] = "林峰必须抢在高启之前取得服务器证据。"
    script_data["scenes"][0]["characters"] = ["lin_feng"]
    script_data["scenes"][0]["scene_goal"] = "林峰进入机房发现服务器正在自毁。"
    script_data["scenes"][1]["characters"] = ["gao_qi"]
    script_data["scenes"][1]["dialogues"][0]["character_id"] = "gao_qi"
    script_data["scenes"][1]["dialogues"][0]["character_name"] = "高启"
    script_data["scenes"][1]["scene_goal"] = "高启远程下令删除日志。"
    script_data["scenes"][2]["characters"] = ["lin_feng", "gao_qi"]
    script_data["scenes"][2]["scene_goal"] = "林峰截获高启删除日志的证据。"
    script = EpisodeScript.model_validate(script_data)

    memory = build_episode_memory(script)

    assert memory.character_updates["lin_feng"].knows == [
        "林峰进入机房发现服务器正在自毁。",
        "林峰截获高启删除日志的证据。",
    ]
    assert memory.character_updates["gao_qi"].knows == [
        "高启远程下令删除日志。",
        "林峰截获高启删除日志的证据。",
    ]
    assert (
        memory.character_updates["lin_feng"].current_goal
        == "林峰截获高启删除日志的证据。"
    )
    assert (
        memory.character_updates["gao_qi"].current_goal
        == "林峰截获高启删除日志的证据。"
    )
    assert memory.summary == script.episode_goal
    assert memory.unresolved_questions == [script.ending_hook]

