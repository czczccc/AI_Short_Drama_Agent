from types import SimpleNamespace

import pytest

from app.schemas.memory import EpisodeMemory, StoryMemory
from app.services.memory_service import build_episode_memory, upsert_episode_memory
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
    assert memory.source == "rule_extracted"
    assert memory.ending_state is not None
    assert memory.ending_state.location == script.scenes[-1].location
    assert memory.ending_state.time_of_day == script.scenes[-1].time_of_day
    assert memory.ending_state.situation == script.scenes[-1].scene_goal


def test_episode_memory_accepts_qc_approved_continuity_snapshot() -> None:
    memory = EpisodeMemory.model_validate(
        {
            "episode_number": 1,
            "source": "qc_approved",
            "summary": "林峰在机房取得了服务器日志。",
            "new_facts": ["林峰已经取得服务器日志。"],
            "revealed_secrets": [],
            "unresolved_questions": ["日志中出现的名字是谁。"],
            "character_updates": {
                "lin_feng": {
                    "appears": True,
                    "knows": ["服务器日志已经复制成功。"],
                    "current_goal": "查明日志中的名字。",
                    "relationship_changes": [],
                }
            },
            "props_and_evidence": [
                {
                    "name": "服务器日志",
                    "owner": "林峰",
                    "status": "已复制到离线硬盘",
                    "first_episode": 1,
                }
            ],
            "ending_state": {
                "location": "人工智能公司机房",
                "time_of_day": "深夜",
                "situation": "林峰看到日志中出现苏妍父亲的名字。",
            },
            "ending_hook": "日志中为什么会出现苏妍父亲的名字。",
        }
    )

    assert memory.source == "qc_approved"
    assert memory.props_and_evidence[0].owner == "林峰"
    assert memory.ending_state.situation.endswith("名字。")


def test_episode_memory_normalizes_blank_optional_character_goal() -> None:
    memory = EpisodeMemory.model_validate(
        {
            "episode_number": 1,
            "source": "qc_approved",
            "summary": "匿名来电者只通过电话出现。",
            "character_updates": {
                "tomorrow_caller": {
                    "appears": True,
                    "knows": [],
                    "current_goal": "  ",
                    "relationship_changes": [],
                }
            },
            "ending_hook": "匿名来电者再次拨入。",
        }
    )

    assert memory.character_updates["tomorrow_caller"].current_goal is None


def test_story_memory_v1_payload_loads_with_v2_compatibility_defaults() -> None:
    memory = StoryMemory.model_validate(
        {
            "episodes": {
                "1": {
                    "episode_number": 1,
                    "summary": "林峰已经进入机房。",
                    "new_facts": ["林峰进入机房。"],
                    "revealed_secrets": [],
                    "unresolved_questions": ["谁删除了日志。"],
                    "character_updates": {},
                    "props_and_evidence": [],
                    "ending_hook": "机房门外出现脚步声。",
                }
            }
        }
    )

    assert memory.version == "story_memory_v2"
    assert memory.episodes["1"].source == "rule_extracted"
    assert memory.episodes["1"].ending_state is None


def test_upsert_rejects_non_qc_approved_snapshot() -> None:
    script = EpisodeScript.model_validate(valid_script_data())
    memory = build_episode_memory(script)
    project = SimpleNamespace(memory_json=None, scripts_json=None)

    with pytest.raises(ValueError, match="source"):
        upsert_episode_memory(project, script, approved_memory=memory)
