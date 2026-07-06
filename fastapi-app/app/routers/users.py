from fastapi import APIRouter, HTTPException
from app.dependencies import CurrentUserId, DbSession, AuthSvc
from app.schemas.user import UserCreate, UserUpdate, UserOut
from app.schemas.common import ApiResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/api/users", tags=["users"])


def get_service(db: DbSession, auth: AuthSvc) -> UserService:
    return UserService(db, auth)


@router.get("", response_model=ApiResponse[list[UserOut]])
async def list_users(db: DbSession, auth: AuthSvc):
    users = await get_service(db, auth).list_users()
    return ApiResponse(data=[UserOut.model_validate(u) for u in users])


@router.get("/{user_id}", response_model=ApiResponse[UserOut])
async def get_user(user_id: int, db: DbSession, auth: AuthSvc):
    user = await get_service(db, auth).get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return ApiResponse(data=UserOut.model_validate(user))


@router.post("", response_model=ApiResponse[UserOut], status_code=201)
async def create_user(payload: UserCreate, db: DbSession, auth: AuthSvc):
    user = await get_service(db, auth).create_user(payload)
    return ApiResponse(message="User created", data=UserOut.model_validate(user))


@router.patch("/{user_id}", response_model=ApiResponse[UserOut])
async def update_user(user_id: int, payload: UserUpdate, db: DbSession, auth: AuthSvc,
                      current_user_id: CurrentUserId):
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="You can only update your own account")
    user = await get_service(db, auth).update_user(user_id, payload)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return ApiResponse(message="User updated", data=UserOut.model_validate(user))


@router.delete("/{user_id}", response_model=ApiResponse)
async def delete_user(user_id: int, db: DbSession, auth: AuthSvc,
                      current_user_id: CurrentUserId):
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="You can only delete your own account")
    ok = await get_service(db, auth).delete_user(user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="User not found")
    return ApiResponse(message="User deleted")
