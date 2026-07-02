from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.project import Project
from app.models.user import User


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_projects(self):
        result = await self.db.execute(select(Project).order_by(Project.id))
        return result.scalars().all()

    async def get_project(self, project_id: int):
        return await self.db.get(Project, project_id)

    async def create_project(self, data) -> Project:
        owner = await self.db.get(User, data.owner_id)
        if not owner:
            raise ValueError("owner_id does not reference an existing user")
        project = Project(name=data.name, description=data.description, owner_id=data.owner_id)
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def update_project(self, project_id: int, data):
        project = await self.get_project(project_id)
        if not project:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(project, field, value)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def delete_project(self, project_id: int) -> bool:
        project = await self.get_project(project_id)
        if not project:
            return False
        await self.db.delete(project)
        await self.db.commit()
        return True
