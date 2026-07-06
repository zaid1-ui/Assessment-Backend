"""Authentication service - password hashing with bcrypt, injectable via FastAPI Depends().

bcrypt is deliberately slow (tunable work factor) and generates a unique
random salt per password, stored inside the hash itself. This makes stolen
hashes impractical to brute-force, unlike fast general-purpose hashes
such as SHA-256.
"""
import bcrypt
from app.config import get_settings


class AuthService:
    def __init__(self, secret_key: str):
        # Kept for DI compatibility; bcrypt does not need an app-level secret
        # (the secret key is still used elsewhere for signing session cookies).
        self.secret_key = secret_key

    def hash_password(self, raw_password: str) -> str:
        # gensalt() embeds a fresh random salt + cost factor in every hash
        return bcrypt.hashpw(raw_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify_password(self, raw_password: str, password_hash: str) -> bool:
        try:
            return bcrypt.checkpw(raw_password.encode("utf-8"), password_hash.encode("utf-8"))
        except ValueError:
            # stored hash isn't a valid bcrypt hash (e.g. legacy SHA-256 row)
            return False


def get_auth_service() -> AuthService:
    """Dependency provider - FastAPI resolves and caches per-request."""
    settings = get_settings()
    return AuthService(secret_key=settings.secret_key)
