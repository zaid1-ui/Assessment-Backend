from flask import Blueprint, request
from marshmallow import ValidationError
from app.services.comment_service import CommentService
from app.services.task_service import TaskService
from app.schemas.comment_schema import CommentCreateSchema
from app.utils.auth import current_user_id, login_required
from app.utils.responses import success_response, error_response

bp = Blueprint("comments", __name__, url_prefix="/api")
service = CommentService()
task_service = TaskService()


def _can_view_task(task, user_id):
    """Comments follow task visibility: project owner or task assignee."""
    return task.project.owner_id == user_id or task.assignee_id == user_id


@bp.get("/tasks/<int:task_id>/comments")
@login_required
def list_comments(task_id):
    task = task_service.get_task(task_id)
    if not task:
        return error_response("Task not found", 404)
    if not _can_view_task(task, current_user_id()):
        return error_response("You do not have access to this task", 403)
    comments = service.list_for_task(task_id)
    return success_response([c.to_dict() for c in comments])


@bp.post("/comments")
@login_required
def create_comment():
    try:
        data = CommentCreateSchema().load(request.get_json(force=True) or {})
    except ValidationError as err:
        return error_response("Validation failed", 422, err.messages)

    task = task_service.get_task(data["task_id"])
    if not task:
        return error_response("task_id does not reference an existing task", 400)
    if not _can_view_task(task, current_user_id()):
        return error_response("You do not have access to this task", 403)

    # Author is always the logged-in user, never client input.
    comment = service.create_comment(data, author_id=current_user_id())
    return success_response(comment.to_dict(), "Comment created", 201)


@bp.delete("/comments/<int:comment_id>")
@login_required
def delete_comment(comment_id):
    comment = service.get_comment(comment_id)
    if not comment:
        return error_response("Comment not found", 404)
    user_id = current_user_id()
    # The comment's author or the project owner may delete it.
    if comment.author_id != user_id and comment.task.project.owner_id != user_id:
        return error_response("You cannot delete this comment", 403)
    service.delete_comment(comment_id)
    return success_response(None, "Comment deleted", 200)
