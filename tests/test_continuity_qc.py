from app.schemas.script import EpisodeScript
from app.services.continuity_qc import evaluate_script_rules
from tests.fakes import valid_script_data


def test_rule_qc_flags_too_many_scenes_for_target_duration() -> None:
    data = valid_script_data()
    data["scenes"] = [
        {
            **data["scenes"][0],
            "scene_number": number,
        }
        for number in range(1, 7)
    ]
    script = EpisodeScript.model_validate(data)

    issues = evaluate_script_rules(script, target_duration_seconds=90)

    assert [issue.code for issue in issues] == ["episode_overloaded"]
    assert issues[0].severity == "warning"


def test_rule_qc_flags_dialogue_character_missing_from_scene_cast() -> None:
    data = valid_script_data()
    data["scenes"][0]["characters"] = ["lin_feng"]
    data["scenes"][0]["dialogues"][0]["character_id"] = "su_yan"
    data["scenes"][0]["dialogues"][0]["character_name"] = "苏妍"
    script = EpisodeScript.model_validate(
        data,
        context={"allowed_character_ids": {"lin_feng", "su_yan", "gao_qi"}},
    )

    issues = evaluate_script_rules(script, target_duration_seconds=90)

    assert [issue.code for issue in issues] == ["scene_character_mismatch"]
    assert issues[0].severity == "error"
