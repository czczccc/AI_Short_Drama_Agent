from fastapi.testclient import TestClient


def test_create_project(client: TestClient) -> None:
    resp = client.post("/projects", json={"name": "测试短剧"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "测试短剧"
    assert body["status"] == "draft"
    assert body["id"] >= 1


def test_get_project(client: TestClient) -> None:
    created = client.post("/projects", json={"name": "查询测试"})
    assert created.status_code == 201
    pid = created.json()["id"]

    resp = client.get(f"/projects/{pid}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == pid
    assert body["name"] == "查询测试"


def test_get_project_not_found(client: TestClient) -> None:
    resp = client.get("/projects/999999")
    assert resp.status_code == 404
