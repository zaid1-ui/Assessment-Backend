from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from app.dependencies import CurrentUserId, DbSession
from app.schemas.task import TaskCreate, TaskUpdate, TaskOut
from app.schemas.common import ApiResponse, Meta
from app.services.task_service import TaskService
from app.services.audit_service import create_audit_log_entry
from app.models.project import Project
from app.utils.pagination import paginate
from app.config import get_settings

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


async def _get_task_checked(db, task_id: int, user_id: int):
    """Load a task and enforce visibility: project owner or assignee."""
    task = await TaskService(db).get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    project = await db.get(Project, task.project_id)
    if project.owner_id != user_id and task.assignee_id != user_id:
        raise HTTPException(status_code=403, detail="You do not have access to this task")
    return task, project


@router.get("", response_model=ApiResponse[list[TaskOut]])
async def list_tasks(
    db: DbSession,
    user_id: CurrentUserId,
    status: str | None = None,
    priority: str | None = None,
    project_id: int | None = None,
    assignee_id: int | None = None,
    search: str | None = None,
    sort: str = "-created_at",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1),
):
    """Filtering + searching + pagination, scoped to the logged-in user."""
    settings = get_settings()
    page_size = min(page_size, settings.page_size_max)

    params = {
        "status": status, "priority": priority, "project_id": project_id,
        "assignee_id": assignee_id, "search": search, "sort": sort,
    }
    stmt = TaskService(db).build_filtered_stmt(params, user_id=user_id)
    items, meta = await paginate(db, stmt, page, page_size)
    return ApiResponse(data=[TaskOut.model_validate(t) for t in items], meta=Meta(**meta))


@router.get("/{task_id}", response_model=ApiResponse[TaskOut])
async def get_task(task_id: int, db: DbSession, user_id: CurrentUserId):
    task, _ = await _get_task_checked(db, task_id, user_id)
    return ApiResponse(data=TaskOut.model_validate(task))


@router.post("", response_model=ApiResponse[TaskOut], status_code=201)
async def create_task(payload: TaskCreate, db: DbSession, user_id: CurrentUserId,
                      background_tasks: BackgroundTasks):
    project = await db.get(Project, payload.project_id)
    if not project:
        raise HTTPException(status_code=400, detail="project_id does not reference an existing project")
    if project.owner_id != user_id:
        raise HTTPException(status_code=403, detail="You can only create tasks in your own projects")

    task = await TaskService(db).create_task(payload)

    background_tasks.add_task(create_audit_log_entry, "create", "task", task.id)
    return ApiResponse(message="Task created", data=TaskOut.model_validate(task))


@router.put("/{task_id}", response_model=ApiResponse[TaskOut])
@router.patch("/{task_id}", response_model=ApiResponse[TaskOut])
async def update_task(task_id: int, payload: TaskUpdate, db: DbSession,
                      user_id: CurrentUserId, background_tasks: BackgroundTasks):
    # Owner or assignee may update (assignee needs to move status, etc.)
    await _get_task_checked(db, task_id, user_id)
    task = await TaskService(db).update_task(task_id, payload)

    background_tasks.add_task(create_audit_log_entry, "update", "task", task.id)
    return ApiResponse(message="Task updated", data=TaskOut.model_validate(task))


@router.delete("/{task_id}", response_model=ApiResponse)
async def delete_task(task_id: int, db: DbSession, user_id: CurrentUserId,
                      background_tasks: BackgroundTasks):
    task = await TaskService(db).get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    project = await db.get(Project, task.project_id)
    # Only the project owner may delete tasks
    if project.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Only the project owner can delete tasks")
    await TaskService(db).delete_task(task_id)
    background_tasks.add_task(create_audit_log_entry, "delete", "task", task_id)
    return ApiResponse(message="Task deleted")
