from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.task import Task
from app.models.project import Project


class TaskService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_task(self, task_id: int):
        return await self.db.get(Task, task_id)

    def build_filtered_stmt(self, params: dict):
        """Filtering + searching, mirrors the Flask implementation."""
        stmt = select(Task)

        if params.get("status"):
            stmt = stmt.where(Task.status == params["status"])
        if params.get("priority"):
            stmt = stmt.where(Task.priority == params["priority"])
        if params.get("project_id"):
            stmt = stmt.where(Task.project_id == params["project_id"])
        if params.get("assignee_id"):
            stmt = stmt.where(Task.assignee_id == params["assignee_id"])
        if params.get("search"):
            stmt = stmt.where(Task.title.ilike(f"%{params['search']}%"))

        sort = params.get("sort", "-created_at")
        column_name = sort.lstrip("-")
        if hasattr(Task, column_name):
            column = getattr(Task, column_name)
            stmt = stmt.order_by(column.desc() if sort.startswith("-") else column.asc())

        return stmt

    async def create_task(self, data) -> Task:
        project = await self.db.get(Project, data.project_id)
        if not project:
            raise ValueError("project_id does not reference an existing project")
        task = Task(**data.model_dump())
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def update_task(self, task_id: int, data):
        task = await self.get_task(task_id)
        if not task:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(task, field, value)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def delete_task(self, task_id: int) -> bool:
        task = await self.get_task(task_id)
        if not task:
            return False
        await self.db.delete(task)
        await self.db.commit()
        return True

    async def bulk_update_status(self, task_ids: list[int], new_status: str):
        """Explicit async transaction across multiple rows."""
        try:
            result = await self.db.execute(select(Task).where(Task.id.in_(task_ids)))
            tasks = result.scalars().all()
            for task in tasks:
                task.status = new_status
            await self.db.commit()
            return tasks
        except Exception:
            await self.db.rollback()
            raise
