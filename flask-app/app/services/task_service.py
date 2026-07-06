from sqlalchemy import or_
from app.extensions import db
from app.models.task import Task
from app.models.project import Project


class TaskService:
    def get_task(self, task_id):
        return Task.query.get(task_id)

    def build_filtered_query(self, args, user_id):
        """Filtering + searching used by the list endpoint.

        Scoped to the logged-in user: only tasks in projects they own,
        plus tasks assigned to them.
        """
        query = Task.query.join(Project, Task.project_id == Project.id).filter(
            or_(Project.owner_id == user_id, Task.assignee_id == user_id)
        )

        status = args.get("status")
        if status:
            query = query.filter(Task.status == status)

        priority = args.get("priority")
        if priority:
            query = query.filter(Task.priority == priority)

        project_id = args.get("project_id")
        if project_id:
            query = query.filter(Task.project_id == project_id)

        assignee_id = args.get("assignee_id")
        if assignee_id:
            query = query.filter(Task.assignee_id == assignee_id)

        search = args.get("search")
        if search:
            like = f"%{search}%"
            query = query.filter(Task.title.ilike(like))

        sort = args.get("sort", "-created_at")
        column = sort.lstrip("-")
        direction = "desc" if sort.startswith("-") else "asc"
        if hasattr(Task, column):
            col = getattr(Task, column)
            query = query.order_by(col.desc() if direction == "desc" else col.asc())

        return query

    def create_task(self, data):
        project = Project.query.get(data["project_id"])
        if not project:
            raise ValueError("project_id does not reference an existing project")
        task = Task(
            title=data["title"],
            description=data.get("description"),
            status=data.get("status", "todo"),
            priority=data.get("priority", "medium"),
            project_id=data["project_id"],
            assignee_id=data.get("assignee_id"),
            due_date=data.get("due_date"),
        )
        db.session.add(task)
        db.session.commit()
        return task

    def update_task(self, task_id, data):
        task = self.get_task(task_id)
        if not task:
            return None
        for field in ("title", "description", "status", "priority", "assignee_id", "due_date"):
            if field in data:
                setattr(task, field, data[field])
        db.session.commit()
        return task

    def delete_task(self, task_id):
        task = self.get_task(task_id)
        if not task:
            return False
        db.session.delete(task)
        db.session.commit()
        return True

    def bulk_update_status(self, task_ids, new_status):
        """Demonstrates an explicit DB transaction across multiple rows."""
        try:
            tasks = Task.query.filter(Task.id.in_(task_ids)).all()
            for task in tasks:
                task.status = new_status
            db.session.commit()
            return tasks
        except Exception:
            db.session.rollback()
            raise
