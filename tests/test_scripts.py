import json

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.main import app
from app.models.project import Project
from app.providers.llm.base import LLMCallError
from app.providers.llm.factory import get_configured_llm_provider
from tests.fakes import FakeLLMProvider, FailingLLMProvider, valid_script_data


def create_project(client: TestClient) -> int:
    response = client.post("/projects", json={"name": "剧本测试"})
    assert response.status_code == 201
    return response.json()["id"]


def create_outline_ready_project(client: TestClient) -> int:
    project_id = create_project(client)
    app.dependency_overrides[get_configured_llm_provider] = FakeLLMProvider
    response = client.post(
        f"/projects/{project_id}/outline",
        json={"idea": "程序员发现老板窃取了他的AI成果", "episode_count": 10},
    )
    assert response.status_code == 200
    return project_id


def generate_script(
    client: TestClient,
    project_id: int,
    episode_number: int = 1,
    provider=None,
):
    app.dependency_overrides[get_configured_llm_provider] = (
        provider or FakeLLMProvider
    )
    return client.post(
        f"/projects/{project_id}/episodes/{episode_number}/script",
        json={"target_duration_seconds": 90},
    )


def test_generate_first_script_validates_updates_and_persists(
    client: TestClient, test_session_local
) -> None:
    project_id = create_outline_ready_project(client)

    response = generate_script(client, project_id)

    assert response.status_code == 200
    body = response.json()
    script = body["script"]
    assert body["project_id"] == project_id
    assert body["episode_number"] == 1
    assert body["status"] == "script_ready"
    assert script["episode_number"] == 1
    assert [scene["scene_number"] for scene in script["scenes"]] == [1, 2, 3]

    allowed_ids = {"lin_feng", "su_yan", "gao_qi"}
    used_ids = {
        dialogue["character_id"]
        for scene in script["scenes"]
        for dialogue in scene["dialogues"]
    }
    assert used_ids <= allowed_ids

    with test_session_local() as db:
        project = db.scalar(select(Project).where(Project.id == project_id))
        assert project is not None
        assert project.status == "script_ready"
        scripts = json.loads(project.scripts_json)
        assert scripts["1"]["title"] == script["title"]
        memory = json.loads(project.memory_json)
        assert memory["episodes"]["1"]["episode_number"] == 1
        assert memory["episodes"]["1"]["summary"] == script["episode_goal"]
        assert script["ending_hook"] in memory["episodes"]["1"]["ending_hook"]


def test_regenerating_episode_overwrites_only_that_episode(
    client: TestClient, test_session_local
) -> None:
    project_id = create_outline_ready_project(client)
    first_provider = lambda: FakeLLMProvider(script_title="旧版剧本")
    second_provider = lambda: FakeLLMProvider(script_title="新版剧本")
    assert generate_script(client, project_id, provider=first_provider).status_code == 200

    response = generate_script(client, project_id, provider=second_provider)

    assert response.status_code == 200
    with test_session_local() as db:
        project = db.get(Project, project_id)
        scripts = json.loads(project.scripts_json)
        assert list(scripts) == ["1"]
        assert scripts["1"]["title"] == "新版剧本"


def test_generating_second_episode_preserves_first(
    client: TestClient, test_session_local
) -> None:
    project_id = create_outline_ready_project(client)
    assert generate_script(client, project_id).status_code == 200
    second_provider = lambda: FakeLLMProvider(script_episode_number=2)

    response = generate_script(client, project_id, 2, second_provider)

    assert response.status_code == 200
    with test_session_local() as db:
        project = db.get(Project, project_id)
        scripts = json.loads(project.scripts_json)
        assert set(scripts) == {"1", "2"}
        assert scripts["1"]["episode_number"] == 1
        assert scripts["2"]["episode_number"] == 2
        memory = json.loads(project.memory_json)
        assert set(memory["episodes"]) == {"1", "2"}


def test_get_saved_script(client: TestClient) -> None:
    project_id = create_outline_ready_project(client)
    assert generate_script(client, project_id).status_code == 200

    response = client.get(f"/projects/{project_id}/episodes/1/script")

    assert response.status_code == 200
    assert response.json()["script"]["episode_number"] == 1


def test_generate_script_returns_404_for_missing_project(client: TestClient) -> None:
    response = generate_script(client, 999999)
    assert response.status_code == 404


def test_generate_script_returns_409_without_outline(client: TestClient) -> None:
    project_id = create_project(client)
    response = generate_script(client, project_id)
    assert response.status_code == 409


def test_generate_script_returns_404_for_missing_episode(client: TestClient) -> None:
    project_id = create_outline_ready_project(client)
    response = generate_script(client, project_id, 11)
    assert response.status_code == 404


def test_generate_script_maps_provider_failure_to_502(client: TestClient) -> None:
    project_id = create_outline_ready_project(client)
    provider = lambda: FailingLLMProvider(LLMCallError("secret upstream detail"))

    response = generate_script(client, project_id, provider=provider)

    assert response.status_code == 502
    assert "secret" not in response.text


def test_generate_script_maps_context_schema_failure_to_502(
    client: TestClient,
) -> None:
    project_id = create_outline_ready_project(client)
    provider = lambda: FakeLLMProvider(script_character_id="unknown_person")

    response = generate_script(client, project_id, provider=provider)

    assert response.status_code == 502


def test_generate_script_rejects_llm_duration_outside_target_tolerance(
    client: TestClient,
) -> None:
    project_id = create_outline_ready_project(client)
    provider = lambda: FakeLLMProvider(script_duration_seconds=95)

    response = generate_script(client, project_id, provider=provider)

    assert response.status_code == 502


