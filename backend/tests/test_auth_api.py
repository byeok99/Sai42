"""Identity API contract tests."""

import sqlite3
import tempfile
import unittest
from collections.abc import AsyncIterator
from pathlib import Path
from uuid import UUID, uuid4

import httpx
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import Settings
from app.database import Base, get_database_session
from app.main import create_app
from app.place.infrastructure.models import Place

PUBLIC_DATABASE_PATH = Path(__file__).resolve().parents[1] / "data" / "sai42.db"


def _stored_public_place() -> dict[str, object]:
    database_uri = f"file:{PUBLIC_DATABASE_PATH.as_posix()}?mode=ro"
    with sqlite3.connect(database_uri, uri=True) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            SELECT *
            FROM places
            WHERE is_recommendable = 1
            ORDER BY content_id
            LIMIT 1
            """
        ).fetchone()
    if row is None:
        raise AssertionError("추적 DB에 추천 가능한 공공 장소가 필요합니다.")
    return dict(row)


class AuthApiTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        database_path = Path(self.temporary_directory.name) / "auth-test.db"
        database_url = f"sqlite+aiosqlite:///{database_path.as_posix()}"
        self.engine = create_async_engine(database_url)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        public_place = _stored_public_place()
        self.public_place_title = str(public_place["title"])
        async with self.session_factory() as session:
            session.add(Place(**public_place))
            await session.commit()

        self.app = create_app(
            Settings(
                database_url=database_url,
                auth_rate_limit_max_attempts=2,
                auth_rate_limit_window_seconds=60,
            )
        )

        async def override_session() -> AsyncIterator[AsyncSession]:
            async with self.session_factory() as session:
                yield session

        self.app.dependency_overrides[get_database_session] = override_session

    async def asyncTearDown(self) -> None:
        self.app.dependency_overrides.clear()
        await self.engine.dispose()
        self.temporary_directory.cleanup()

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            transport=httpx.ASGITransport(app=self.app, raise_app_exceptions=False),
            base_url="http://testserver",
        )

    async def _create_profile(
        self,
        client: httpx.AsyncClient,
        *,
        nickname: str = "복숭아와호두",
        password: str = "0420",
    ) -> httpx.Response:
        return await client.post(
            "/api/v1/auth/profiles",
            json={"nickname": nickname, "password": password},
        )

    async def test_nickname_suggestions_come_from_stored_public_places(self) -> None:
        async with self._client() as client:
            response = await client.get(
                "/api/v1/auth/nickname-suggestions",
                params={"count": 3},
            )

        self.assertEqual(200, response.status_code)
        suggestions = response.json()["data"]["suggestions"]
        self.assertEqual(3, len(suggestions))
        title_token = "".join(
            character for character in self.public_place_title if character.isalnum()
        )
        expected_prefix = title_token[: min(len(title_token), 11)]
        self.assertTrue(all(suggestion.startswith(expected_prefix) for suggestion in suggestions))

    async def test_register_verify_and_get_my_profile(self) -> None:
        async with self._client() as client:
            created_response = await self._create_profile(
                client,
                nickname="  복숭아와호두  ",
            )
            created = created_response.json()["data"]
            verified_response = await client.post(
                "/api/v1/auth/verify",
                json={"nickname": "복숭아와호두", "password": "0420"},
            )
            my_profile_response = await client.get(
                "/api/v1/profiles/me",
                headers={
                    "X-Profile-Id": created["profileId"],
                    "X-User-Password": "0420",
                },
            )

        self.assertEqual(201, created_response.status_code)
        self.assertEqual("복숭아와호두", created["nickname"])
        UUID(created["profileId"])
        self.assertNotIn("0420", created_response.text)
        self.assertEqual(200, verified_response.status_code)
        self.assertEqual(created["profileId"], verified_response.json()["data"]["profileId"])
        self.assertEqual(200, my_profile_response.status_code)
        self.assertEqual(0, my_profile_response.json()["data"]["publishedCourseCount"])

    async def test_duplicate_and_validation_errors_follow_the_common_contract(self) -> None:
        async with self._client() as client:
            first_response = await self._create_profile(client, nickname="Couple")
            duplicate_response = await self._create_profile(
                client,
                nickname="ＣＯＵＰＬＥ",
            )
            invalid_password_response = await client.post(
                "/api/v1/auth/verify",
                json={"nickname": "Couple", "password": "12ab"},
            )

        self.assertEqual(201, first_response.status_code)
        self.assertEqual(409, duplicate_response.status_code)
        self.assertEqual("AUTH_NICKNAME_ALREADY_EXISTS", duplicate_response.json()["code"])
        self.assertEqual(422, invalid_password_response.status_code)
        password_errors = [
            error
            for error in invalid_password_response.json()["errors"]
            if error["field"] == "password"
        ]
        self.assertTrue(password_errors)
        self.assertIsNone(password_errors[0]["rejectedValue"])
        self.assertNotIn("12ab", invalid_password_response.text)

    async def test_reserved_nickname_is_rejected(self) -> None:
        async with self._client() as client:
            response = await self._create_profile(client, nickname="관리자커플")

        self.assertEqual(422, response.status_code)
        self.assertEqual("COMMON_VALIDATION_ERROR", response.json()["code"])

    async def test_required_headers_hide_profile_existence(self) -> None:
        async with self._client() as client:
            missing_response = await client.get("/api/v1/profiles/me")
            malformed_response = await client.get(
                "/api/v1/profiles/me",
                headers={
                    "X-Profile-Id": "not-a-uuid",
                    "X-User-Password": "0420",
                },
            )
            unknown_response = await client.get(
                "/api/v1/profiles/me",
                headers={
                    "X-Profile-Id": str(uuid4()),
                    "X-User-Password": "0420",
                },
            )

        self.assertEqual("AUTH_CREDENTIALS_REQUIRED", missing_response.json()["code"])
        self.assertEqual("AUTH_INVALID_PROFILE_ID_FORMAT", malformed_response.json()["code"])
        self.assertEqual("AUTH_INVALID_CREDENTIALS", unknown_response.json()["code"])

    async def test_repeated_verification_failures_are_rate_limited(self) -> None:
        async with self._client() as client:
            await self._create_profile(client)
            responses = [
                await client.post(
                    "/api/v1/auth/verify",
                    json={"nickname": "복숭아와호두", "password": "9999"},
                )
                for _ in range(3)
            ]

        self.assertEqual([401, 401, 429], [response.status_code for response in responses])
        self.assertEqual("AUTH_TOO_MANY_ATTEMPTS", responses[-1].json()["code"])

    async def test_openapi_exposes_identity_contracts(self) -> None:
        async with self._client() as client:
            response = await client.get("/openapi.json")

        self.assertEqual(200, response.status_code)
        schema = response.json()
        self.assertIn("/api/v1/auth/profiles", schema["paths"])
        self.assertIn("/api/v1/auth/verify", schema["paths"])
        self.assertIn("/api/v1/profiles/me", schema["paths"])
        password_schema = schema["components"]["schemas"]["CreateProfileRequestDto"]["properties"][
            "password"
        ]
        self.assertTrue(password_schema["writeOnly"])
        self.assertEqual("password", password_schema["format"])
