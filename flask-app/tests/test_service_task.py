"""Service layer tests."""
import pytest
from app.extensions import db
from app.models.user import User
from app.models.project import Project
from app.services.task_service import TaskService


@pytest.fixture()
def project(app, db):
    user = User(username="carol", email="carol@example.com", password_hash="x")
    db.session.add(user)
    db.session.commit()
    p = Project(name="API Migration", owner_id=user.id)
    db.session.add(p)
    db.session.commit()
    return p


def test_create_task_requires_valid_project(app):
    service = TaskService()
    with pytest.raises(ValueError):
        service.create_task({"title": "Ghost task", "project_id": 9999})


def test_create_and_filter_tasks(app, project):
    service = TaskService()
    service.create_task({"title": "Write tests", "project_id": project.id, "status": "todo"})
    service.create_task({"title": "Fix bug", "project_id": project.id, "status": "done"})

    query = service.build_filtered_query({"status": "done"})
    results = query.all()
    assert len(results) == 1
    assert results[0].title == "Fix bug"


def test_search_by_title(app, project):
    service = TaskService()
    service.create_task({"title": "Refactor auth module", "project_id": project.id})
    service.create_task({"title": "Update docs", "project_id": project.id})

    query = service.build_filtered_query({"search": "auth"})
    results = query.all()
    assert len(results) == 1
    assert "auth" in results[0].title.lower()
