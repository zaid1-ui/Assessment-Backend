"""Service layer tests (async)."""
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.database import Base
from app.models.user import User
from app.models.project import Project
from app.services.task_service import TaskService

pytestmark = pytest.mark.asyncio


@pytest.fixture()
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        yield session
    await engine.dispose()


async def test_create_task_requires_valid_project(db_session):
    from app.schemas.task import TaskCreate
    service = TaskService(db_session)
    payload = TaskCreate(title="Ghost task", project_id=9999)
    with pytest.raises(ValueError):
        await service.create_task(payload)


async def test_create_and_filter_tasks(db_session):
    from app.schemas.task import TaskCreate
    user = User(username="erin", email="erin@example.com", password_hash="x")
    db_session.add(user)
    await db_session.commit()
    project = Project(name="Data Platform", owner_id=user.id)
    db_session.add(project)
    await db_session.commit()

    service = TaskService(db_session)
    await service.create_task(TaskCreate(title="Write tests", project_id=project.id, status="todo"))
    await service.create_task(TaskCreate(title="Fix bug", project_id=project.id, status="done"))

    stmt = service.build_filtered_stmt({"status": "done"}, user_id=project.owner_id)
    result = await db_session.execute(stmt)
    tasks = result.scalars().all()
    assert len(tasks) == 1
    assert tasks[0].title == "Fix bug"
