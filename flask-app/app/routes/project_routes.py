from flask import Blueprint, request
from marshmallow import ValidationError
from app.services.project_service import ProjectService
from app.schemas.project_schema import ProjectCreateSchema, ProjectUpdateSchema
from app.utils.responses import success_response, error_response

bp = Blueprint("projects", __name__, url_prefix="/api/projects")
service = ProjectService()


@bp.get("")
def list_projects():
    projects = service.list_projects()
    return success_response([p.to_dict() for p in projects])


@bp.get("/<int:project_id>")
def get_project(project_id):
    project = service.get_project(project_id)
    if not project:
        return error_response("Project not found", 404)
    return success_response(project.to_dict())


@bp.post("")
def create_project():
    try:
        data = ProjectCreateSchema().load(request.get_json(force=True) or {})
    except ValidationError as err:
        return error_response("Validation failed", 422, err.messages)
    try:
        project = service.create_project(data)
    except ValueError as e:
        return error_response(str(e), 400)
    return success_response(project.to_dict(), "Project created", 201)


@bp.patch("/<int:project_id>")
def update_project(project_id):
    try:
        data = ProjectUpdateSchema().load(request.get_json(force=True) or {}, partial=True)
    except ValidationError as err:
        return error_response("Validation failed", 422, err.messages)
    project = service.update_project(project_id, data)
    if not project:
        return error_response("Project not found", 404)
    return success_response(project.to_dict(), "Project updated")


@bp.delete("/<int:project_id>")
def delete_project(project_id):
    ok = service.delete_project(project_id)
    if not ok:
        return error_response("Project not found", 404)
    return success_response(None, "Project deleted", 200)
