from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.comment import Comment
from app.models.task import Task
from app.models.user import User


class CommentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_task(self, task_id: int):
        result = await self.db.execute(
            select(Comment).where(Comment.task_id == task_id).order_by(Comment.created_at)
        )
        return result.scalars().all()

    async def create_comment(self, data) -> Comment:
        if not await self.db.get(Task, data.task_id):
            raise ValueError("task_id does not reference an existing task")
        if not await self.db.get(User, data.author_id):
            raise ValueError("author_id does not reference an existing user")
        comment = Comment(**data.model_dump())
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
