from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.services.auth_service import AuthService


class UserService:
    def __init__(self, db: AsyncSession, auth_service: AuthService):
        self.db = db
        self.auth_service = auth_service

    async def list_users(self):
        result = await self.db.execute(select(User).order_by(User.id))
        return result.scalars().all()

    async def get_user(self, user_id: int):
        return await self.db.get(User, user_id)

    async def create_user(self, data) -> User:
        user = User(
            username=data.username,
            email=data.email,
            password_hash=self.auth_service.hash_password(data.password),
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_user(self, user_id: int, data):
        user = await self.get_user(user_id)
        if not user:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete_user(self, user_id: int) -> bool:
        user = await self.get_user(user_id)
        if not user:
            return False
        await self.db.delete(user)
        await self.db.commit()
        return True
