"""Signed session tokens for cookie-based auth (stdlib only, no extra deps).

Token format:  "<user_id>.<issued_at>.<hmac_sha256_signature>"
The signature is computed over "user_id.issued_at" with the app secret key,
so clients cannot forge or tamper with the token. Equivalent in spirit to
Flask's signed session cookie.
"""
import hashlib
import hmac
import time

SESSION_COOKIE_NAME = "session"
SESSION_MAX_AGE_SECONDS = 7 * 24 * 3600  # 7 days


def _signature(payload: str, secret_key: str) -> str:
    return hmac.new(secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()


def create_session_token(user_id: int, secret_key: str) -> str:
    payload = f"{user_id}.{int(time.time())}"
    return f"{payload}.{_signature(payload, secret_key)}"


def verify_session_token(token: str | None, secret_key: str,
                         max_age: int = SESSION_MAX_AGE_SECONDS) -> int | None:
    """Return the user_id if the token is valid and unexpired, else None."""
    if not token:
        return None
    parts = token.split(".")
    if len(parts) != 3:
        return None
    user_id_str, issued_at_str, signature = parts
    payload = f"{user_id_str}.{issued_at_str}"
    # constant-time comparison prevents timing attacks
    if not hmac.compare_digest(signature, _signature(payload, secret_key)):
        return None
    try:
        user_id = int(user_id_str)
        issued_at = int(issued_at_str)
    except ValueError:
        return None
    if time.time() - issued_at > max_age:
        return None
    return user_id
