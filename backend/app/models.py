"""Aggregate model imports so Alembic can discover all metadata."""

from app.database import Base
from app.place.models import Place

__all__ = ["Base", "Place"]
