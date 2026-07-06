from flask import Blueprint, request
from marshmallow import ValidationError
from app.services.task_service import TaskService
from app.services.audit_service import create_audit_log_entry
from app.schemas.task_schema import TaskCreateSchema, TaskUpdateSchema
from app.models.project import Project
from app.utils.auth import current_user_id, login_required
from app.utils.responses import success_response, error_response
from app.utils.pagination import paginate_query
from app.utils.background import run_in_background

bp = Blueprint("tasks", __name__, url_prefix="/api/tasks")
service = TaskService()


def _can_view(task, user_id):
    """A task is visible to the project owner and to its assignee."""
    return task.project.owner_id == user_id or task.assignee_id == user_id


@bp.get("")
@login_required
def list_tasks():
    """Filtering + searching + pagination, scoped to the logged-in user.

    Query params: status, priority, project_id, assignee_id, search, sort, page, page_size
    """
    query = service.build_filtered_query(request.args, user_id=current_user_id())
    items, meta = paginate_query(query, request.args)
    return success_response([t.to_dict() for t in items], meta=meta)


@bp.get("/<int:task_id>")
@login_required
def get_task(task_id):
    task = service.get_task(task_id)
    if not task:
        return error_response("Task not found", 404)
    if not _can_view(task, current_user_id()):
        return error_response("You do not have access to this task", 403)
    return success_response(task.to_dict())


@bp.post("")
@login_required
def create_task():
    try:
        data = TaskCreateSchema().load(request.get_json(force=True) or {})
    except ValidationError as err:
        return error_response("Validation failed", 422, err.messages)

    project = Project.query.get(data["project_id"])
    if not project:
        return error_response("project_id does not reference an existing project", 400)
    if project.owner_id != current_user_id():
        return error_response("You can only create tasks in your own projects", 403)

    task = service.create_task(data)

    # Background task: fire-and-forget audit logging
    run_in_background(create_audit_log_entry, "create", "task", task.id)

    return success_response(task.to_dict(), "Task created", 201)


@bp.put("/<int:task_id>")
@bp.patch("/<int:task_id>")
@login_required
def update_task(task_id):
    task = service.get_task(task_id)
    if not task:
        return error_response("Task not found", 404)
    # Owner or assignee may update (assignee needs to move status, etc.)
    if not _can_view(task, current_user_id()):
        return error_response("You do not have access to this task", 403)
    try:
        data = TaskUpdateSchema().load(request.get_json(force=True) or {}, partial=True)
    except ValidationError as err:
        return error_response("Validation failed", 422, err.messages)
    task = service.update_task(task_id, data)

    run_in_background(create_audit_log_entry, "update", "task", task.id)

    return success_response(task.to_dict(), "Task updated")


@bp.delete("/<int:task_id>")
@login_required
def delete_task(task_id):
    task = service.get_task(task_id)
    if not task:
        return error_response("Task not found", 404)
    # Only the project owner may delete tasks
    if task.project.owner_id != current_user_id():
        return error_response("Only the project owner can delete tasks", 403)
    service.delete_task(task_id)
    run_in_background(create_audit_log_entry, "delete", "task", task_id)
    return success_response(None, "Task deleted", 200)
