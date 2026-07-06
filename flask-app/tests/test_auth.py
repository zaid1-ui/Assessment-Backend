"""Session authentication tests."""


def _register(client, username="alice", email="alice@example.com", password="hunter22"):
    resp = client.post("/api/users", json={"username": username, "email": email, "password": password})
    assert resp.status_code == 201
    return resp.get_json()["data"]


def _login(client, username="alice", password="hunter22"):
    return client.post("/api/auth/login", json={"username": username, "password": password})


def test_login_success_sets_session(client):
    _register(client)
    resp = _login(client)
    assert resp.status_code == 200
    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.get_json()["data"]["username"] == "alice"


def test_login_wrong_password(client):
    _register(client)
    resp = _login(client, password="wrong")
    assert resp.status_code == 401


def test_me_requires_login(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_logout_clears_session(client):
    _register(client)
    _login(client)
    resp = client.post("/api/auth/logout")
    assert resp.status_code == 200
    assert client.get("/api/auth/me").status_code == 401


def test_create_project_requires_login(client):
    resp = client.post("/api/projects", json={"name": "Nope"})
    assert resp.status_code == 401


def test_project_owner_is_session_user(client):
    user = _register(client)
    _login(client)
    resp = client.post("/api/projects", json={"name": "Mine"})
    assert resp.status_code == 201
    assert resp.get_json()["data"]["owner_id"] == user["id"]


def test_cannot_modify_someone_elses_project(client):
    _register(client, "alice", "alice@example.com")
    _login(client, "alice")
    project = client.post("/api/projects", json={"name": "Alice's"}).get_json()["data"]
    client.post("/api/auth/logout")

    _register(client, "bob", "bob@example.com", "hunter22")
    _login(client, "bob")
    assert client.patch(f"/api/projects/{project['id']}", json={"name": "Hacked"}).status_code == 403
    assert client.delete(f"/api/projects/{project['id']}").status_code == 403


def test_delete_user_requires_login(client):
    user = _register(client)
    resp = client.delete(f"/api/users/{user['id']}")
    assert resp.status_code == 401


def test_cannot_delete_another_user(client):
    alice = _register(client, "alice", "alice@example.com")
    _register(client, "bob", "bob@example.com", "hunter22")
    _login(client, "bob")
    assert client.delete(f"/api/users/{alice['id']}").status_code == 403
    assert client.patch(f"/api/users/{alice['id']}", json={"username": "pwned"}).status_code == 403


def test_can_delete_own_account(client):
    user = _register(client)
    _login(client)
    assert client.delete(f"/api/users/{user['id']}").status_code == 200
    # session is invalidated after self-deletion
    assert client.get("/api/auth/me").status_code == 401


def test_users_see_only_their_own_projects_and_tasks(client):
    # alice creates a project + task
    _register(client, "alice", "alice@example.com")
    _login(client, "alice")
    project = client.post("/api/projects", json={"name": "Alice's"}).get_json()["data"]
    client.post("/api/tasks", json={"title": "Alice task", "project_id": project["id"]})
    client.post("/api/auth/logout")

    # bob sees none of it
    _register(client, "bob", "bob@example.com", "hunter22")
    _login(client, "bob")
    assert client.get("/api/projects").get_json()["data"] == []
    assert client.get("/api/tasks").get_json()["data"] == []
    assert client.get(f"/api/projects/{project['id']}").status_code == 403


def test_assignee_can_see_assigned_task(client):
    bob = _register(client, "bob", "bob@example.com")
    _register(client, "alice", "alice@example.com")
    _login(client, "alice")
    project = client.post("/api/projects", json={"name": "Alice's"}).get_json()["data"]
    client.post("/api/tasks", json={
        "title": "For Bob", "project_id": project["id"], "assignee_id": bob["id"]
    })
    client.post("/api/auth/logout")

    _login(client, "bob", "hunter22")
    tasks = client.get("/api/tasks").get_json()["data"]
    assert len(tasks) == 1 and tasks[0]["title"] == "For Bob"
    # but bob still can't see alice's project itself
    assert client.get("/api/projects").get_json()["data"] == []
