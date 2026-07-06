from flask import Blueprint, request
from marshmallow import ValidationError
from app.services.user_service import UserService
from app.schemas.user_schema import UserCreateSchema, UserUpdateSchema
from app.utils.auth import current_user_id, login_required, logout_user
from app.utils.responses import success_response, error_response

bp = Blueprint("users", __name__, url_prefix="/api/users")
service = UserService()


@bp.get("")
def list_users():
    users = service.list_users()
    return success_response([u.to_dict() for u in users])


@bp.get("/<int:user_id>")
def get_user(user_id):
    user = service.get_user(user_id)
    if not user:
        return error_response("User not found", 404)
    return success_response(user.to_dict())


@bp.post("")
def create_user():
    try:
        data = UserCreateSchema().load(request.get_json(force=True) or {})
    except ValidationError as err:
        return error_response("Validation failed", 422, err.messages)
    user = service.create_user(data)
    return success_response(user.to_dict(), "User created", 201)


@bp.patch("/<int:user_id>")
@login_required
def update_user(user_id):
    if user_id != current_user_id():
        return error_response("You can only update your own account", 403)
    try:
        data = UserUpdateSchema().load(request.get_json(force=True) or {}, partial=True)
    except ValidationError as err:
        return error_response("Validation failed", 422, err.messages)
    user = service.update_user(user_id, data)
    if not user:
        return error_response("User not found", 404)
    return success_response(user.to_dict(), "User updated")


@bp.delete("/<int:user_id>")
@login_required
def delete_user(user_id):
    if user_id != current_user_id():
        return error_response("You can only delete your own account", 403)
    ok = service.delete_user(user_id)
    if not ok:
        return error_response("User not found", 404)
    logout_user()  # the account behind this session no longer exists
    return success_response(None, "User deleted", 200)
