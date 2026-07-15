"""SQLAlchemy persistence model for anonymous user profiles."""

from sqlalchemy import CheckConstraint, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserProfile(Base):
    """Anonymous couple profile authenticated by a four-digit password."""

    __tablename__ = "user_profiles"
    __table_args__ = (
        CheckConstraint(
            "length(nickname) BETWEEN 2 AND 14",
            name="ck_user_profiles_nickname_length",
        ),
        CheckConstraint(
            "length(password) = 4 AND password GLOB '[0-9][0-9][0-9][0-9]'",
            name="ck_user_profiles_password_format",
        ),
        UniqueConstraint(
            "nickname_normalized",
            name="uq_user_profiles_nickname_normalized",
        ),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    nickname: Mapped[str] = mapped_column(Text, nullable=False)
    nickname_normalized: Mapped[str] = mapped_column(Text, nullable=False)
    password: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)
    deleted_at: Mapped[str | None] = mapped_column(Text)
