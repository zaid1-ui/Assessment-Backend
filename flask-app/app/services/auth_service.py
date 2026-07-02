"""Authentication service - password hashing (demonstrates a shared/injectable service)."""
import hashlib
import os


class AuthService:
    """A small service class injected into other services (dependency management example)."""

    @staticmethod
    def hash_password(raw_password: str) -> str:
        salt = os.environ.get("PASSWORD_SALT", "static-dev-salt")
        return hashlib.sha256(f"{salt}{raw_password}".encode()).hexdigest()

    @staticmethod
    def verify_password(raw_password: str, password_hash: str) -> bool:
        return AuthService.hash_password(raw_password) == password_hash
