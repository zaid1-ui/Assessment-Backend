from flask import Blueprint
from app.models.project import Project
from app.services.report_service import generate_project_report
from app.utils.auth import current_user_id, login_required
from app.utils.responses import success_response, error_response

bp = Blueprint("reports", __name__, url_prefix="/api/reports")


@bp.get("/projects/<int:project_id>")
@login_required
def project_report(project_id):
    """Synchronous, time-consuming report generation endpoint."""
    project = Project.query.get(project_id)
    if not project:
        return error_response("Project not found", 404)
    if project.owner_id != current_user_id():
        return error_response("You do not own this project", 403)
    try:
        report = generate_project_report(project_id)
    except ValueError as e:
        return error_response(str(e), 404)
    return success_response(report, "Report generated")
