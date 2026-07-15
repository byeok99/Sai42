"""Aggregate model imports so Alembic can discover all metadata."""

from app.auth.infrastructure.models import UserProfile
from app.chat.infrastructure.models import ChatSession
from app.common.infrastructure.models import IdempotencyRecord
from app.community.infrastructure.models import CommunityPost
from app.course.infrastructure.models import DateCourse, DateCoursePlace
from app.database import Base
from app.place.infrastructure.models import Place

__all__ = [
    "Base",
    "ChatSession",
    "CommunityPost",
    "DateCourse",
    "DateCoursePlace",
    "IdempotencyRecord",
    "Place",
    "UserProfile",
]
