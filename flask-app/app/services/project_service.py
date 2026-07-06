from app.extensions import db
from app.models.project import Project
from app.models.user import User


class ProjectService:
    def list_projects(self, owner_id):
        """Scoped: a user only ever sees their own projects."""
        return Project.query.filter_by(owner_id=owner_id).order_by(Project.id).all()

    def get_project(self, project_id):
        return Project.query.get(project_id)

    def create_project(self, data, owner_id):
        """owner_id comes from the authenticated session, not client input."""
        project = Project(
            name=data["name"],
            description=data.get("description"),
            owner_id=owner_id,
        )
        db.session.add(project)
        db.session.commit()
        return project

    def update_project(self, project_id, data):
        project = self.get_project(project_id)
        if not project:
            return None
        for field in ("name", "description"):
            if field in data:
                setattr(project, field, data[field])
        db.session.commit()
        return project

    def delete_project(self, project_id):
        project = self.get_project(project_id)
        if not project:
            return False
        db.session.delete(project)
        db.session.commit()
        return True
