from flask import Blueprint, request
from marshmallow import ValidationError
from app.services.comment_service import CommentService
from app.schemas.comment_schema import CommentCreateSchema
from app.utils.responses import success_response, error_response

bp = Blueprint("comments", __name__, url_prefix="/api")
service = CommentService()


@bp.get("/tasks/<int:task_id>/comments")
def list_comments(task_id):
    comments = service.list_for_task(task_id)
    return success_response([c.to_dict() for c in comments])


@bp.post("/comments")
def create_comment():
    try:
        data = CommentCreateSchema().load(request.get_json(force=True) or {})
    except ValidationError as err:
        return error_response("Validation failed", 422, err.messages)
    try:
        comment = service.create_comment(data)
    except ValueError as e:
        return error_response(str(e), 400)
    return success_response(comment.to_dict(), "Comment created", 201)


@bp.delete("/comments/<int:comment_id>")
def delete_comment(comment_id):
    ok = service.delete_comment(comment_id)
    if not ok:
        return error_response("Comment not found", 404)
    return success_response(None, "Comment deleted", 200)
