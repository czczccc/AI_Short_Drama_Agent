import json

from fastapi.testclient import TestClient

from app.api.main import app
from app.models.project import Project
from app.providers.llm.base import LLMCallError
from app.providers.llm.factory import get_configured_llm_provider
from app.schemas.character import CharacterBibleCollection
from tests.fakes import FakeLLMProvider, FailingLLMProvider


API_PREFIX = "/api/v1"


def create_project(client: TestClient) -> int:
    response = client.post(f"{API_PREFIX}/projects", json={"name": "角色测试"})
    assert response.status_code == 201
    return response.json()["id"]


def create_outline_ready_project(client: TestClient) -> int:
    project_id = create_project(client)
    app.dependency_overrides[get_configured_llm_provider] = FakeLLMProvider
    response = client.post(
        f"{API_PREFIX}/projects/{project_id}/outline",
        json={"idea": "程序员发现老板窃取了他的AI成果", "episode_count": 10},
    )
    assert response.status_code == 200
    return project_id


def generate_characters(client: TestClient, project_id: int, provider=None):
    app.dependency_overrides[get_configured_llm_provider] = (
        provider or FakeLLMProvider
    )
    return client.post(
        f"{API_PREFIX}/projects/{project_id}/characters/generate",
        json={},
    )


def test_generate_all_character_bibles_validates_and_persists(
    client: TestClient, test_session_local
) -> None:
    project_id = create_outline_ready_project(client)

    response = generate_characters(client, project_id)

    assert response.status_code == 200
    body = response.json()
    characters = body["characters"]
    assert body["project_id"] == project_id
    assert body["status"] == "characters_ready"
    assert set(characters) == {"lin_feng", "su_yan", "gao_qi"}
    assert len(characters) == 3
    for character_id, bible in characters.items():
        assert bible["character_id"] == character_id
        assert bible["speech_style"]
        assert bible["behavior_boundaries"]
        assert bible["continuity_rules"]["must_keep"]
        assert all(
            relationship["target_character_id"] in characters
            and relationship["target_character_id"] != character_id
            for relationship in bible["relationships"]
        )

    with test_session_local() as db:
        project = db.get(Project, project_id)
        assert project is not None
        assert project.status == "characters_ready"
        assert json.loads(project.characters_json) == characters


def test_get_saved_character_bibles(client: TestClient) -> None:
    project_id = create_outline_ready_project(client)
    assert generate_characters(client, project_id).status_code == 200

    response = client.get(f"{API_PREFIX}/projects/{project_id}/characters")

    assert response.status_code == 200
    assert response.json()["characters"]["lin_feng"]["name"] == "林峰"


def test_put_replaces_and_persists_character_bibles(
    client: TestClient, test_session_local
) -> None:
    project_id = create_outline_ready_project(client)
    generated = generate_characters(client, project_id).json()["characters"]
    generated["lin_feng"]["speech_style"] = "说话始终简短冷静，不使用网络流行语。"

    response = client.put(
        f"{API_PREFIX}/projects/{project_id}/characters",
        json={"characters": generated},
    )

    assert response.status_code == 200
    assert (
        response.json()["characters"]["lin_feng"]["speech_style"]
        == "说话始终简短冷静，不使用网络流行语。"
    )
    with test_session_local() as db:
        project = db.get(Project, project_id)
        saved = json.loads(project.characters_json)
        assert saved["lin_feng"]["speech_style"] == response.json()["characters"][
            "lin_feng"
        ]["speech_style"]


def test_put_rejects_character_set_not_matching_outline(client: TestClient) -> None:
    project_id = create_outline_ready_project(client)
    characters = generate_characters(client, project_id).json()["characters"]
    characters["new_person"] = {
        **characters["lin_feng"],
        "character_id": "new_person",
        "name": "新增人物",
    }

    response = client.put(
        f"{API_PREFIX}/projects/{project_id}/characters",
        json={"characters": characters},
    )

    assert response.status_code == 422


def test_generate_characters_returns_404_for_missing_project(
    client: TestClient,
) -> None:
    response = generate_characters(client, 999999)
    assert response.status_code == 404
    assert response.json() == {"detail": "Project not found"}


def test_generate_characters_returns_409_without_outline(client: TestClient) -> None:
    project_id = create_project(client)
    response = generate_characters(client, project_id)
    assert response.status_code == 409


def test_get_returns_404_before_characters_are_generated(client: TestClient) -> None:
    project_id = create_outline_ready_project(client)
    response = client.get(f"{API_PREFIX}/projects/{project_id}/characters")
    assert response.status_code == 404
    assert response.json() == {"detail": "Character bibles not found"}


def test_generate_characters_maps_provider_failure_to_502(
    client: TestClient,
) -> None:
    project_id = create_outline_ready_project(client)
    provider = lambda: FailingLLMProvider(LLMCallError("secret upstream detail"))

    response = generate_characters(client, project_id, provider)

    assert response.status_code == 502
    assert "secret upstream detail" not in response.text


def test_generate_characters_rejects_model_added_character(
    client: TestClient,
) -> None:
    project_id = create_outline_ready_project(client)
    provider = lambda: FakeLLMProvider(character_mode="add")

    response = generate_characters(client, project_id, provider)

    assert response.status_code == 502


def test_generate_characters_rejects_model_missing_character(
    client: TestClient,
) -> None:
    project_id = create_outline_ready_project(client)
    provider = lambda: FakeLLMProvider(character_mode="drop")

    response = generate_characters(client, project_id, provider)

    assert response.status_code == 502


def test_generate_characters_retries_once_after_context_mismatch(
    client: TestClient,
) -> None:
    project_id = create_outline_ready_project(client)

    class RepairingCharacterProvider(FakeLLMProvider):
        def __init__(self) -> None:
            super().__init__()
            self.character_calls = 0

        def generate_structured(self, system_prompt, user_prompt, output_schema):
            if output_schema is CharacterBibleCollection:
                self.character_calls += 1
                self.character_mode = "add" if self.character_calls == 1 else "valid"
            return super().generate_structured(
                system_prompt,
                user_prompt,
                output_schema,
            )

    provider = RepairingCharacterProvider()
    response = generate_characters(client, project_id, lambda: provider)

    assert response.status_code == 200
    assert provider.character_calls == 2
    assert "unexpected_character_ids" in provider.last_user_prompt
