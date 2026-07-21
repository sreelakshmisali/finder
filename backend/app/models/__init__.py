"""
Models Package

Exports all SQLAlchemy ORM models so they register with Base.metadata.
"""

from app.models.job import Job
from app.models.resume import Resume
from app.models.preference import Preference
from app.models.application import Application, ApplicationLog
from app.models.user import User

__all__ = ["Job", "Resume", "Preference", "Application", "ApplicationLog", "User"]
