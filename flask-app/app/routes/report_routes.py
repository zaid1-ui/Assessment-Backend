from flask import Blueprint
from app.services.report_service import generate_project_report
from app.utils.responses import success_response, error_response

bp = Blueprint("reports", __name__, url_prefix="/api/reports")


@bp.get("/projects/<int:project_id>")
def project_report(project_id):
    """Synchronous, time-consuming report generation endpoint."""
    try:
        report = generate_project_report(project_id)
    except ValueError as e:
        return error_response(str(e), 404)
    return success_response(report, "Report generated")
