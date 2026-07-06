"""Central place for FastAPI dependencies (DB session, services, auth) -
demonstrates FastAPI's native Depends() based dependency injection system.
"""
from typing import Annotated
from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.auth_service import AuthService, get_auth_service
from app.config import get_settings, Settings
from app.utils.session_cookie import SESSION_COOKIE_NAME, verify_session_token

DbSession = Annotated[AsyncSession, Depends(get_db)]
AuthSvc = Annotated[AuthService, Depends(get_auth_service)]
AppSettings = Annotated[Settings, Depends(get_settings)]


async def get_current_user_id(
    session: Annotated[str | None, Cookie(alias=SESSION_COOKIE_NAME)] = None,
) -> int:
    """Session-based auth dependency.

    Reads the signed session cookie (set by POST /api/auth/login), verifies
    its HMAC signature and expiry, and returns the authenticated user's id.
    Endpoints that depend on this automatically respond 401 when the caller
    is not logged in.
    """
    user_id = verify_session_token(session, get_settings().secret_key)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required (log in via /api/auth/login)",
        )
    return user_id


CurrentUserId = Annotated[int, Depends(get_current_user_id)]
