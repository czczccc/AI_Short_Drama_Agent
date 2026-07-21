import hashlib
import json
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.main import app
from app.models.project import Project
from app.providers.llm.base import (
    LLMCallError,
    LLMConfigurationError,
    LLMResponseJSONError,
    LLMResponseValidationError,
)
from app.providers.llm.factory import get_configured_llm_provider
from tests.fakes import FakeLLMProvider, FailingLLMProvider


def create_project(client: TestClient) -> int:
    response = client.post("/projects", json={"name": "大纲测试"})
    assert response.status_code == 201
    return response.json()["id"]


def test_generate_outline_updates_and_persists_project(
    client: TestClient, test_session_local
) -> None:
    project_id = create_project(client)
    app.dependency_overrides[get_configured_llm_provider] = FakeLLMProvider

    response = client.post(
        f"/projects/{project_id}/outline",
        json={"idea": "一个被公司开除的程序员发现老板窃取了他的人工智能成果", "episode_count": 10},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["project_id"] == project_id
    assert body["status"] == "outline_ready"
    assert len(body["outline"]["episodes"]) == 10
    assert [item["episode_number"] for item in body["outline"]["episodes"]] == list(
        range(1, 11)
    )

    with test_session_local() as db:
        saved = db.scalar(select(Project).where(Project.id == project_id))
        assert saved is not None
        assert saved.status == "outline_ready"
        assert saved.idea == "一个被公司开除的程序员发现老板窃取了他的人工智能成果"
        assert json.loads(saved.outline_json)["title"] == "逆光代码"


def test_generate_outline_returns_404_for_missing_project(client: TestClient) -> None:
    app.dependency_overrides[get_configured_llm_provider] = FakeLLMProvider
    response = client.post(
        "/projects/999999/outline", json={"idea": "一个足够完整的短剧创意", "episode_count": 10}
    )
    assert response.status_code == 404


def test_generate_outline_rejects_empty_idea(client: TestClient) -> None:
    project_id = create_project(client)
    app.dependency_overrides[get_configured_llm_provider] = FakeLLMProvider
    response = client.post(
        f"/projects/{project_id}/outline", json={"idea": "   ", "episode_count": 10}
    )
    assert response.status_code == 422


def test_generate_outline_maps_provider_failures(client: TestClient) -> None:
    errors = [
        (LLMCallError("secret upstream detail"), 502),
        (LLMResponseJSONError("raw response"), 502),
        (LLMResponseValidationError("raw validation"), 502),
        (LLMConfigurationError("bad provider"), 503),
    ]

    for error, expected_status in errors:
        project_id = create_project(client)
        app.dependency_overrides[get_configured_llm_provider] = lambda e=error: (
            FailingLLMProvider(e)
        )
        response = client.post(
            f"/projects/{project_id}/outline",
            json={"idea": "一个足够完整的短剧创意", "episode_count": 10},
        )
        assert response.status_code == expected_status
        assert "secret" not in response.text
        assert "raw" not in response.text


def test_formal_database_is_not_used_by_tests(formal_db_snapshot: str | None) -> None:
    formal_db = Path("data/app.db")
    current_digest = (
        hashlib.sha256(formal_db.read_bytes()).hexdigest()
        if formal_db.exists()
        else None
    )
    assert current_digest == formal_db_snapshot
