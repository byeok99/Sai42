"""Community, ranking, and history APIs over real stored public place snapshots."""

import sqlite3
import tempfile
import unittest
from collections.abc import AsyncIterator
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import httpx
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.models  # noqa: F401 - register full SQLAlchemy metadata
from app.auth.infrastructure.models import UserProfile
from app.common.domain.time import now_seoul
from app.community.infrastructure.models import CommunityPost
from app.config import Settings
from app.course.infrastructure.models import DateCourse, DateCoursePlace
from app.database import Base, get_database_session
from app.main import create_app
from app.place.infrastructure.models import Place

PUBLIC_DATABASE_PATH = Path(__file__).resolve().parents[1] / "data" / "sai42.db"
PASSWORD = "0420"


def _public_places() -> list[dict[str, object]]:
    with sqlite3.connect(f"file:{PUBLIC_DATABASE_PATH.as_posix()}?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT * FROM places
            WHERE is_recommendable = 1 AND district IS NOT NULL
            ORDER BY content_id LIMIT 2
            """
        ).fetchall()
    if len(rows) != 2:
        raise AssertionError("추적 DB에 테스트할 공공 장소 2개가 필요합니다.")
    return [dict(row) for row in rows]


class CommunityHistoryApiTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        path = Path(self.temporary_directory.name) / "community-test.db"
        database_url = f"sqlite+aiosqlite:///{path.as_posix()}"
        self.engine = create_async_engine(database_url)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        places = _public_places()
        self.owner_id = str(uuid4())
        self.reader_id = str(uuid4())
        self.course_id = str(uuid4())
        self.post_id = str(uuid4())
        timestamp = "2026-07-15T18:00:00+09:00"
        async with self.sessions() as session:
            session.add_all(Place(**place) for place in places)
            session.add_all(
                [
                    UserProfile(
                        id=self.owner_id,
                        nickname="대전산책단",
                        nickname_normalized="대전산책단",
                        password=PASSWORD,
                        created_at=timestamp,
                        updated_at=timestamp,
                        deleted_at=None,
                    ),
                    UserProfile(
                        id=self.reader_id,
                        nickname="유성구름단",
                        nickname_normalized="유성구름단",
                        password=PASSWORD,
                        created_at=timestamp,
                        updated_at=timestamp,
                        deleted_at=None,
                    ),
                ]
            )
            session.add(
                DateCourse(
                    id=self.course_id,
                    profile_id=self.owner_id,
                    chat_session_id=None,
                    status="COMPLETED",
                    source_type="AI_CHAT",
                    source_course_id=None,
                    title="대전 공공 장소 코스",
                    date="2026-07-15",
                    start_time="14:00",
                    time_slot="AFTERNOON",
                    main_district=places[0]["district"],
                    space_type="ANY",
                    moods_json='["QUIET"]',
                    activities_json='["TOURISM"]',
                    schedule_density="NORMAL",
                    transportation="PUBLIC_TRANSIT",
                    overall_comment="실제 공공 장소 스냅샷 코스입니다.",
                    tags_json='["#대전"]',
                    weather_json=None,
                    current_order_no=2,
                    completion_comment="이동이 편했어요.",
                    started_at=timestamp,
                    completed_at=timestamp,
                    created_at=timestamp,
                    updated_at=timestamp,
                )
            )
            for index, place in enumerate(places):
                session.add(
                    DateCoursePlace(
                        id=str(uuid4()),
                        date_course_id=self.course_id,
                        content_id=place["content_id"],
                        order_no=index + 1,
                        scheduled_at=f"2026-07-15T{14 + index * 2:02d}:00:00+09:00",
                        estimated_stay_minutes=60,
                        sweet_comment="함께 둘러보세요.",
                        hearted=1 if index == 0 else 0,
                        hearted_at=timestamp if index == 0 else None,
                        completed_at=timestamp,
                        title_snapshot=place["title"],
                        address_snapshot=place["address"],
                        address_detail_snapshot=place["address_detail"],
                        longitude_snapshot=place["longitude"],
                        latitude_snapshot=place["latitude"],
                        content_type_id_snapshot=place["content_type_id"],
                        district_snapshot=place["district"],
                        space_type_snapshot=place["space_type"] or "ANY",
                        image_url_snapshot=place["image_url"] or None,
                        created_at=timestamp,
                    )
                )
            session.add(
                CommunityPost(
                    id=self.post_id,
                    date_course_id=self.course_id,
                    author_profile_id=self.owner_id,
                    author_nickname_snapshot="대전산책단",
                    one_line_comment="이동이 편했어요.",
                    status="PUBLISHED",
                    published_at=timestamp,
                    updated_at=timestamp,
                    deleted_at=None,
                )
            )
            await session.commit()

        self.app = create_app(Settings(database_url=database_url))

        async def override_session() -> AsyncIterator[AsyncSession]:
            async with self.sessions() as session:
                yield session

        self.app.dependency_overrides[get_database_session] = override_session

    async def asyncTearDown(self) -> None:
        self.app.dependency_overrides.clear()
        await self.engine.dispose()
        self.temporary_directory.cleanup()

    def _client(self, profile_id: str | None = None) -> httpx.AsyncClient:
        headers = {"X-Profile-Id": profile_id, "X-User-Password": PASSWORD} if profile_id else None
        return httpx.AsyncClient(
            transport=httpx.ASGITransport(app=self.app, raise_app_exceptions=False),
            base_url="http://testserver",
            headers=headers,
        )

    async def test_public_list_detail_like_and_master_ranking(self) -> None:
        async with self._client() as anonymous:
            listed = await anonymous.get("/api/v1/community/posts", params={"sort": "POPULAR"})
            detail = await anonymous.get(f"/api/v1/community/posts/{self.post_id}")
        async with self._client(self.reader_id) as reader:
            liked = await reader.put(f"/api/v1/community/posts/{self.post_id}/like")
            liked_again = await reader.put(f"/api/v1/community/posts/{self.post_id}/like")
            personalized = await reader.get(f"/api/v1/community/posts/{self.post_id}")
            masters = await reader.get("/api/v1/rankings/masters")
            unliked = await reader.delete(f"/api/v1/community/posts/{self.post_id}/like")

        self.assertEqual(200, listed.status_code, listed.text)
        self.assertEqual(self.post_id, listed.json()["data"][0]["postId"])
        self.assertEqual(1, listed.json()["data"][0]["placeHeartCount"])
        self.assertFalse(detail.json()["data"]["owner"])
        self.assertEqual(1, liked.json()["data"]["likeCount"])
        self.assertEqual(1, liked_again.json()["data"]["likeCount"])
        self.assertTrue(personalized.json()["data"]["likedByMe"])
        self.assertEqual(self.owner_id, masters.json()["data"]["masters"][0]["profileId"])
        self.assertEqual(1, masters.json()["data"]["masters"][0]["receivedLikeCount"])
        self.assertEqual(0, unliked.json()["data"]["likeCount"])

    async def test_owner_update_delete_and_idempotent_republish(self) -> None:
        key = str(uuid4())
        async with self._client(self.owner_id) as owner:
            updated = await owner.patch(
                f"/api/v1/community/posts/{self.post_id}",
                json={"oneLineComment": "  다시 걷고 싶은 코스예요.  "},
            )
            deleted = await owner.delete(f"/api/v1/community/posts/{self.post_id}")
            hidden = await owner.get(f"/api/v1/community/posts/{self.post_id}")
            restored = await owner.post(
                "/api/v1/community/posts",
                json={
                    "dateCourseId": self.course_id,
                    "oneLineComment": "다시 공개합니다.",
                },
                headers={"Idempotency-Key": key},
            )
            replayed = await owner.post(
                "/api/v1/community/posts",
                json={
                    "dateCourseId": self.course_id,
                    "oneLineComment": "다시 공개합니다.",
                },
                headers={"Idempotency-Key": key},
            )

        self.assertEqual("다시 걷고 싶은 코스예요.", updated.json()["data"]["oneLineComment"])
        self.assertEqual("COMMUNITY_POST_DELETED", deleted.json()["code"])
        self.assertEqual(404, hidden.status_code)
        self.assertEqual(200, restored.status_code, restored.text)
        self.assertEqual(restored.json(), replayed.json())

    async def test_history_list_detail_and_restart_copy_snapshots(self) -> None:
        future = (now_seoul().date() + timedelta(days=1)).isoformat()
        async with self._client(self.owner_id) as owner:
            listed = await owner.get(
                "/api/v1/profiles/me/date-courses",
                params={"year": 2026, "month": 7},
            )
            detail = await owner.get(f"/api/v1/profiles/me/date-courses/{self.course_id}")
            restarted = await owner.post(
                f"/api/v1/profiles/me/date-courses/{self.course_id}/restart",
                json={"date": future, "startTime": "15:00"},
                headers={"Idempotency-Key": str(uuid4())},
            )

        self.assertEqual(1, listed.json()["meta"]["totalElements"])
        self.assertEqual(1, listed.json()["data"][0]["heartedPlaceCount"])
        self.assertEqual(self.course_id, detail.json()["data"]["courseId"])
        self.assertEqual(201, restarted.status_code, restarted.text)
        copied = restarted.json()["data"]
        self.assertEqual("ACTIVE", copied["status"])
        self.assertEqual("HISTORY_RESTART", copied["sourceType"])
        self.assertTrue(all(not place["heartedByMe"] for place in copied["places"]))
        self.assertEqual(0, copied["progress"]["completedPlaceCount"])

    async def test_public_post_start_creates_ranking_copy(self) -> None:
        future = (now_seoul().date() + timedelta(days=1)).isoformat()
        async with self._client(self.reader_id) as reader:
            response = await reader.post(
                f"/api/v1/community/posts/{self.post_id}/start",
                json={"date": future, "startTime": "16:00"},
                headers={"Idempotency-Key": str(uuid4())},
            )

        self.assertEqual(201, response.status_code, response.text)
        data = response.json()["data"]
        self.assertEqual("RANKING_COPY", data["activeCourse"]["sourceType"])
        self.assertEqual(self.post_id, data["copyResult"]["sourcePostId"])


if __name__ == "__main__":
    unittest.main()
