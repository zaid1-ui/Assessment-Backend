"""Authentication endpoints - session-cookie based login/logout."""
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from app.dependencies import AppSettings, AuthSvc, CurrentUserId, DbSession
from app.schemas.common import ApiResponse
from app.schemas.user import UserOut
from app.services.user_service import UserService
from app.utils.session_cookie import (
    SESSION_COOKIE_NAME,
    SESSION_MAX_AGE_SECONDS,
    create_session_token,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginPayload(BaseModel):
    username: str
    password: str


@router.post("/login", response_model=ApiResponse[UserOut])
async def login(payload: LoginPayload, response: Response,
                db: DbSession, auth: AuthSvc, settings: AppSettings):
    user = await UserService(db, auth).get_user_by_username(payload.username)
    # Same error for unknown user and bad password: don't leak which usernames exist.
    if not user or not auth.verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_session_token(user.id, settings.secret_key)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_MAX_AGE_SECONDS,
        httponly=True,               # not readable from JavaScript
        samesite="lax",              # basic CSRF mitigation
        secure=settings.is_production,  # HTTPS-only in production
    )
    return ApiResponse(message="Logged in", data=UserOut.model_validate(user))


@router.post("/logout", response_model=ApiResponse)
async def logout(response: Response, _user_id: CurrentUserId):
    response.delete_cookie(SESSION_COOKIE_NAME)
    return ApiResponse(message="Logged out")


@router.get("/me", response_model=ApiResponse[UserOut])
async def me(user_id: CurrentUserId, db: DbSession, auth: AuthSvc):
    user = await UserService(db, auth).get_user(user_id)
    if not user:  # user deleted while session still alive
        raise HTTPException(status_code=401, detail="Not logged in")
    return ApiResponse(data=UserOut.model_validate(user))
