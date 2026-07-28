"""
Models Package

Exports all SQLAlchemy ORM models so they register with Base.metadata.
"""

from app.models.job import Job
from app.models.resume import Resume
from app.models.application import Application, ApplicationLog
from app.models.user import User
from app.models.saved_search import SavedSearch
from app.models.notification import Notification
from app.models.job_verification import JobVerification

__all__ = ["Job", "Resume", "Application", "ApplicationLog", "User", "SavedSearch", "Notification", "JobVerification"]
