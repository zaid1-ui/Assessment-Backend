"""Central place for FastAPI dependencies (DB session, services, auth) -
demonstrates FastAPI's native Depends() based dependency injection system.
"""
from typing import Annotated
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.auth_service import AuthService, get_auth_service
from app.config import get_settings, Settings

DbSession = Annotated[AsyncSession, Depends(get_db)]
AuthSvc = Annotated[AuthService, Depends(get_auth_service)]
AppSettings = Annotated[Settings, Depends(get_settings)]


async def get_current_user_id(x_user_id: Annotated[str | None, Header()] = None) -> int:
    """Very small illustrative auth dependency: reads an X-User-Id header.

    A real implementation would decode a JWT/session token; this keeps the
    example self-contained while demonstrating a dependency chain used by
    protected-style endpoints (e.g. bulk operations).
    """
    if x_user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-User-Id header")
    try:
        return int(x_user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid X-User-Id header")


CurrentUserId = Annotated[int, Depends(get_current_user_id)]
