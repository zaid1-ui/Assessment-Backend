from app.extensions import db
from app.models.comment import Comment
from app.models.task import Task
from app.models.user import User


class CommentService:
    def list_for_task(self, task_id):
        return Comment.query.filter_by(task_id=task_id).order_by(Comment.created_at).all()

    def create_comment(self, data):
        if not Task.query.get(data["task_id"]):
            raise ValueError("task_id does not reference an existing task")
        if not User.query.get(data["author_id"]):
            raise ValueError("author_id does not reference an existing user")
        comment = Comment(
            content=data["content"],
            task_id=data["task_id"],
            author_id=data["author_id"],
        )
        db.session.add(comment)
        db.session.commit()
        return comment

    def delete_comment(self, comment_id):
        comment = Comment.query.get(comment_id)
        if not comment:
            return False
        db.session.delete(comment)
        db.session.commit()
        return True
