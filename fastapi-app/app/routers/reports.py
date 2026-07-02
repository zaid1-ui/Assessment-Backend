"""Report endpoints: one synchronous (blocking `def`) and one asynchronous
(`async def`) implementation of the SAME feature, per requirement 6 & 7."""
from functools import lru_cache
from sqlalchemy import select, create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import APIRouter, HTTPException
from app.dependencies import DbSession
from app.schemas.common import ApiResponse
from app.models.project import Project
from app.models.task import Task
from app.config import get_settings
from app.services.report_service import generate_project_report_async, generate_project_report_sync_blocking

router = APIRouter(prefix="/api/reports", tags=["reports"])


@lru_cache
def _sync_session_factory():
    """A separate *synchronous* engine/session, used only by the sync demo
    endpoint below (plain `def`, no async/await) so the sync vs async
    implementations of the same feature can be compared fairly."""
    settings = get_settings()
    sync_url = settings.database_url.replace("+aiosqlite", "").replace(":memory:", "file::memory:?cache=shared&uri=true")
    engine = create_engine(sync_url, connect_args={"check_same_thread": False})
    return sessionmaker(bind=engine)


@router.get("/sync/projects/{project_id}", response_model=ApiResponse)
def project_report_sync(project_id: int):
    """Synchronous endpoint (plain `def`). FastAPI runs this in an external
    threadpool, so it doesn't block the event loop, but the call itself
    blocks that worker thread for its full duration - unlike the async
    version below."""
    Session = _sync_session_factory()
    with Session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        tasks = session.execute(select(Task).where(Task.project_id == project_id)).scalars().all()
        report = generate_project_report_sync_blocking(project, tasks)
    return ApiResponse(message="Report generated (sync)", data=report)


@router.get("/async/projects/{project_id}", response_model=ApiResponse)
async def project_report_async(project_id: int, db: DbSession):
    """Asynchronous endpoint (`async def`) - non-blocking I/O throughout."""
    try:
        report = await generate_project_report_async(db, project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return ApiResponse(message="Report generated (async)", data=report)
