"""Create chat, date-course, course-place, and community-post storage.

Revision ID: 20260715_0004
Revises: 20260715_0003
Create Date: 2026-07-15
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260715_0004"
down_revision: str | Sequence[str] | None = "20260715_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("profile_id", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("conditions_json", sa.Text(), nullable=False),
        sa.Column("messages_json", sa.Text(), nullable=False),
        sa.Column("draft_json", sa.Text()),
        sa.Column("draft_version", sa.Integer(), nullable=False),
        sa.Column("weather_json", sa.Text()),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.Column("confirmed_at", sa.Text()),
        sa.Column("expires_at", sa.Text()),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'CONFIRMED', 'DISCARDED', 'EXPIRED')",
            name="ck_chat_sessions_status",
        ),
        sa.ForeignKeyConstraint(["profile_id"], ["user_profiles.id"], ondelete="CASCADE"),
    )
    op.create_table(
        "date_courses",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("profile_id", sa.Text(), nullable=False),
        sa.Column("chat_session_id", sa.Text()),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("source_course_id", sa.Text()),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("date", sa.Text(), nullable=False),
        sa.Column("start_time", sa.Text(), nullable=False),
        sa.Column("time_slot", sa.Text(), nullable=False),
        sa.Column("main_district", sa.Text(), nullable=False),
        sa.Column("space_type", sa.Text(), nullable=False),
        sa.Column("moods_json", sa.Text(), nullable=False),
        sa.Column("activities_json", sa.Text(), nullable=False),
        sa.Column("schedule_density", sa.Text(), nullable=False),
        sa.Column("transportation", sa.Text()),
        sa.Column("overall_comment", sa.Text(), nullable=False),
        sa.Column("tags_json", sa.Text(), nullable=False),
        sa.Column("weather_json", sa.Text()),
        sa.Column("current_order_no", sa.Integer(), nullable=False),
        sa.Column("completion_comment", sa.Text()),
        sa.Column("started_at", sa.Text()),
        sa.Column("completed_at", sa.Text()),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.CheckConstraint("status IN ('ACTIVE', 'COMPLETED')", name="ck_date_courses_status"),
        sa.CheckConstraint(
            "source_type IN ('AI_CHAT', 'RANKING_COPY', 'HISTORY_RESTART')",
            name="ck_date_courses_source_type",
        ),
        sa.ForeignKeyConstraint(["profile_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["chat_session_id"], ["chat_sessions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_course_id"], ["date_courses.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "uq_one_active_course_per_profile",
        "date_courses",
        ["profile_id"],
        unique=True,
        sqlite_where=sa.text("status = 'ACTIVE'"),
    )
    op.create_index(
        "ix_date_courses_profile_status", "date_courses", ["profile_id", "status"]
    )
    op.create_table(
        "date_course_places",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("date_course_id", sa.Text(), nullable=False),
        sa.Column("content_id", sa.Text()),
        sa.Column("order_no", sa.Integer(), nullable=False),
        sa.Column("scheduled_at", sa.Text(), nullable=False),
        sa.Column("estimated_stay_minutes", sa.Integer(), nullable=False),
        sa.Column("sweet_comment", sa.Text(), nullable=False),
        sa.Column("hearted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("hearted_at", sa.Text()),
        sa.Column("completed_at", sa.Text()),
        sa.Column("title_snapshot", sa.Text(), nullable=False),
        sa.Column("address_snapshot", sa.Text()),
        sa.Column("address_detail_snapshot", sa.Text()),
        sa.Column("longitude_snapshot", sa.Float()),
        sa.Column("latitude_snapshot", sa.Float()),
        sa.Column("content_type_id_snapshot", sa.Integer(), nullable=False),
        sa.Column("district_snapshot", sa.Text()),
        sa.Column("space_type_snapshot", sa.Text(), nullable=False),
        sa.Column("image_url_snapshot", sa.Text()),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.CheckConstraint("hearted IN (0, 1)", name="ck_date_course_places_hearted"),
        sa.ForeignKeyConstraint(["date_course_id"], ["date_courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["content_id"], ["places.content_id"], ondelete="SET NULL"),
        sa.UniqueConstraint("date_course_id", "order_no", name="uq_course_place_order"),
        sa.UniqueConstraint("date_course_id", "content_id", name="uq_course_place_content"),
    )
    op.create_index("ix_date_course_places_course", "date_course_places", ["date_course_id"])
    op.create_index(
        "ix_date_course_places_content_hearted",
        "date_course_places",
        ["content_id", "hearted"],
    )
    op.create_table(
        "community_posts",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("date_course_id", sa.Text(), nullable=False),
        sa.Column("author_profile_id", sa.Text()),
        sa.Column("author_nickname_snapshot", sa.Text(), nullable=False),
        sa.Column("one_line_comment", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("published_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.Column("deleted_at", sa.Text()),
        sa.CheckConstraint(
            "status IN ('PUBLISHED', 'DELETED')", name="ck_community_posts_status"
        ),
        sa.ForeignKeyConstraint(["date_course_id"], ["date_courses.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["author_profile_id"], ["user_profiles.id"], ondelete="SET NULL"
        ),
        sa.UniqueConstraint("date_course_id", name="uq_community_posts_date_course"),
    )
    op.create_index(
        "ix_community_posts_status_published",
        "community_posts",
        ["status", "published_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_community_posts_status_published", table_name="community_posts")
    op.drop_table("community_posts")
    op.drop_index("ix_date_course_places_content_hearted", table_name="date_course_places")
    op.drop_index("ix_date_course_places_course", table_name="date_course_places")
    op.drop_table("date_course_places")
    op.drop_index("ix_date_courses_profile_status", table_name="date_courses")
    op.drop_index("uq_one_active_course_per_profile", table_name="date_courses")
    op.drop_table("date_courses")
    op.drop_table("chat_sessions")
