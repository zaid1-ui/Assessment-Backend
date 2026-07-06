"""Authentication routes - session-based login/logout."""
from flask import Blueprint, request
from marshmallow import Schema, fields, ValidationError

from app.models.user import User
from app.services.auth_service import AuthService
from app.utils.auth import current_user_id, login_required, login_user, logout_user
from app.utils.responses import error_response, success_response

bp = Blueprint("auth", __name__, url_prefix="/api/auth")
auth_service = AuthService()


class LoginSchema(Schema):
    username = fields.String(required=True)
    password = fields.String(required=True)


@bp.post("/login")
def login():
    try:
        data = LoginSchema().load(request.get_json(force=True) or {})
    except ValidationError as err:
        return error_response("Validation failed", 422, err.messages)

    user = User.query.filter_by(username=data["username"]).first()
    # Same error for unknown user and bad password: don't leak which usernames exist.
    if not user or not auth_service.verify_password(data["password"], user.password_hash):
        return error_response("Invalid username or password", 401)

    login_user(user.id)
    return success_response(user.to_dict(), "Logged in")


@bp.post("/logout")
@login_required
def logout():
    logout_user()
    return success_response(None, "Logged out")


@bp.get("/me")
def me():
    user_id = current_user_id()
    if user_id is None:
        return error_response("Not logged in", 401)
    user = User.query.get(user_id)
    if not user:  # user deleted while session still alive
        logout_user()
        return error_response("Not logged in", 401)
    return success_response(user.to_dict())
