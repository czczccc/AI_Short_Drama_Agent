import json

from fastapi.testclient import TestClient

from app.api.main import app
from app.providers.llm.factory import get_configured_llm_provider
from tests.fakes import FakeLLMProvider


def test_dev_testbench_serves_html(client: TestClient) -> None:
    response = client.get("/dev/testbench")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "AI Short Drama Testbench" in response.text
    assert 'apiBase = "/api/v1"' in response.text
    assert 'request("/projects"' in response.text
    assert "生成角色圣经" in response.text
    assert "生成剧本" in response.text
    assert "function escapeHtml" in response.text
    assert 'devBase = "/dev"' in response.text
    assert 'devRequest("/projects")' in response.text
    assert "上一集" in response.text
    assert "下一集" in response.text
    assert "Story Memory JSON" in response.text
    assert "QC Report JSON" in response.text
    assert "检查当前集 QC" in response.text
    assert "删除当前项目" in response.text
    assert 'method: "DELETE"' in response.text


def test_dev_testbench_is_not_in_openapi(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]

    assert "/dev/testbench" not in paths
    assert "/dev/projects" not in paths
    assert "/dev/logs" not in paths
    assert "/dev/projects/{project_id}" not in paths
    assert "/dev/projects/{project_id}/episodes/{episode_number}/qc" not in paths


def test_dev_projects_lists_saved_projects(client: TestClient) -> None:
    created = client.post("/api/v1/projects", json={"name": "历史项目"})
    assert created.status_code == 201

    response = client.get("/dev/projects")

    assert response.status_code == 200
    projects = response.json()["projects"]
    assert any(project["name"] == "历史项目" for project in projects)


def test_dev_project_delete_removes_project_from_local_database(
    client: TestClient,
) -> None:
    created = client.post("/api/v1/projects", json={"name": "待删除项目"})
    assert created.status_code == 201
    project_id = created.json()["id"]

    deleted = client.delete(f"/dev/projects/{project_id}")

    assert deleted.status_code == 200
    assert deleted.json() == {"deleted_project_id": project_id}
    assert client.get(f"/dev/projects/{project_id}/state").status_code == 404
    projects = client.get("/dev/projects").json()["projects"]
    assert all(project["id"] != project_id for project in projects)


def test_dev_project_delete_returns_404_for_missing_project(
    client: TestClient,
) -> None:
    response = client.delete("/dev/projects/999999")

    assert response.status_code == 404


def test_dev_project_state_returns_saved_workflow_outputs(client: TestClient) -> None:
    app.dependency_overrides[get_configured_llm_provider] = FakeLLMProvider
    created = client.post("/api/v1/projects", json={"name": "历史剧本项目"})
    assert created.status_code == 201
    project_id = created.json()["id"]
    assert client.post(
        f"/api/v1/projects/{project_id}/outline",
        json={"idea": "程序员发现老板窃取了他的AI成果", "episode_count": 10},
    ).status_code == 200
    assert client.post(
        f"/api/v1/projects/{project_id}/characters/generate",
        json={},
    ).status_code == 200
    assert client.post(
        f"/api/v1/projects/{project_id}/episodes/1/script",
        json={"target_duration_seconds": 90},
    ).status_code == 200
    app.dependency_overrides[get_configured_llm_provider] = lambda: FakeLLMProvider(
        script_episode_number=2
    )
    assert client.post(
        f"/api/v1/projects/{project_id}/episodes/2/script",
        json={"target_duration_seconds": 90},
    ).status_code == 200

    response = client.get(f"/dev/projects/{project_id}/state")

    assert response.status_code == 200
    body = response.json()
    assert body["project"]["id"] == project_id
    assert body["outline"]["title"]
    assert set(body["scripts"]) == {"1", "2"}
    assert body["saved_episode_numbers"] == [1, 2]
    assert set(body["memory"]["episodes"]) == {"1", "2"}


def test_dev_episode_qc_returns_llm_report(client: TestClient) -> None:
    app.dependency_overrides[get_configured_llm_provider] = FakeLLMProvider
    created = client.post("/api/v1/projects", json={"name": "QC测试项目"})
    assert created.status_code == 201
    project_id = created.json()["id"]
    assert client.post(
        f"/api/v1/projects/{project_id}/outline",
        json={"idea": "程序员发现老板窃取了他的AI成果", "episode_count": 10},
    ).status_code == 200
    assert client.post(
        f"/api/v1/projects/{project_id}/characters/generate",
        json={},
    ).status_code == 200
    assert client.post(
        f"/api/v1/projects/{project_id}/episodes/1/script",
        json={"target_duration_seconds": 90},
    ).status_code == 200
    qc_provider = FakeLLMProvider()
    app.dependency_overrides[get_configured_llm_provider] = lambda: qc_provider

    response = client.post(f"/dev/projects/{project_id}/episodes/1/qc")

    assert response.status_code == 200
    body = response.json()
    assert body["project_id"] == project_id
    assert body["episode_number"] == 1
    assert body["report"]["status"] == "warning"
    assert body["report"]["issues"][0]["code"] == "future_boundary_risk"
    assert qc_provider.last_user_prompt is not None
    qc_input = json.loads(qc_provider.last_user_prompt)
    assert qc_input["story_memory"]["version"] == "story_memory_v2"
    assert qc_input["current_episode_outline"]["episode_number"] == 1
    assert {
        "scene_number": 1,
        "evidence_text": "电脑突然开始远程自毁，警报声逼近，林峰迅速复制关键文件。",
    } in qc_input["evidence_catalog"]
    assert qc_input["ending_state_reference"] == {
        "scene_number": 3,
        "location": "人工智能公司机房",
        "time_of_day": "深夜",
    }


def test_dev_episode_qc_returns_404_when_script_missing(client: TestClient) -> None:
    app.dependency_overrides[get_configured_llm_provider] = FakeLLMProvider
    created = client.post("/api/v1/projects", json={"name": "QC缺剧本项目"})
    assert created.status_code == 201
    project_id = created.json()["id"]
    assert client.post(
        f"/api/v1/projects/{project_id}/outline",
        json={"idea": "程序员发现老板窃取了他的AI成果", "episode_count": 10},
    ).status_code == 200

    response = client.post(f"/dev/projects/{project_id}/episodes/1/qc")

    assert response.status_code == 404
