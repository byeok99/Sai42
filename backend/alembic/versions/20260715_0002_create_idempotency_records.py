"""Create durable idempotency request records.

Revision ID: 20260715_0002
Revises: 20260715_0001
Create Date: 2026-07-15
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260715_0002"
down_revision: str | Sequence[str] | None = "20260715_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create request replay storage and cleanup indexes."""
    op.create_table(
        "idempotency_records",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("scope_key", sa.Text(), nullable=False),
        sa.Column("http_method", sa.Text(), nullable=False),
        sa.Column("request_path", sa.Text(), nullable=False),
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        sa.Column("request_fingerprint", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("response_status_code", sa.Integer()),
        sa.Column("response_body_json", sa.Text()),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.Text(), nullable=False),
        sa.UniqueConstraint(
            "scope_key",
            "http_method",
            "request_path",
            "idempotency_key",
            name="uq_idempotency_scope_method_path_key",
        ),
        sa.CheckConstraint(
            "http_method IN ('POST', 'PUT', 'PATCH', 'DELETE')",
            name="ck_idempotency_records_http_method",
        ),
        sa.CheckConstraint(
            "status IN ('PROCESSING', 'COMPLETED')",
            name="ck_idempotency_records_status",
        ),
        sa.CheckConstraint(
            "length(request_fingerprint) = 64",
            name="ck_idempotency_records_request_fingerprint",
        ),
        sa.CheckConstraint(
            "response_status_code IS NULL OR response_status_code BETWEEN 100 AND 599",
            name="ck_idempotency_records_response_status_code",
        ),
        sa.CheckConstraint(
            "(status = 'PROCESSING' AND response_status_code IS NULL "
            "AND response_body_json IS NULL) OR "
            "(status = 'COMPLETED' AND response_status_code IS NOT NULL "
            "AND response_body_json IS NOT NULL)",
            name="ck_idempotency_records_completion_payload",
        ),
    )
    op.create_index(
        "ix_idempotency_records_expires_at",
        "idempotency_records",
        ["expires_at"],
    )
    op.create_index(
        "ix_idempotency_records_status_expires_at",
        "idempotency_records",
        ["status", "expires_at"],
    )


def downgrade() -> None:
    """Drop durable idempotency request records."""
    op.drop_index("ix_idempotency_records_status_expires_at", table_name="idempotency_records")
    op.drop_index("ix_idempotency_records_expires_at", table_name="idempotency_records")
    op.drop_table("idempotency_records")
