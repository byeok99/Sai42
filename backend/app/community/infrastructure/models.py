"""SQLAlchemy persistence model for automatically published course posts."""

from sqlalchemy import CheckConstraint, ForeignKey, Index, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CommunityPost(Base):
    __tablename__ = "community_posts"
    __table_args__ = (
        UniqueConstraint("date_course_id", name="uq_community_posts_date_course"),
        CheckConstraint("status IN ('PUBLISHED', 'DELETED')", name="ck_community_posts_status"),
        Index("ix_community_posts_status_published", "status", "published_at"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    date_course_id: Mapped[str] = mapped_column(
        Text, ForeignKey("date_courses.id", ondelete="RESTRICT"), nullable=False
    )
    author_profile_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("user_profiles.id", ondelete="SET NULL")
    )
    author_nickname_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    one_line_comment: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)
    deleted_at: Mapped[str | None] = mapped_column(Text)
