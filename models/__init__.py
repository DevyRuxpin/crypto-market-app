from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User  # Ensure User is imported from its respective file
from .database import db  # Ensure db is imported from its respective file

__all__ = ["User", "db"]  # Export User and db for external imports

