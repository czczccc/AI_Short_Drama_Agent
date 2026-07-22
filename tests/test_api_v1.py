from collections.abc import Iterator

from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.api.main import app
from app.database.session import get_db
from app.providers.llm.factory import get_configured_llm_provider
from tests.fakes import FakeLLMProvider


API_PREFIX = "/api/v1"


def test_v1_health_endpoint_returns_json(client: TestClient) -> None:
    response = client.get(f"{API_PREFIX}/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_v1_exposes_existing_project_outline_and_script_workflow(
    client: TestClient,
) -> None:
    app.dependency_overrides[get_configured_llm_provider] = FakeLLMProvider

    created = client.post(f"{API_PREFIX}/projects", json={"name": "前端联调项目"})
    assert created.status_code == 201
    project_id = created.json()["id"]

    fetched = client.get(f"{API_PREFIX}/projects/{project_id}")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "前端联调项目"

    outline = client.post(
        f"{API_PREFIX}/projects/{project_id}/outline",
        json={"idea": "程序员发现老板窃取了他的AI成果", "episode_count": 10},
    )
    assert outline.status_code == 200
    assert outline.json()["status"] == "outline_ready"

    generated = client.post(
        f"{API_PREFIX}/projects/{project_id}/episodes/1/script",
        json={"target_duration_seconds": 90},
    )
    assert generated.status_code == 200
    assert generated.json()["script"]["episode_number"] == 1

    stored = client.get(f"{API_PREFIX}/projects/{project_id}/episodes/1/script")
    assert stored.status_code == 200
    assert stored.json()["status"] == "script_ready"


def test_v1_project_input_rejects_blank_name_and_extra_fields(
    client: TestClient,
) -> None:
    blank = client.post(f"{API_PREFIX}/projects", json={"name": "   "})
    extra = client.post(
        f"{API_PREFIX}/projects",
        json={"name": "测试项目", "unexpected": "不允许"},
    )

    assert blank.status_code == 422
    assert extra.status_code == 422


def test_v1_returns_404_for_missing_project(client: TestClient) -> None:
    response = client.get(f"{API_PREFIX}/projects/999999")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")


def test_openapi_publishes_only_canonical_v1_routes(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]

    assert f"{API_PREFIX}/health" in paths
    assert f"{API_PREFIX}/projects" in paths
    assert f"{API_PREFIX}/projects/{{project_id}}/outline" in paths
    assert (
        f"{API_PREFIX}/projects/{{project_id}}/episodes/{{episode_number}}/script"
        in paths
    )
    assert "/projects" not in paths
    assert "/health" not in paths


def test_openapi_documents_common_error_responses(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]

    project_create = paths[f"{API_PREFIX}/projects"]["post"]["responses"]
    project_read = paths[f"{API_PREFIX}/projects/{{project_id}}"]["get"]["responses"]
    outline_create = paths[f"{API_PREFIX}/projects/{{project_id}}/outline"]["post"][
        "responses"
    ]
    script_create = paths[
        f"{API_PREFIX}/projects/{{project_id}}/episodes/{{episode_number}}/script"
    ]["post"]["responses"]

    assert {"201", "422", "500"} <= set(project_create)
    assert {"200", "404", "422", "500"} <= set(project_read)
    assert {"200", "404", "422", "500", "502", "503"} <= set(outline_create)
    assert {"200", "404", "409", "422", "500", "502", "503"} <= set(
        script_create
    )


def test_cors_allows_configured_local_frontend(client: TestClient) -> None:
    response = client.options(
        f"{API_PREFIX}/projects",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_does_not_allow_unconfigured_origin(client: TestClient) -> None:
    response = client.options(
        f"{API_PREFIX}/projects",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert "access-control-allow-origin" not in response.headers


class CommitFailingSession:
    def add(self, instance: object) -> None:
        pass

    def commit(self) -> None:
        raise SQLAlchemyError("private database detail")


def _get_failing_db() -> Iterator[CommitFailingSession]:
    yield CommitFailingSession()


def test_database_failure_returns_clean_json_error() -> None:
    previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = _get_failing_db
    try:
        with TestClient(app, raise_server_exceptions=False) as isolated_client:
            response = isolated_client.post(
                f"{API_PREFIX}/projects",
                json={"name": "数据库故障测试"},
            )
    finally:
        if previous_override is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous_override

    assert response.status_code == 500
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {"detail": "数据库操作失败"}
    assert "private database detail" not in response.text
