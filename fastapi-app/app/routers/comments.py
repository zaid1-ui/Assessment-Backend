from fastapi import APIRouter, HTTPException
from app.dependencies import DbSession
from app.schemas.comment import CommentCreate, CommentOut
from app.schemas.common import ApiResponse
from app.services.comment_service import CommentService

router = APIRouter(prefix="/api", tags=["comments"])


@router.get("/tasks/{task_id}/comments", response_model=ApiResponse[list[CommentOut]])
async def list_comments(task_id: int, db: DbSession):
    comments = await CommentService(db).list_for_task(task_id)
    return ApiResponse(data=[CommentOut.model_validate(c) for c in comments])


@router.post("/comments", response_model=ApiResponse[CommentOut], status_code=201)
async def create_comment(payload: CommentCreate, db: DbSession):
    try:
        comment = await CommentService(db).create_comment(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ApiResponse(message="Comment created", data=CommentOut.model_validate(comment))


@router.delete("/comments/{comment_id}", response_model=ApiResponse)
async def delete_comment(comment_id: int, db: DbSession):
    ok = await CommentService(db).delete_comment(comment_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Comment not found")
    return ApiResponse(message="Comment deleted")
