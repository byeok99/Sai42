"""Aggregate model imports so Alembic can discover all metadata."""

from app.auth.infrastructure.models import UserProfile
from app.common.infrastructure.models import IdempotencyRecord
from app.database import Base
from app.place.infrastructure.models import Place

__all__ = ["Base", "IdempotencyRecord", "Place", "UserProfile"]
