"""Authentication service - password hashing with bcrypt.

bcrypt is deliberately slow (tunable work factor) and generates a unique
random salt per password, stored inside the hash itself. This makes stolen
hashes impractical to brute-force, unlike fast general-purpose hashes
such as SHA-256.
"""
import bcrypt


class AuthService:
    """A small service class injected into other services (dependency management example)."""

    @staticmethod
    def hash_password(raw_password: str) -> str:
        # gensalt() embeds a fresh random salt + cost factor in every hash
        return bcrypt.hashpw(raw_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def verify_password(raw_password: str, password_hash: str) -> bool:
        try:
            return bcrypt.checkpw(raw_password.encode("utf-8"), password_hash.encode("utf-8"))
        except ValueError:
            # stored hash isn't a valid bcrypt hash (e.g. legacy SHA-256 row)
            return False
