"""Report generation service - the 'time-consuming operation' requirement.

Implemented synchronously here. The FastAPI project implements the same
logic both synchronously and asynchronously for comparison (see docs).
"""
import time
import logging
from collections import Counter
from app.models.task import Task
from app.models.project import Project

logger = logging.getLogger("flask_app.reports")


def generate_project_report(project_id: int) -> dict:
    """Aggregate task statistics for a project. Simulates a heavy
    computation (e.g. reading & crunching many rows) with a sleep so the
    synchronous blocking behaviour is observable."""
    start = time.time()
    logger.info("Starting report generation for project_id=%s", project_id)

    project = Project.query.get(project_id)
    if not project:
        raise ValueError("Project not found")

    tasks = Task.query.filter_by(project_id=project_id).all()

    # Simulate expensive aggregation work (I/O bound or CPU bound in real life)
    time.sleep(1.5)

    status_counts = Counter(t.status for t in tasks)
    priority_counts = Counter(t.priority for t in tasks)

    report = {
        "project_id": project_id,
        "project_name": project.name,
        "total_tasks": len(tasks),
        "status_breakdown": dict(status_counts),
        "priority_breakdown": dict(priority_counts),
        "generated_in_seconds": round(time.time() - start, 3),
    }
    logger.info("Finished report generation for project_id=%s in %.3fs",
                project_id, report["generated_in_seconds"])
    return report
