"""SQLAlchemy persistence models for Common infrastructure."""

from sqlalchemy import CheckConstraint, Index, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class IdempotencyRecord(Base):
    """A durable replay record for protected mutating requests."""

    __tablename__ = "idempotency_records"
    __table_args__ = (
        UniqueConstraint(
            "scope_key",
            "http_method",
            "request_path",
            "idempotency_key",
            name="uq_idempotency_scope_method_path_key",
        ),
        CheckConstraint(
            "http_method IN ('POST', 'PUT', 'PATCH', 'DELETE')",
            name="ck_idempotency_records_http_method",
        ),
        CheckConstraint(
            "status IN ('PROCESSING', 'COMPLETED')",
            name="ck_idempotency_records_status",
        ),
        CheckConstraint(
            "length(request_fingerprint) = 64",
            name="ck_idempotency_records_request_fingerprint",
        ),
        CheckConstraint(
            "response_status_code IS NULL OR response_status_code BETWEEN 100 AND 599",
            name="ck_idempotency_records_response_status_code",
        ),
        CheckConstraint(
            "(status = 'PROCESSING' AND response_status_code IS NULL "
            "AND response_body_json IS NULL) OR "
            "(status = 'COMPLETED' AND response_status_code IS NOT NULL "
            "AND response_body_json IS NOT NULL)",
            name="ck_idempotency_records_completion_payload",
        ),
        Index("ix_idempotency_records_expires_at", "expires_at"),
        Index("ix_idempotency_records_status_expires_at", "status", "expires_at"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    scope_key: Mapped[str] = mapped_column(Text, nullable=False)
    http_method: Mapped[str] = mapped_column(Text, nullable=False)
    request_path: Mapped[str] = mapped_column(Text, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(Text, nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    response_status_code: Mapped[int | None] = mapped_column(Integer)
    response_body_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[str] = mapped_column(Text, nullable=False)
