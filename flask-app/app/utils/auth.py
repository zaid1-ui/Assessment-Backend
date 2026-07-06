"""Session-based authentication helpers.

Uses Flask's built-in session (a signed cookie backed by SECRET_KEY).
The cookie only stores the user id; the signature prevents tampering.
"""
from functools import wraps
from flask import session

from app.utils.responses import error_response

_SESSION_USER_KEY = "user_id"


def current_user_id():
    """Return the id of the logged-in user, or None."""
    return session.get(_SESSION_USER_KEY)


def login_user(user_id: int):
    """Start a fresh session for the given user (clears any old session first)."""
    session.clear()
    session[_SESSION_USER_KEY] = user_id
    session.permanent = True  # honours PERMANENT_SESSION_LIFETIME


def logout_user():
    session.clear()


def login_required(fn):
    """Decorator: reject the request with 401 unless a user is logged in."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if current_user_id() is None:
            return error_response("Authentication required", 401)
        return fn(*args, **kwargs)

    return wrapper
