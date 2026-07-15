"""Create the places table for TourAPI public data.

Revision ID: 20260715_0001
Revises:
Create Date: 2026-07-15
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260715_0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the public place storage and lookup indexes."""
    op.create_table(
        "places",
        sa.Column("content_id", sa.Text(), primary_key=True),
        sa.Column("content_type_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("address_detail", sa.Text(), nullable=False),
        sa.Column("zipcode", sa.Text(), nullable=False),
        sa.Column("telephone", sa.Text(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("map_level", sa.Integer()),
        sa.Column("area_code", sa.Text(), nullable=False),
        sa.Column("sigungu_code", sa.Text(), nullable=False),
        sa.Column("legal_region_code", sa.Text(), nullable=False),
        sa.Column("legal_sigungu_code", sa.Text(), nullable=False),
        sa.Column("category1", sa.Text(), nullable=False),
        sa.Column("category2", sa.Text(), nullable=False),
        sa.Column("category3", sa.Text(), nullable=False),
        sa.Column("class_code1", sa.Text(), nullable=False),
        sa.Column("class_code2", sa.Text(), nullable=False),
        sa.Column("class_code3", sa.Text(), nullable=False),
        sa.Column("image_url", sa.Text(), nullable=False),
        sa.Column("thumbnail_url", sa.Text(), nullable=False),
        sa.Column("copyright_code", sa.Text(), nullable=False),
        sa.Column("source_created_at", sa.Text()),
        sa.Column("source_modified_at", sa.Text()),
        sa.Column("district", sa.Text()),
        sa.Column("space_type", sa.Text()),
        sa.Column("moods_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("activities_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("keywords_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("description", sa.Text()),
        sa.Column("estimated_stay_minutes", sa.Integer()),
        sa.Column("estimated_cost", sa.Integer()),
        sa.Column("rain_suitability", sa.Float()),
        sa.Column("conversation_score", sa.Float()),
        sa.Column("photo_score", sa.Float()),
        sa.Column("is_recommendable", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.CheckConstraint(
            "content_type_id IN (12, 14, 25, 28, 32, 38, 39)",
            name="ck_places_content_type_id",
        ),
        sa.CheckConstraint(
            "is_recommendable IN (0, 1)",
            name="ck_places_is_recommendable",
        ),
    )
    op.create_index("ix_places_content_type_id", "places", ["content_type_id"])
    op.create_index("ix_places_district", "places", ["district"])
    op.create_index("ix_places_recommendable", "places", ["is_recommendable"])
    op.create_index("ix_places_title", "places", ["title"])
    op.create_index("ix_places_coordinates", "places", ["latitude", "longitude"])


def downgrade() -> None:
    """Drop the public place storage."""
    op.drop_index("ix_places_coordinates", table_name="places")
    op.drop_index("ix_places_title", table_name="places")
    op.drop_index("ix_places_recommendable", table_name="places")
    op.drop_index("ix_places_district", table_name="places")
    op.drop_index("ix_places_content_type_id", table_name="places")
    op.drop_table("places")
