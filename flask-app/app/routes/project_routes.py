from flask import Blueprint, request
from marshmallow import ValidationError
from app.services.project_service import ProjectService
from app.schemas.project_schema import ProjectCreateSchema, ProjectUpdateSchema
from app.utils.auth import current_user_id, login_required
from app.utils.responses import success_response, error_response

bp = Blueprint("projects", __name__, url_prefix="/api/projects")
service = ProjectService()


@bp.get("")
@login_required
def list_projects():
    """Only the logged-in user's own projects."""
    projects = service.list_projects(owner_id=current_user_id())
    return success_response([p.to_dict() for p in projects])


@bp.get("/<int:project_id>")
@login_required
def get_project(project_id):
    project = service.get_project(project_id)
    if not project:
        return error_response("Project not found", 404)
    if project.owner_id != current_user_id():
        return error_response("You do not own this project", 403)
    return success_response(project.to_dict())


@bp.post("")
@login_required
def create_project():
    try:
        data = ProjectCreateSchema().load(request.get_json(force=True) or {})
    except ValidationError as err:
        return error_response("Validation failed", 422, err.messages)
    # Owner comes from the session, never from the request body.
    project = service.create_project(data, owner_id=current_user_id())
    return success_response(project.to_dict(), "Project created", 201)


@bp.patch("/<int:project_id>")
@login_required
def update_project(project_id):
    project = service.get_project(project_id)
    if not project:
        return error_response("Project not found", 404)
    if project.owner_id != current_user_id():
        return error_response("You do not own this project", 403)
    try:
        data = ProjectUpdateSchema().load(request.get_json(force=True) or {}, partial=True)
    except ValidationError as err:
        return error_response("Validation failed", 422, err.messages)
    project = service.update_project(project_id, data)
    return success_response(project.to_dict(), "Project updated")


@bp.delete("/<int:project_id>")
@login_required
def delete_project(project_id):
    project = service.get_project(project_id)
    if not project:
        return error_response("Project not found", 404)
    if project.owner_id != current_user_id():
        return error_response("You do not own this project", 403)
    service.delete_project(project_id)
    return success_response(None, "Project deleted", 200)
