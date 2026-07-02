from flask import Blueprint, request
from marshmallow import ValidationError
from app.services.task_service import TaskService
from app.services.audit_service import create_audit_log_entry
from app.schemas.task_schema import TaskCreateSchema, TaskUpdateSchema
from app.utils.responses import success_response, error_response
from app.utils.pagination import paginate_query
from app.utils.background import run_in_background

bp = Blueprint("tasks", __name__, url_prefix="/api/tasks")
service = TaskService()


@bp.get("")
def list_tasks():
    """Meaningful endpoint supporting filtering + searching + pagination together.

    Query params: status, priority, project_id, assignee_id, search, sort, page, page_size
    """
    query = service.build_filtered_query(request.args)
    items, meta = paginate_query(query, request.args)
    return success_response([t.to_dict() for t in items], meta=meta)


@bp.get("/<int:task_id>")
def get_task(task_id):
    task = service.get_task(task_id)
    if not task:
        return error_response("Task not found", 404)
    return success_response(task.to_dict())


@bp.post("")
def create_task():
    try:
        data = TaskCreateSchema().load(request.get_json(force=True) or {})
    except ValidationError as err:
        return error_response("Validation failed", 422, err.messages)
    try:
        task = service.create_task(data)
    except ValueError as e:
        return error_response(str(e), 400)

    # Background task: fire-and-forget audit logging
    run_in_background(create_audit_log_entry, "create", "task", task.id)

    return success_response(task.to_dict(), "Task created", 201)


@bp.put("/<int:task_id>")
@bp.patch("/<int:task_id>")
def update_task(task_id):
    try:
        data = TaskUpdateSchema().load(request.get_json(force=True) or {}, partial=True)
    except ValidationError as err:
        return error_response("Validation failed", 422, err.messages)
    task = service.update_task(task_id, data)
    if not task:
        return error_response("Task not found", 404)

    run_in_background(create_audit_log_entry, "update", "task", task.id)

    return success_response(task.to_dict(), "Task updated")


@bp.delete("/<int:task_id>")
def delete_task(task_id):
    ok = service.delete_task(task_id)
    if not ok:
        return error_response("Task not found", 404)
    run_in_background(create_audit_log_entry, "delete", "task", task_id)
    return success_response(None, "Task deleted", 200)
