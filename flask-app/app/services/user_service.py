from app.extensions import db
from app.models.user import User
from app.services.auth_service import AuthService


class UserService:
    def __init__(self, auth_service: AuthService = None):
        # Dependency injection: auth service can be swapped/mocked in tests
        self.auth_service = auth_service or AuthService()

    def list_users(self):
        return User.query.order_by(User.id).all()

    def get_user(self, user_id):
        return User.query.get(user_id)

    def create_user(self, data):
        user = User(
            username=data["username"],
            email=data["email"],
            password_hash=self.auth_service.hash_password(data["password"]),
        )
        db.session.add(user)
        db.session.commit()
        return user

    def update_user(self, user_id, data):
        user = self.get_user(user_id)
        if not user:
            return None
        for field in ("username", "email"):
            if field in data:
                setattr(user, field, data[field])
        db.session.commit()
        return user

    def delete_user(self, user_id):
        user = self.get_user(user_id)
        if not user:
            return False
        db.session.delete(user)
        db.session.commit()
        return True
