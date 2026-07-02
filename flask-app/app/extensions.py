"""Shared extension instances (single source, avoids circular imports)."""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
