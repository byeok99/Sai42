"""Create anonymous user profiles.

Revision ID: 20260715_0003
Revises: 20260715_0002
Create Date: 2026-07-15 18:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260715_0003"
down_revision: str | Sequence[str] | None = "20260715_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_profiles",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("nickname", sa.Text(), nullable=False),
        sa.Column("nickname_normalized", sa.Text(), nullable=False),
        sa.Column("password", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.Column("deleted_at", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "length(nickname) BETWEEN 2 AND 14",
            name="ck_user_profiles_nickname_length",
        ),
        sa.CheckConstraint(
            "length(password) = 4 AND password GLOB '[0-9][0-9][0-9][0-9]'",
            name="ck_user_profiles_password_format",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "nickname_normalized",
            name="uq_user_profiles_nickname_normalized",
        ),
    )


def downgrade() -> None:
    op.drop_table("user_profiles")
