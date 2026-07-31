import json

from fastapi.testclient import TestClient

from app.agents.showrunner import ShowrunnerAgent
from app.api.main import app
from app.models.project import Project
from app.providers.llm.base import LLMCallError
from app.providers.llm.factory import get_configured_llm_provider
from app.schemas.character import CharacterBibleCollection
from app.schemas.memory import StoryMemory
from app.schemas.outline import StoryOutline
from app.schemas.showrunner import ShowrunnerState
from app.services.showrunner_service import stable_json_sha256
from tests.fakes import (
    FakeLLMProvider,
    FailingLLMProvider,
    valid_character_bibles_data,
    valid_outline_data,
    valid_showrunner_state_data,
)
from tests.test_characters import create_outline_ready_project, generate_characters


API_PREFIX = "/api/v1"


def generate_showrunner(client: TestClient, project_id: int, provider=None):
    app.dependency_overrides[get_configured_llm_provider] = (
        provider or FakeLLMProvider
    )
    return client.post(f"{API_PREFIX}/projects/{project_id}/showrunner", json={})


def generate_writer_brief(
    client: TestClient,
    project_id: int,
    episode_number: int = 1,
    provider=None,
    target_duration_seconds: int = 90,
):
    default_provider = lambda: FakeLLMProvider(
        writer_brief_episode_number=episode_number
    )
    app.dependency_overrides[get_configured_llm_provider] = provider or default_provider
    return client.post(
        f"{API_PREFIX}/projects/{project_id}/episodes/{episode_number}/writer-brief",
        json={"target_duration_seconds": target_duration_seconds},
    )


def test_stable_json_sha256_ignores_dict_key_order() -> None:
    left = {"b": [2, 1], "a": {"y": "是", "x": 1}}
    right = {"a": {"x": 1, "y": "是"}, "b": [2, 1]}

    assert stable_json_sha256(left) == stable_json_sha256(right)


def test_generate_showrunner_state_validates_and_persists(
    client: TestClient, test_session_local
) -> None:
    project_id = create_outline_ready_project(client)
    assert generate_characters(client, project_id).status_code == 200

    response = generate_showrunner(client, project_id)

    assert response.status_code == 200
    body = response.json()
    showrunner = body["showrunner"]
    assert body["project_id"] == project_id
    assert showrunner["version"] == "showrunner_v1"
    assert showrunner["source_outline_hash"] == stable_json_sha256(
        valid_outline_data()
    )
    assert showrunner["source_characters_hash"] == stable_json_sha256(
        valid_character_bibles_data()
    )
    assert showrunner["writer_briefs"] == {}
    assert showrunner["qc_reports"] == {}
    assert len(showrunner["episode_plan"]) == 10
    assert set(arc["character_id"] for arc in showrunner["character_arcs"]) == {
        "lin_feng",
        "su_yan",
        "gao_qi",
    }

    with test_session_local() as db:
        project = db.get(Project, project_id)
        assert project is not None
        assert project.status == "characters_ready"
        assert json.loads(project.showrunner_json) == showrunner


def test_get_saved_showrunner_state(client: TestClient) -> None:
    project_id = create_outline_ready_project(client)
    assert generate_characters(client, project_id).status_code == 200
    assert generate_showrunner(client, project_id).status_code == 200

    response = client.get(f"{API_PREFIX}/projects/{project_id}/showrunner")

    assert response.status_code == 200
    assert response.json()["showrunner"]["story_bible"]["series_title"] == "逆光代码"


def test_get_returns_404_before_showrunner_is_generated(client: TestClient) -> None:
    project_id = create_outline_ready_project(client)
    assert generate_characters(client, project_id).status_code == 200

    response = client.get(f"{API_PREFIX}/projects/{project_id}/showrunner")

    assert response.status_code == 404
    assert response.json() == {"detail": "Showrunner state not found"}


def test_generate_showrunner_returns_404_for_missing_project(client: TestClient) -> None:
    response = generate_showrunner(client, 999999)

    assert response.status_code == 404
    assert response.json() == {"detail": "Project not found"}


def test_generate_showrunner_returns_409_without_outline(client: TestClient) -> None:
    response = client.post(f"{API_PREFIX}/projects", json={"name": "缺大纲项目"})
    project_id = response.json()["id"]

    response = generate_showrunner(client, project_id)

    assert response.status_code == 409
    assert response.json() == {"detail": "Project outline is not ready"}


def test_generate_showrunner_returns_409_without_character_bibles(
    client: TestClient,
) -> None:
    project_id = create_outline_ready_project(client)

    response = generate_showrunner(client, project_id)

    assert response.status_code == 409
    assert response.json() == {"detail": "Character bibles are not ready"}


def test_generate_showrunner_maps_provider_failure_to_502(client: TestClient) -> None:
    project_id = create_outline_ready_project(client)
    assert generate_characters(client, project_id).status_code == 200
    provider = lambda: FailingLLMProvider(LLMCallError("secret upstream detail"))

    response = generate_showrunner(client, project_id, provider)

    assert response.status_code == 502
    assert "secret upstream detail" not in response.text


