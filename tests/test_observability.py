from pathlib import Path

from fastapi.testclient import TestClient

from app.configs.settings import get_settings
from app.observability.logging import (
    configure_logging,
    log_event,
    read_recent_logs,
    set_request_id,
    reset_request_id,
)


def test_log_event_writes_structured_jsonl_with_request_id(tmp_path: Path) -> None:
    log_file = tmp_path / "app.jsonl"
    configure_logging(str(log_file))
    token = set_request_id("req-test-1")
    try:
        log_event(
            "workflow.test.event",
            project_id=123,
            prompt="should not be logged",
            deepseek_api_key="should not be logged",
        )
    finally:
        reset_request_id(token)

    records = read_recent_logs(log_file_path=str(log_file))

    assert len(records) == 1
    assert records[0]["event"] == "workflow.test.event"
    assert records[0]["request_id"] == "req-test-1"
    assert records[0]["project_id"] == 123
    assert "prompt" not in records[0]
    assert "deepseek_api_key" not in records[0]


def test_http_requests_get_request_id_and_structured_log(
    client: TestClient,
    tmp_path: Path,
) -> None:
    log_file = tmp_path / "app.jsonl"
    configure_logging(str(log_file))

    response = client.get(
        "/api/v1/health",
        headers={"X-Request-ID": "manual-request-id"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "manual-request-id"
    records = read_recent_logs(log_file_path=str(log_file))
    assert any(
        record["event"] == "http.request.completed"
        and record["request_id"] == "manual-request-id"
        and record["path"] == "/api/v1/health"
        and record["status_code"] == 200
        for record in records
    )


def test_dev_logs_endpoint_returns_recent_logs_filtered_by_project(
    client: TestClient,
    tmp_path: Path,
) -> None:
    log_file = tmp_path / "app.jsonl"
    original_log_file_path = get_settings().log_file_path
    get_settings().log_file_path = str(log_file)
    configure_logging(str(log_file))
    log_event("workflow.project.created", project_id=1)
    log_event("workflow.project.created", project_id=2)

    try:
        response = client.get("/dev/logs", params={"project_id": 2, "limit": 10})
    finally:
        get_settings().log_file_path = original_log_file_path

    assert response.status_code == 200
    logs = response.json()["logs"]
    assert [record["project_id"] for record in logs] == [2]
