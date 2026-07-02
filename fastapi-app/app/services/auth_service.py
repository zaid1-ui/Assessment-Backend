"""Authentication service - password hashing, injectable via FastAPI Depends()."""
import hashlib
from app.config import get_settings


class AuthService:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key

    def hash_password(self, raw_password: str) -> str:
        return hashlib.sha256(f"{self.secret_key}{raw_password}".encode()).hexdigest()

    def verify_password(self, raw_password: str, password_hash: str) -> bool:
        return self.hash_password(raw_password) == password_hash


def get_auth_service() -> AuthService:
    """Dependency provider - FastAPI resolves and caches per-request."""
    settings = get_settings()
    return AuthService(secret_key=settings.secret_key)
