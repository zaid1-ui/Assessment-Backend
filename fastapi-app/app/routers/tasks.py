from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from app.dependencies import DbSession
from app.schemas.task import TaskCreate, TaskUpdate, TaskOut
from app.schemas.common import ApiResponse, Meta
from app.services.task_service import TaskService
from app.services.audit_service import create_audit_log_entry
from app.utils.pagination import paginate
from app.config import get_settings

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=ApiResponse[list[TaskOut]])
async def list_tasks(
    db: DbSession,
    status: str | None = None,
    priority: str | None = None,
    project_id: int | None = None,
    assignee_id: int | None = None,
    search: str | None = None,
    sort: str = "-created_at",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1),
):
    """Meaningful endpoint supporting filtering + searching + pagination together."""
    settings = get_settings()
    page_size = min(page_size, settings.page_size_max)

    params = {
        "status": status, "priority": priority, "project_id": project_id,
        "assignee_id": assignee_id, "search": search, "sort": sort,
    }
    stmt = TaskService(db).build_filtered_stmt(params)
    items, meta = await paginate(db, stmt, page, page_size)
    return ApiResponse(data=[TaskOut.model_validate(t) for t in items], meta=Meta(**meta))


@router.get("/{task_id}", response_model=ApiResponse[TaskOut])
async def get_task(task_id: int, db: DbSession):
    task = await TaskService(db).get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return ApiResponse(data=TaskOut.model_validate(task))


@router.post("", response_model=ApiResponse[TaskOut], status_code=201)
async def create_task(payload: TaskCreate, db: DbSession, background_tasks: BackgroundTasks):
    try:
        task = await TaskService(db).create_task(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    background_tasks.add_task(create_audit_log_entry, "create", "task", task.id)
    return ApiResponse(message="Task created", data=TaskOut.model_validate(task))


@router.put("/{task_id}", response_model=ApiResponse[TaskOut])
@router.patch("/{task_id}", response_model=ApiResponse[TaskOut])
async def update_task(task_id: int, payload: TaskUpdate, db: DbSession, background_tasks: BackgroundTasks):
    task = await TaskService(db).update_task(task_id, payload)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    background_tasks.add_task(create_audit_log_entry, "update", "task", task.id)
    return ApiResponse(message="Task updated", data=TaskOut.model_validate(task))


@router.delete("/{task_id}", response_model=ApiResponse)
async def delete_task(task_id: int, db: DbSession, background_tasks: BackgroundTasks):
    ok = await TaskService(db).delete_task(task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Task not found")
    background_tasks.add_task(create_audit_log_entry, "delete", "task", task_id)
    return ApiResponse(message="Task deleted")
