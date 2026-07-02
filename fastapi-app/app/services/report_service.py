"""Report generation implemented BOTH synchronously and asynchronously,
so the two execution models can be compared directly (requirement 6 & 7).
"""
import time
import asyncio
import logging
from collections import Counter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.task import Task
from app.models.project import Project

logger = logging.getLogger("fastapi_app.reports")


def _aggregate(tasks, project, start: float) -> dict:
    status_counts = Counter(t.status for t in tasks)
    priority_counts = Counter(t.priority for t in tasks)
    return {
        "project_id": project.id,
        "project_name": project.name,
        "total_tasks": len(tasks),
        "status_breakdown": dict(status_counts),
        "priority_breakdown": dict(priority_counts),
        "generated_in_seconds": round(time.time() - start, 3),
    }


async def generate_project_report_async(db: AsyncSession, project_id: int) -> dict:
    """Async implementation: uses asyncio.sleep so the event loop is free to
    handle other requests concurrently while this 'expensive' operation runs.
    """
    start = time.time()
    logger.info("Starting ASYNC report generation for project_id=%s", project_id)

    project = await db.get(Project, project_id)
    if not project:
        raise ValueError("Project not found")

    result = await db.execute(select(Task).where(Task.project_id == project_id))
    tasks = result.scalars().all()

    await asyncio.sleep(1.5)  # simulate expensive I/O-bound aggregation, non-blocking

    report = _aggregate(tasks, project, start)
    logger.info("Finished ASYNC report generation for project_id=%s in %.3fs",
                project_id, report["generated_in_seconds"])
    return report


def generate_project_report_sync_blocking(project, tasks: list) -> dict:
    """Synchronous aggregation used by the sync endpoint. time.sleep here
    blocks the worker thread handling the request (FastAPI runs sync def
    endpoints in a thread pool, so it does not block the whole event loop,
    but it does block that request/thread for its duration).
    """
    start = time.time()
    logger.info("Starting SYNC report generation for project_id=%s", project.id)
    time.sleep(1.5)
    report = _aggregate(tasks, project, start)
    logger.info("Finished SYNC report generation for project_id=%s in %.3fs",
                project.id, report["generated_in_seconds"])
    return report
