import json

from fastapi.testclient import TestClient

from app.api.main import app
from app.models.project import Project
from app.providers.llm.base import LLMCallError
from app.providers.llm.factory import get_configured_llm_provider
from app.services.showrunner_service import stable_json_sha256
from tests.fakes import (
    FakeLLMProvider,
    FailingLLMProvider,
    valid_character_bibles_data,
    valid_outline_data,
)
from tests.test_characters import create_outline_ready_project, generate_characters


API_PREFIX = "/api/v1"


def generate_showrunner(client: TestClient, project_id: int, provider=None):
    app.dependency_overrides[get_configured_llm_provider] = (
        provider or FakeLLMProvider
    )
    return client.post(f"{API_PREFIX}/projects/{project_id}/showrunner", json={})


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
