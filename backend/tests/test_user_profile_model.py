"""Database constraint tests for anonymous user profiles."""

import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.infrastructure.models import UserProfile
from app.database import Base


def _profile(
    *,
    nickname: str,
    nickname_normalized: str,
    password: str = "0420",
) -> UserProfile:
    return UserProfile(
        id=str(uuid4()),
        nickname=nickname,
        nickname_normalized=nickname_normalized,
        password=password,
        created_at="2026-07-15T18:00:00+09:00",
        updated_at="2026-07-15T18:00:00+09:00",
        deleted_at=None,
    )


class UserProfileModelTest(unittest.TestCase):
    def test_normalized_nickname_is_unique(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "profile-test.db"
            engine = create_engine(f"sqlite:///{database_path.as_posix()}")
            Base.metadata.create_all(engine)

            with Session(engine) as session:
                session.add(_profile(nickname="Couple", nickname_normalized="couple"))
                session.commit()
                session.add(_profile(nickname="ＣＯＵＰＬＥ", nickname_normalized="couple"))
                with self.assertRaises(IntegrityError):
                    session.commit()

            engine.dispose()

    def test_password_constraint_rejects_non_digit_values(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "profile-test.db"
            engine = create_engine(f"sqlite:///{database_path.as_posix()}")
            Base.metadata.create_all(engine)

            with Session(engine) as session:
                session.add(
                    _profile(
                        nickname="복숭아와호두",
                        nickname_normalized="복숭아와호두",
                        password="12ab",
                    )
                )
                with self.assertRaises(IntegrityError):
                    session.commit()

            engine.dispose()
