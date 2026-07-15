"""SQLAlchemy models for current and completed date courses."""

from sqlalchemy import (
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.chat.infrastructure.models import ChatSession as ChatSession
from app.database import Base


class DateCourse(Base):
    __tablename__ = "date_courses"
    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE', 'COMPLETED')", name="ck_date_courses_status"),
        CheckConstraint(
            "source_type IN ('AI_CHAT', 'RANKING_COPY', 'HISTORY_RESTART')",
            name="ck_date_courses_source_type",
        ),
        Index(
            "uq_one_active_course_per_profile",
            "profile_id",
            unique=True,
            sqlite_where=text("status = 'ACTIVE'"),
        ),
        Index("ix_date_courses_profile_status", "profile_id", "status"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        Text, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False
    )
    chat_session_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("chat_sessions.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    source_course_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("date_courses.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    date: Mapped[str] = mapped_column(Text, nullable=False)
    start_time: Mapped[str] = mapped_column(Text, nullable=False)
    time_slot: Mapped[str] = mapped_column(Text, nullable=False)
    main_district: Mapped[str] = mapped_column(Text, nullable=False)
    space_type: Mapped[str] = mapped_column(Text, nullable=False)
    moods_json: Mapped[str] = mapped_column(Text, nullable=False)
    activities_json: Mapped[str] = mapped_column(Text, nullable=False)
    schedule_density: Mapped[str] = mapped_column(Text, nullable=False)
    transportation: Mapped[str | None] = mapped_column(Text)
    overall_comment: Mapped[str] = mapped_column(Text, nullable=False)
    tags_json: Mapped[str] = mapped_column(Text, nullable=False)
    weather_json: Mapped[str | None] = mapped_column(Text)
    current_order_no: Mapped[int] = mapped_column(Integer, nullable=False)
    completion_comment: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[str | None] = mapped_column(Text)
    completed_at: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)


class DateCoursePlace(Base):
    __tablename__ = "date_course_places"
    __table_args__ = (
        UniqueConstraint("date_course_id", "order_no", name="uq_course_place_order"),
        UniqueConstraint("date_course_id", "content_id", name="uq_course_place_content"),
        CheckConstraint("hearted IN (0, 1)", name="ck_date_course_places_hearted"),
        Index("ix_date_course_places_course", "date_course_id"),
        Index("ix_date_course_places_content_hearted", "content_id", "hearted"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    date_course_id: Mapped[str] = mapped_column(
        Text, ForeignKey("date_courses.id", ondelete="CASCADE"), nullable=False
    )
    content_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("places.content_id", ondelete="SET NULL")
    )
    order_no: Mapped[int] = mapped_column(Integer, nullable=False)
    scheduled_at: Mapped[str] = mapped_column(Text, nullable=False)
    estimated_stay_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    sweet_comment: Mapped[str] = mapped_column(Text, nullable=False)
    hearted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    hearted_at: Mapped[str | None] = mapped_column(Text)
    completed_at: Mapped[str | None] = mapped_column(Text)
    title_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    address_snapshot: Mapped[str | None] = mapped_column(Text)
    address_detail_snapshot: Mapped[str | None] = mapped_column(Text)
    longitude_snapshot: Mapped[float | None] = mapped_column(Float)
    latitude_snapshot: Mapped[float | None] = mapped_column(Float)
    content_type_id_snapshot: Mapped[int] = mapped_column(Integer, nullable=False)
    district_snapshot: Mapped[str | None] = mapped_column(Text)
    space_type_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    image_url_snapshot: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
