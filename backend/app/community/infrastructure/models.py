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


class CommunityLike(Base):
    __tablename__ = "community_likes"
    __table_args__ = (
        UniqueConstraint("profile_id", "community_post_id", name="uq_community_likes_profile_post"),
        Index("ix_community_likes_post", "community_post_id"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        Text, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False
    )
    community_post_id: Mapped[str] = mapped_column(
        Text, ForeignKey("community_posts.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
