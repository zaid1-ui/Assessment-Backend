from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.comment import Comment
from app.models.task import Task
from app.models.user import User


class CommentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_comment(self, comment_id: int):
        return await self.db.get(Comment, comment_id)

    async def list_for_task(self, task_id: int):
        result = await self.db.execute(
            select(Comment).where(Comment.task_id == task_id).order_by(Comment.created_at)
        )
        return result.scalars().all()

    async def create_comment(self, data, author_id: int) -> Comment:
        """author_id comes from the authenticated session, not client input."""
        comment = Comment(**data.model_dump(), author_id=author_id)
        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment)
        return comment

    async def delete_comment(self, comment_id: int) -> bool:
        comment = await self.db.get(Comment, comment_id)
        if not comment:
            return False
        await self.db.delete(comment)
        await self.db.commit()
        return True
