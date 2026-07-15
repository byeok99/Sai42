"""Current DateCourse API tests using snapshots from tracked public places."""

import sqlite3
import tempfile
import unittest
from collections.abc import AsyncIterator
from pathlib import Path
from uuid import uuid4

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.models  # noqa: F401 - register the complete metadata for create_all
from app.auth.infrastructure.models import UserProfile
from app.community.infrastructure.models import CommunityPost
from app.config import Settings
from app.course.infrastructure.models import DateCourse, DateCoursePlace
from app.database import Base, get_database_session
from app.main import create_app
from app.place.infrastructure.models import Place

PUBLIC_DATABASE_PATH = Path(__file__).resolve().parents[1] / "data" / "sai42.db"
PASSWORD = "0420"


def _stored_public_places() -> list[dict[str, object]]:
    database_uri = f"file:{PUBLIC_DATABASE_PATH.as_posix()}?mode=ro"
    with sqlite3.connect(database_uri, uri=True) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT *
            FROM places
            WHERE is_recommendable = 1
              AND district IS NOT NULL
            ORDER BY content_id
            LIMIT 2
            """
        ).fetchall()
    if len(rows) != 2:
        raise AssertionError("추적 DB에 코스 테스트용 공공 장소 2개가 필요합니다.")
    return [dict(row) for row in rows]


class DateCourseApiTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        database_path = Path(self.temporary_directory.name) / "date-course-test.db"
        database_url = f"sqlite+aiosqlite:///{database_path.as_posix()}"
        self.engine = create_async_engine(database_url)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        public_places = _stored_public_places()
        self.profile_id = str(uuid4())
        self.course_id = str(uuid4())
        self.course_place_ids = [str(uuid4()), str(uuid4())]
        timestamp = "2026-07-15T14:00:00+09:00"
        async with self.session_factory() as session:
            session.add_all(Place(**row) for row in public_places)
            session.add(
                UserProfile(
                    id=self.profile_id,
                    nickname="복숭아와호두",
                    nickname_normalized="복숭아와호두",
                    password=PASSWORD,
                    created_at=timestamp,
                    updated_at=timestamp,
                    deleted_at=None,
                )
            )
            session.add(
                DateCourse(
                    id=self.course_id,
                    profile_id=self.profile_id,
                    chat_session_id=None,
                    status="ACTIVE",
                    source_type="AI_CHAT",
                    source_course_id=None,
                    title="공공 장소 데이트",
                    date="2026-07-15",
                    start_time="14:00",
                    time_slot="AFTERNOON",
                    main_district=public_places[0]["district"],
                    space_type="ANY",
                    moods_json='["QUIET"]',
                    activities_json='["TOURISM"]',
                    schedule_density="NORMAL",
                    transportation="PUBLIC_TRANSIT",
                    overall_comment="저장된 공공 장소로 구성한 코스입니다.",
                    tags_json='["#대전데이트"]',
                    weather_json=None,
                    current_order_no=1,
                    completion_comment=None,
                    started_at=None,
                    completed_at=None,
                    created_at=timestamp,
                    updated_at=timestamp,
                )
            )
            for index, public_place in enumerate(public_places):
                session.add(
                    DateCoursePlace(
                        id=self.course_place_ids[index],
                        date_course_id=self.course_id,
                        content_id=public_place["content_id"],
                        order_no=index + 1,
                        scheduled_at=f"2026-07-15T{14 + index * 2:02d}:00:00+09:00",
                        estimated_stay_minutes=60,
                        sweet_comment="실제 공공 장소를 함께 둘러보세요.",
                        hearted=0,
                        hearted_at=None,
                        completed_at=None,
                        title_snapshot=public_place["title"],
                        address_snapshot=public_place["address"],
                        address_detail_snapshot=public_place["address_detail"],
                        longitude_snapshot=public_place["longitude"],
                        latitude_snapshot=public_place["latitude"],
                        content_type_id_snapshot=public_place["content_type_id"],
                        district_snapshot=public_place["district"],
                        space_type_snapshot=public_place["space_type"] or "ANY",
                        image_url_snapshot=public_place["image_url"] or None,
                        created_at=timestamp,
                    )
                )
            await session.commit()

        self.app = create_app(Settings(database_url=database_url))

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
            headers={"X-Profile-Id": self.profile_id, "X-User-Password": PASSWORD},
        )

    async def test_current_course_returns_snapshot_map_and_progress(self) -> None:
        async with self._client() as client:
            response = await client.get("/api/v1/date-courses/current")

        self.assertEqual(200, response.status_code, response.text)
        data = response.json()["data"]
        self.assertEqual(self.course_id, data["courseId"])
        self.assertEqual(180, data["estimatedTotalMinutes"])
        self.assertEqual(2, len(data["places"]))
        self.assertEqual(2, len(data["map"]["polyline"]))
        self.assertEqual(0, data["progress"]["completedPlaceCount"])
        self.assertFalse(data["progress"]["allPlacesCompleted"])

    async def test_place_completion_is_sequential_and_idempotent(self) -> None:
        async with self._client() as client:
            conflict = await client.put(
                f"/api/v1/date-courses/current/places/{self.course_place_ids[1]}/complete"
            )
            first = await client.put(
                f"/api/v1/date-courses/current/places/{self.course_place_ids[0]}/complete"
            )
            repeated = await client.put(
                f"/api/v1/date-courses/current/places/{self.course_place_ids[0]}/complete"
            )
            last = await client.put(
                f"/api/v1/date-courses/current/places/{self.course_place_ids[1]}/complete"
            )

        self.assertEqual(409, conflict.status_code)
        self.assertEqual("DATE_COURSE_PLACE_SEQUENCE_CONFLICT", conflict.json()["code"])
        self.assertEqual(
            first.json()["data"]["completedPlace"]["completedAt"],
            repeated.json()["data"]["completedPlace"]["completedAt"],
        )
        self.assertEqual(1, repeated.json()["data"]["completedPlaceCount"])
        self.assertEqual(100, last.json()["data"]["progressPercent"])
        self.assertIsNone(last.json()["data"]["nextPlace"])
        self.assertTrue(last.json()["data"]["allPlacesCompleted"])

    async def test_heart_is_idempotent_and_completion_publishes_atomically(self) -> None:
        first_place_url = f"/api/v1/date-courses/current/places/{self.course_place_ids[0]}"
        async with self._client() as client:
            incomplete = await client.post(
                "/api/v1/date-courses/current/complete",
                json={"oneLineComment": "좋은 데이트였어요."},
            )
            hearted = await client.put(f"{first_place_url}/heart")
            hearted_again = await client.put(f"{first_place_url}/heart")
            unhearted = await client.delete(f"{first_place_url}/heart")
            unhearted_again = await client.delete(f"{first_place_url}/heart")
            for course_place_id in self.course_place_ids:
                await client.put(f"/api/v1/date-courses/current/places/{course_place_id}/complete")
            completed = await client.post(
                "/api/v1/date-courses/current/complete",
                json={"oneLineComment": "  이동이 편한 데이트였어요.  "},
            )
            current = await client.get("/api/v1/date-courses/current")
            profile = await client.get("/api/v1/profiles/me")

        self.assertEqual("DATE_COURSE_PLACES_INCOMPLETE", incomplete.json()["code"])
        self.assertEqual(1, hearted.json()["data"]["heartCount"])
        self.assertEqual(1, hearted_again.json()["data"]["heartCount"])
        self.assertEqual(0, unhearted.json()["data"]["heartCount"])
        self.assertEqual(0, unhearted_again.json()["data"]["heartCount"])
        self.assertEqual(200, completed.status_code, completed.text)
        completion = completed.json()["data"]
        self.assertEqual("COMPLETED", completion["completedCourse"]["status"])
        self.assertEqual("PUBLISHED", completion["communityPost"]["status"])
        self.assertEqual("이동이 편한 데이트였어요.", completion["communityPost"]["oneLineComment"])
        self.assertEqual("DATE_COURSE_CURRENT_EMPTY", current.json()["code"])
        self.assertEqual(1, profile.json()["data"]["completedDateCourseCount"])
        self.assertEqual(1, profile.json()["data"]["publishedCourseCount"])
        async with self.session_factory() as session:
            post_count = await session.scalar(select(func.count(CommunityPost.id)))
        self.assertEqual(1, post_count)

    async def test_completion_comment_and_auth_validation_follow_common_contract(self) -> None:
        async with self._client() as client:
            blank = await client.post(
                "/api/v1/date-courses/current/complete", json={"oneLineComment": "   "}
            )
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=self.app, raise_app_exceptions=False),
            base_url="http://testserver",
        ) as anonymous:
            unauthorized = await anonymous.get("/api/v1/date-courses/current")

        self.assertEqual(422, blank.status_code)
        self.assertEqual("COMMUNITY_COMMENT_REQUIRED", blank.json()["code"])
        self.assertEqual(401, unauthorized.status_code)
        self.assertEqual("AUTH_CREDENTIALS_REQUIRED", unauthorized.json()["code"])

    async def test_completion_idempotency_replays_first_common_response(self) -> None:
        idempotency_key = str(uuid4())
        async with self._client() as client:
            for course_place_id in self.course_place_ids:
                await client.put(f"/api/v1/date-courses/current/places/{course_place_id}/complete")
            first = await client.post(
                "/api/v1/date-courses/current/complete",
                json={"oneLineComment": "기억에 남는 하루였어요."},
                headers={"Idempotency-Key": idempotency_key},
            )
            replayed = await client.post(
                "/api/v1/date-courses/current/complete",
                json={"oneLineComment": "기억에 남는 하루였어요."},
                headers={"Idempotency-Key": idempotency_key},
            )
            reused = await client.post(
                "/api/v1/date-courses/current/complete",
                json={"oneLineComment": "다른 코멘트입니다."},
                headers={"Idempotency-Key": idempotency_key},
            )

        self.assertEqual(200, first.status_code, first.text)
        self.assertEqual(first.json(), replayed.json())
        self.assertEqual(409, reused.status_code)
        self.assertEqual("COMMON_IDEMPOTENCY_KEY_REUSED", reused.json()["code"])
        async with self.session_factory() as session:
            post_count = await session.scalar(select(func.count(CommunityPost.id)))
        self.assertEqual(1, post_count)


if __name__ == "__main__":
    unittest.main()
