"""Create community post likes.

Revision ID: 20260715_0005
Revises: 20260715_0004
Create Date: 2026-07-15
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260715_0005"
down_revision: str | Sequence[str] | None = "20260715_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "community_likes",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("profile_id", sa.Text(), nullable=False),
        sa.Column("community_post_id", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["community_post_id"], ["community_posts.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint(
            "profile_id", "community_post_id", name="uq_community_likes_profile_post"
        ),
    )
    op.create_index("ix_community_likes_post", "community_likes", ["community_post_id"])


def downgrade() -> None:
    op.drop_index("ix_community_likes_post", table_name="community_likes")
    op.drop_table("community_likes")
