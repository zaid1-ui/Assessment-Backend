from app.extensions import db
from app.models.project import Project
from app.models.user import User


class ProjectService:
    def list_projects(self):
        return Project.query.order_by(Project.id).all()

    def get_project(self, project_id):
        return Project.query.get(project_id)

    def create_project(self, data):
        owner = User.query.get(data["owner_id"])
        if not owner:
            raise ValueError("owner_id does not reference an existing user")
        project = Project(
            name=data["name"],
            description=data.get("description"),
            owner_id=data["owner_id"],
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
