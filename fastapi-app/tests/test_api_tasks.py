"""API layer tests (async, via httpx.AsyncClient)."""
import pytest

pytestmark = pytest.mark.asyncio


async def _create_user(client):
    resp = await client.post("/api/users", json={
        "username": "frank", "email": "frank@example.com", "password": "supersecret"
    })
    return resp.json()["data"]


async def _login(client, username="frank", password="supersecret"):
    resp = await client.post("/api/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200
    return resp.json()["data"]


async def _create_project(client, owner_id=None):
    # owner_id is ignored by the API now; the owner is the session user.
    resp = await client.post("/api/projects", json={"name": "Test Project"})
    return resp.json()["data"]


async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200


async def test_create_user_validation_error(client):
    resp = await client.post("/api/users", json={"username": "a"})
    assert resp.status_code == 422


async def test_full_task_crud_flow(client):
    user = await _create_user(client)
    await _login(client)
    project = await _create_project(client)

    create_resp = await client.post("/api/tasks", json={
        "title": "Implement login", "project_id": project["id"], "priority": "high"
    })
    assert create_resp.status_code == 201
    task = create_resp.json()["data"]
    assert task["status"] == "todo"

    patch_resp = await client.patch(f"/api/tasks/{task['id']}", json={"status": "in_progress"})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["data"]["status"] == "in_progress"

    delete_resp = await client.delete(f"/api/tasks/{task['id']}")
    assert delete_resp.status_code == 200

    missing_resp = await client.get(f"/api/tasks/{task['id']}")
    assert missing_resp.status_code == 404


async def test_task_list_filter_search_pagination(client):
    user = await _create_user(client)
    await _login(client)
    project = await _create_project(client)
    for i in range(5):
        await client.post("/api/tasks", json={
            "title": f"Task number {i}", "project_id": project["id"],
            "status": "todo" if i % 2 == 0 else "done",
        })

    resp = await client.get("/api/tasks", params={
        "status": "done", "search": "Task", "page": 1, "page_size": 2
    })
    body = resp.json()
    assert resp.status_code == 200
    assert body["meta"]["page_size"] == 2
    assert all(t["status"] == "done" for t in body["data"])


async def test_report_generation_async(client):
    user = await _create_user(client)
    await _login(client)
    project = await _create_project(client)
    await client.post("/api/tasks", json={"title": "T1", "project_id": project["id"]})

    resp = await client.get(f"/api/reports/async/projects/{project['id']}")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total_tasks"] == 1
    assert "generated_in_seconds" in data