def test_generate_showrunner_rejects_character_arc_set_not_matching_bibles(
    client: TestClient,
) -> None:
    project_id = create_outline_ready_project(client)
    assert generate_characters(client, project_id).status_code == 200
    provider = lambda: FakeLLMProvider(showrunner_mode="add_arc")

    response = generate_showrunner(client, project_id, provider)

    assert response.status_code == 502


def test_showrunner_state_prompt_removes_duplicate_and_visual_character_data() -> None:
    provider = FakeLLMProvider()

    ShowrunnerAgent(provider).generate_showrunner_state(
        outline=StoryOutline.model_validate(valid_outline_data()),
        characters=CharacterBibleCollection.model_validate(
            {"characters": valid_character_bibles_data()}
        ),
        source_outline_hash="0" * 64,
        source_characters_hash="1" * 64,
    )

    assert provider.last_user_prompt is not None
    outline_section = provider.last_user_prompt.split("story_outline:\n", 1)[1].split(
        "\ncharacter_bibles:", 1
    )[0]
    assert '"characters"' not in outline_section
    assert '"face_features"' not in provider.last_user_prompt
    assert '"signature_props"' in provider.last_user_prompt


def test_writer_brief_prompt_uses_adjacent_sparse_arc_turning_points() -> None:
    data = valid_showrunner_state_data()
    for arc in data["character_arcs"]:
        arc["episode_beats"] = [
            arc["episode_beats"][0],
            arc["episode_beats"][4],
            arc["episode_beats"][9],
        ]
    state = ShowrunnerState.model_validate(data)
    provider = FakeLLMProvider(writer_brief_episode_number=3)

    ShowrunnerAgent(provider).generate_writer_brief(
        state=state,
        episode_number=3,
        story_memory=StoryMemory(),
        target_duration_seconds=90,
    )

    assert provider.last_user_prompt is not None
    assert '"current_episode_beat": null' in provider.last_user_prompt
    assert '"latest_arc_beat"' in provider.last_user_prompt
    assert '"next_arc_beat"' in provider.last_user_prompt
    assert '"episode_number": 1' in provider.last_user_prompt
    assert '"episode_number": 5' in provider.last_user_prompt


def test_generate_writer_brief_validates_persists_and_preserves_other_briefs(
    client: TestClient, test_session_local
) -> None:
    project_id = create_outline_ready_project(client)
    assert generate_characters(client, project_id).status_code == 200
    assert generate_showrunner(client, project_id).status_code == 200

    first = generate_writer_brief(client, project_id, episode_number=1)
    second = generate_writer_brief(client, project_id, episode_number=2)

    assert first.status_code == 200
    assert second.status_code == 200
    first_brief = first.json()["brief"]
    second_brief = second.json()["brief"]
    assert first_brief["episode_number"] == 1
    assert second_brief["episode_number"] == 2
    assert second_brief["target_duration_seconds"] == 90
    assert second_brief["required_beats"]
    assert second_brief["forbidden_content"]

    with test_session_local() as db:
        project = db.get(Project, project_id)
        showrunner = json.loads(project.showrunner_json)
        assert set(showrunner["writer_briefs"]) == {"1", "2"}
        assert showrunner["writer_briefs"]["1"] == first_brief
        assert showrunner["writer_briefs"]["2"] == second_brief


def test_get_saved_writer_brief(client: TestClient) -> None:
    project_id = create_outline_ready_project(client)
    assert generate_characters(client, project_id).status_code == 200
    assert generate_showrunner(client, project_id).status_code == 200
    assert generate_writer_brief(client, project_id, episode_number=1).status_code == 200

    response = client.get(
        f"{API_PREFIX}/projects/{project_id}/episodes/1/writer-brief"
    )

    assert response.status_code == 200
    assert response.json()["brief"]["episode_number"] == 1


def test_get_writer_brief_returns_404_before_generation(client: TestClient) -> None:
    project_id = create_outline_ready_project(client)
    assert generate_characters(client, project_id).status_code == 200
    assert generate_showrunner(client, project_id).status_code == 200

    response = client.get(
        f"{API_PREFIX}/projects/{project_id}/episodes/1/writer-brief"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Writer brief not found"}


def test_generate_writer_brief_returns_404_without_showrunner_state(
    client: TestClient,
) -> None:
    project_id = create_outline_ready_project(client)
    assert generate_characters(client, project_id).status_code == 200

    response = generate_writer_brief(client, project_id, episode_number=1)

    assert response.status_code == 404
    assert response.json() == {"detail": "Showrunner state not found"}


def test_generate_writer_brief_returns_404_for_unknown_episode(
    client: TestClient,
) -> None:
    project_id = create_outline_ready_project(client)
    assert generate_characters(client, project_id).status_code == 200
    assert generate_showrunner(client, project_id).status_code == 200

    response = generate_writer_brief(client, project_id, episode_number=11)

    assert response.status_code == 404
    assert response.json() == {"detail": "Episode not found in showrunner plan"}


def test_generate_writer_brief_rejects_episode_mismatch(client: TestClient) -> None:
    project_id = create_outline_ready_project(client)
    assert generate_characters(client, project_id).status_code == 200
    assert generate_showrunner(client, project_id).status_code == 200
    provider = lambda: FakeLLMProvider(writer_brief_episode_number=2)

    response = generate_writer_brief(client, project_id, episode_number=1, provider=provider)

    assert response.status_code == 502
