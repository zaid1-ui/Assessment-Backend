"""Session authentication tests (async)."""
import pytest

pytestmark = pytest.mark.asyncio


async def _register(client, username="alice", email="alice@example.com", password="hunter22"):
    resp = await client.post("/api/users", json={"username": username, "email": email, "password": password})
    assert resp.status_code == 201
    return resp.json()["data"]


async def _login(client, username="alice", password="hunter22"):
    return await client.post("/api/auth/login", json={"username": username, "password": password})


async def test_login_success_sets_session(client):
    await _register(client)
    resp = await _login(client)
    assert resp.status_code == 200
    assert "session" in resp.cookies
    me = await client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["data"]["username"] == "alice"


async def test_login_wrong_password(client):
    await _register(client)
    resp = await _login(client, password="wrong")
    assert resp.status_code == 401


async def test_me_requires_login(client):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


async def test_tampered_cookie_rejected(client):
    await _register(client)
    await _login(client)
    # change the user id in the token: the HMAC signature no longer matches
    token = client.cookies.get("session")
    user_id, issued_at, sig = token.split(".")
    client.cookies.set("session", f"{int(user_id) + 1}.{issued_at}.{sig}")
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


async def test_logout_clears_session(client):
    await _register(client)
    await _login(client)
    resp = await client.post("/api/auth/logout")
    assert resp.status_code == 200
    client.cookies.clear()  # emulate browser honouring the delete-cookie header
    assert (await client.get("/api/auth/me")).status_code == 401


async def test_create_project_requires_login(client):
    resp = await client.post("/api/projects", json={"name": "Nope"})
    assert resp.status_code == 401


async def test_project_owner_is_session_user(client):
    user = await _register(client)
    await _login(client)
    resp = await client.post("/api/projects", json={"name": "Mine"})
    assert resp.status_code == 201
    assert resp.json()["data"]["owner_id"] == user["id"]


async def test_cannot_modify_someone_elses_project(client):
    await _register(client, "alice", "alice@example.com")
    await _login(client, "alice")
    project = (await client.post("/api/projects", json={"name": "Alice's"})).json()["data"]

    await _register(client, "bob", "bob@example.com", "hunter22")
    await _login(client, "bob")  # overwrites the session cookie
    assert (await client.patch(f"/api/projects/{project['id']}", json={"name": "Hacked"})).status_code == 403
    assert (await client.delete(f"/api/projects/{project['id']}")).status_code == 403


async def test_delete_user_requires_login(client):
    user = await _register(client)
    resp = await client.delete(f"/api/users/{user['id']}")
    assert resp.status_code == 401


async def test_cannot_delete_another_user(client):
    alice = await _register(client, "alice", "alice@example.com")
    await _register(client, "bob", "bob@example.com", "hunter22")
    await _login(client, "bob")
    assert (await client.delete(f"/api/users/{alice['id']}")).status_code == 403
    assert (await client.patch(f"/api/users/{alice['id']}", json={"username": "pwned"})).status_code == 403


async def test_can_delete_own_account(client):
    user = await _register(client)
    await _login(client)
    assert (await client.delete(f"/api/users/{user['id']}")).status_code == 200


async def test_users_see_only_their_own_projects_and_tasks(client):
    await _register(client, "alice", "alice@example.com")
    await _login(client, "alice")
    project = (await client.post("/api/projects", json={"name": "Alice's"})).json()["data"]
    await client.post("/api/tasks", json={"title": "Alice task", "project_id": project["id"]})

    await _register(client, "bob", "bob@example.com", "hunter22")
    await _login(client, "bob")  # overwrites session cookie
    assert (await client.get("/api/projects")).json()["data"] == []
    assert (await client.get("/api/tasks")).json()["data"] == []
    assert (await client.get(f"/api/projects/{project['id']}")).status_code == 403


async def test_assignee_can_see_assigned_task(client):
    bob = await _register(client, "bob", "bob@example.com")
    await _register(client, "alice", "alice@example.com")
    await _login(client, "alice")
    project = (await client.post("/api/projects", json={"name": "Alice's"})).json()["data"]
    await client.post("/api/tasks", json={
        "title": "For Bob", "project_id": project["id"], "assignee_id": bob["id"]
    })

    await _login(client, "bob", "hunter22")
    tasks = (await client.get("/api/tasks")).json()["data"]
    assert len(tasks) == 1 and tasks[0]["title"] == "For Bob"
    assert (await client.get("/api/projects")).json()["data"] == []
