"""Database constraint tests for durable idempotency records."""

import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.common.models import IdempotencyRecord
from app.database import Base


def _record(*, key: str, fingerprint: str = "a" * 64) -> IdempotencyRecord:
    return IdempotencyRecord(
        id=str(uuid4()),
        scope_key="profile:88a6f640-72fb-4e67-a05f-47b2809b76ff",
        http_method="POST",
        request_path="/api/v1/date-courses/current/complete",
        idempotency_key=key,
        request_fingerprint=fingerprint,
        status="PROCESSING",
        response_status_code=None,
        response_body_json=None,
        created_at="2026-07-15T14:30:00+09:00",
        updated_at="2026-07-15T14:30:00+09:00",
        expires_at="2026-07-16T14:30:00+09:00",
    )


class IdempotencyRecordTest(unittest.TestCase):
    def test_unique_request_scope_rejects_duplicate_key(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "test.db"
            engine = create_engine(f"sqlite:///{database_path.as_posix()}")
            Base.metadata.create_all(engine)
            key = str(uuid4())

            with Session(engine) as session:
                session.add(_record(key=key))
                session.commit()
                session.add(_record(key=key))
                with self.assertRaises(IntegrityError):
                    session.commit()
                session.rollback()

            engine.dispose()

    def test_completed_record_requires_a_status_code_and_body(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "test.db"
            engine = create_engine(f"sqlite:///{database_path.as_posix()}")
            Base.metadata.create_all(engine)
            record = _record(key=str(uuid4()))
            record.status = "COMPLETED"

            with Session(engine) as session:
                session.add(record)
                with self.assertRaises(IntegrityError):
                    session.commit()
                session.rollback()

            engine.dispose()


if __name__ == "__main__":
    unittest.main()