def test_generate_script_accepts_llm_singular_dialogue_key(
    client: TestClient,
) -> None:
    project_id = create_outline_ready_project(client)
    provider = lambda: FakeLLMProvider(script_dialogue_key="dialogue")

    response = generate_script(client, project_id, provider=provider)

    assert response.status_code == 200
    script = response.json()["script"]
    assert "dialogues" in script["scenes"][0]
    assert "dialogue" not in script["scenes"][0]


def test_generate_script_rejects_invalid_duration(client: TestClient) -> None:
    project_id = create_outline_ready_project(client)
    response = client.post(
        f"/projects/{project_id}/episodes/1/script",
        json={"target_duration_seconds": 30},
    )
    assert response.status_code == 422


def test_writer_uses_character_bibles_when_available(client: TestClient) -> None:
    project_id = create_outline_ready_project(client)
    app.dependency_overrides[get_configured_llm_provider] = FakeLLMProvider
    characters = client.post(
        f"/projects/{project_id}/characters/generate",
        json={},
    )
    assert characters.status_code == 200

    writer_provider = FakeLLMProvider()
    response = generate_script(
        client,
        project_id,
        provider=lambda: writer_provider,
    )

    assert response.status_code == 200
    writer_input = json.loads(writer_provider.last_user_prompt)
    assert writer_input["character_source"] == "character_bible"
    assert all("speech_style" in character for character in writer_input["characters"])
    assert all(
        "continuity_rules" in character for character in writer_input["characters"]
    )


def test_writer_falls_back_to_outline_characters_when_bibles_are_absent(
    client: TestClient,
) -> None:
    project_id = create_outline_ready_project(client)
    writer_provider = FakeLLMProvider()

    response = generate_script(
        client,
        project_id,
        provider=lambda: writer_provider,
    )

    assert response.status_code == 200
    writer_input = json.loads(writer_provider.last_user_prompt)
    assert writer_input["character_source"] == "outline"
    assert all("speech_style" not in character for character in writer_input["characters"])


def test_writer_receives_episode_boundary_context_for_first_episode(
    client: TestClient,
) -> None:
    project_id = create_outline_ready_project(client)
    writer_provider = FakeLLMProvider()

    response = generate_script(
        client,
        project_id,
        provider=lambda: writer_provider,
    )

    assert response.status_code == 200
    writer_input = json.loads(writer_provider.last_user_prompt)
    assert writer_input["previous_episode_outline"] is None
    assert writer_input["current_episode_outline"]["episode_number"] == 1
    assert writer_input["next_episode_outline"]["episode_number"] == 2


def test_writer_receives_episode_boundary_context_for_middle_episode(
    client: TestClient,
) -> None:
    project_id = create_outline_ready_project(client)
    assert generate_script(client, project_id).status_code == 200
    writer_provider = FakeLLMProvider(script_episode_number=2)

    response = generate_script(
        client,
        project_id,
        episode_number=2,
        provider=lambda: writer_provider,
    )

    assert response.status_code == 200
    writer_input = json.loads(writer_provider.last_user_prompt)
    assert writer_input["previous_episode_outline"]["episode_number"] == 1
    assert writer_input["current_episode_outline"]["episode_number"] == 2
    assert writer_input["next_episode_outline"]["episode_number"] == 3
    assert "summary" not in writer_input["next_episode_outline"]
    assert [
        episode["episode_number"]
        for episode in writer_input["story_outline"]["episodes"]
    ] == [1, 2]
    assert writer_input["story_memory"]["episodes"]["1"]["episode_number"] == 1
    assert writer_input["story_memory"]["episodes"]["1"]["summary"]


def test_regenerating_episode_prunes_later_story_memory(
    client: TestClient,
    test_session_local,
) -> None:
    project_id = create_outline_ready_project(client)
    assert generate_script(client, project_id).status_code == 200
    assert (
        generate_script(
            client,
            project_id,
            episode_number=2,
            provider=lambda: FakeLLMProvider(script_episode_number=2),
        ).status_code
        == 200
    )

    response = generate_script(
        client,
        project_id,
        provider=lambda: FakeLLMProvider(script_title="重写第一集"),
    )

    assert response.status_code == 200
    with test_session_local() as db:
        project = db.get(Project, project_id)
        memory = json.loads(project.memory_json)
        assert set(memory["episodes"]) == {"1"}


def test_writer_receives_memory_backfilled_from_legacy_saved_scripts(
    client: TestClient,
    test_session_local,
) -> None:
    project_id = create_outline_ready_project(client)
    with test_session_local() as db:
        project = db.get(Project, project_id)
        project.scripts_json = json.dumps(
            {"1": valid_script_data()},
            ensure_ascii=False,
        )
        project.memory_json = None
        db.commit()

    writer_provider = FakeLLMProvider(script_episode_number=2)
    response = generate_script(
        client,
        project_id,
        episode_number=2,
        provider=lambda: writer_provider,
    )

    assert response.status_code == 200
    writer_input = json.loads(writer_provider.last_user_prompt)
    assert writer_input["story_memory"]["episodes"]["1"]["summary"]


def test_writer_uses_v2_prompt_with_continuity_guardrails(
    client: TestClient,
) -> None:
    project_id = create_outline_ready_project(client)
    writer_provider = FakeLLMProvider()

    response = generate_script(
        client,
        project_id,
        provider=lambda: writer_provider,
    )

    assert response.status_code == 200
    assert "Writer Agent v2" in writer_provider.last_system_prompt
    assert "后续集" in writer_provider.last_system_prompt
    assert "道具" in writer_provider.last_system_prompt
    assert "临时发明" in writer_provider.last_system_prompt
    assert "触发瞬间" in writer_provider.last_system_prompt
    assert "不能写入 `characters` 数组" in writer_provider.last_system_prompt
