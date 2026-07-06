from fastapi import APIRouter, HTTPException
from app.dependencies import CurrentUserId, DbSession
from app.schemas.comment import CommentCreate, CommentOut
from app.schemas.common import ApiResponse
from app.services.comment_service import CommentService
from app.models.task import Task
from app.models.project import Project

router = APIRouter(prefix="/api", tags=["comments"])


async def _get_task_checked(db, task_id: int, user_id: int) -> Task:
    """Comments follow task visibility: project owner or task assignee."""
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    project = await db.get(Project, task.project_id)
    if project.owner_id != user_id and task.assignee_id != user_id:
        raise HTTPException(status_code=403, detail="You do not have access to this task")
    return task


@router.get("/tasks/{task_id}/comments", response_model=ApiResponse[list[CommentOut]])
async def list_comments(task_id: int, db: DbSession, user_id: CurrentUserId):
    await _get_task_checked(db, task_id, user_id)
    comments = await CommentService(db).list_for_task(task_id)
    return ApiResponse(data=[CommentOut.model_validate(c) for c in comments])


@router.post("/comments", response_model=ApiResponse[CommentOut], status_code=201)
async def create_comment(payload: CommentCreate, db: DbSession, user_id: CurrentUserId):
    task = await db.get(Task, payload.task_id)
    if not task:
        raise HTTPException(status_code=400, detail="task_id does not reference an existing task")
    project = await db.get(Project, task.project_id)
    if project.owner_id != user_id and task.assignee_id != user_id:
        raise HTTPException(status_code=403, detail="You do not have access to this task")

    # Author is always the logged-in user, never client input.
    comment = await CommentService(db).create_comment(payload, author_id=user_id)
    return ApiResponse(message="Comment created", data=CommentOut.model_validate(comment))


@router.delete("/comments/{comment_id}", response_model=ApiResponse)
async def delete_comment(comment_id: int, db: DbSession, user_id: CurrentUserId):
    service = CommentService(db)
    comment = await service.get_comment(comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    task = await db.get(Task, comment.task_id)
    project = await db.get(Project, task.project_id)
    # The comment's author or the project owner may delete it.
    if comment.author_id != user_id and project.owner_id != user_id:
        raise HTTPException(status_code=403, detail="You cannot delete this comment")
    await service.delete_comment(comment_id)
    return ApiResponse(message="Comment deleted")
