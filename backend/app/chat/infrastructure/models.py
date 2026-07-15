"""SQLAlchemy persistence model reserved for future AI chat sessions."""

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ChatSession(Base):
    """Persisted course-draft session; Chat APIs are implemented in a later phase."""

    __tablename__ = "chat_sessions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('ACTIVE', 'CONFIRMED', 'DISCARDED', 'EXPIRED')",
            name="ck_chat_sessions_status",
        ),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        Text, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(Text, nullable=False)
    conditions_json: Mapped[str] = mapped_column(Text, nullable=False)
    messages_json: Mapped[str] = mapped_column(Text, nullable=False)
    draft_json: Mapped[str | None] = mapped_column(Text)
    draft_version: Mapped[int] = mapped_column(Integer, nullable=False)
    weather_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)
    confirmed_at: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[str | None] = mapped_column(Text)
