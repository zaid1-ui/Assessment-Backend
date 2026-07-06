"""API layer tests."""
import json


def _create_user(client):
    resp = client.post("/api/users", json={
        "username": "dave", "email": "dave@example.com", "password": "supersecret"
    })
    return resp.get_json()["data"]


def _login(client, username="dave", password="supersecret"):
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200
    return resp.get_json()["data"]


def _create_project(client, owner_id=None):
    # owner_id is ignored by the API now; the owner is the session user.
    resp = client.post("/api/projects", json={"name": "Test Project"})
    return resp.get_json()["data"]


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200


def test_create_user_validation_error(client):
    resp = client.post("/api/users", json={"username": "a"})
    assert resp.status_code == 422
    assert resp.get_json()["success"] is False


def test_full_task_crud_flow(client):
    user = _create_user(client)
    _login(client)
    project = _create_project(client)

    create_resp = client.post("/api/tasks", json={
        "title": "Implement login", "project_id": project["id"], "priority": "high"
    })
    assert create_resp.status_code == 201
    task = create_resp.get_json()["data"]
    assert task["status"] == "todo"

    get_resp = client.get(f"/api/tasks/{task['id']}")
    assert get_resp.status_code == 200

    patch_resp = client.patch(f"/api/tasks/{task['id']}", json={"status": "in_progress"})
    assert patch_resp.status_code == 200
    assert patch_resp.get_json()["data"]["status"] == "in_progress"

    delete_resp = client.delete(f"/api/tasks/{task['id']}")
    assert delete_resp.status_code == 200

    missing_resp = client.get(f"/api/tasks/{task['id']}")
    assert missing_resp.status_code == 404


def test_task_list_filter_search_pagination(client):
    user = _create_user(client)
    _login(client)
    project = _create_project(client)
    for i in range(5):
        client.post("/api/tasks", json={
            "title": f"Task number {i}", "project_id": project["id"],
            "status": "todo" if i % 2 == 0 else "done",
        })

    resp = client.get("/api/tasks?status=done&search=Task&page=1&page_size=2")
    body = resp.get_json()
    assert resp.status_code == 200
    assert body["meta"]["page_size"] == 2
    assert all(t["status"] == "done" for t in body["data"])


def test_report_generation(client):
    user = _create_user(client)
    _login(client)
    project = _create_project(client)
    client.post("/api/tasks", json={"title": "T1", "project_id": project["id"]})

    resp = client.get(f"/api/reports/projects/{project['id']}")
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["total_tasks"] == 1
    assert "generated_in_seconds" in data
