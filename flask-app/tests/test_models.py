"""Database layer tests."""
from app.extensions import db
from app.models.user import User
from app.models.project import Project
from app.models.task import Task


def test_create_user_and_project(app, db):
    user = User(username="alice", email="alice@example.com", password_hash="x")
    db.session.add(user)
    db.session.commit()

    project = Project(name="Website Revamp", owner_id=user.id)
    db.session.add(project)
    db.session.commit()

    assert project.owner.username == "alice"
    assert user.projects[0].name == "Website Revamp"


def test_task_cascade_delete_with_project(app, db):
    user = User(username="bob", email="bob@example.com", password_hash="x")
    db.session.add(user)
    db.session.commit()
    project = Project(name="Mobile App", owner_id=user.id)
    db.session.add(project)
    db.session.commit()
    task = Task(title="Design UI", project_id=project.id)
    db.session.add(task)
    db.session.commit()

    db.session.delete(project)
    db.session.commit()

    assert Task.query.get(task.id) is None
