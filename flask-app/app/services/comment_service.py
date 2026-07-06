from app.extensions import db
from app.models.comment import Comment
from app.models.task import Task
from app.models.user import User


class CommentService:
    def get_comment(self, comment_id):
        return Comment.query.get(comment_id)

    def list_for_task(self, task_id):
        return Comment.query.filter_by(task_id=task_id).order_by(Comment.created_at).all()

    def create_comment(self, data, author_id):
        """author_id comes from the authenticated session, not client input."""
        comment = Comment(
            content=data["content"],
            task_id=data["task_id"],
            author_id=author_id,
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
