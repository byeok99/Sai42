"""AI chat and course confirmation APIs over tracked public place rows."""

import sqlite3
import tempfile
import unittest
from collections.abc import AsyncIterator
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.models  # noqa: F401 - register full SQLAlchemy metadata
from app.auth.infrastructure.models import UserProfile
from app.chat.application.service import QUALITY_FALLBACK_WARNING, TRANSITION_BUFFER_MINUTES
from app.chat.application.travel import estimate_travel_minutes
from app.chat.domain.entities import (
    AiChatTurn,
    AiConversationMemory,
    AiCourseContent,
    AiCoursePlace,
    AiCoursePlan,
    AiCourseRequest,
)
from app.chat.domain.enums import ChatTurnIntent
from app.chat.infrastructure.models import ChatSession
from app.chat.presentation.dependencies import get_ai_course_provider
from app.common.domain.enums import ScheduleDensity, SpaceType, Transportation
from app.common.domain.time import now_seoul
from app.config import Settings
from app.database import Base, get_database_session
from app.main import create_app
from app.place.infrastructure.models import Place
from app.weather.presentation.dependencies import get_weather_provider

PUBLIC_DATABASE_PATH = Path(__file__).resolve().parents[1] / "data" / "sai42.db"
PASSWORD = "0420"


def _public_places() -> list[dict[str, object]]:
    with sqlite3.connect(f"file:{PUBLIC_DATABASE_PATH.as_posix()}?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT * FROM (
                SELECT places.*,
                       ROW_NUMBER() OVER (
                           PARTITION BY content_type_id ORDER BY content_id
                       ) AS category_order
                FROM places
                WHERE is_recommendable = 1 AND district = 'YUSEONG_GU'
                  AND content_type_id IN (12, 14, 38, 39)
            )
            WHERE category_order <= 5
            ORDER BY content_type_id, content_id
            """
        ).fetchall()
    if len(rows) < 4:
        raise AssertionError("추적 DB에 테스트할 추천 가능 공공 장소가 부족합니다.")
    return [{key: row[key] for key in row.keys() if key != "category_order"} for row in rows]


class RecordingAiProvider:
    def __init__(self, *, invalid_content_id: bool = False) -> None:
        self.invalid_content_id = invalid_content_id
        self.requests: list[AiCourseRequest] = []

    def _plan(self, request: AiCourseRequest) -> AiCoursePlan:
        pool = request.candidates
        if request.current_draft is not None:
            alternatives = [candidate for candidate in pool if not candidate.is_current]
            if len(alternatives) >= 3:
                pool = alternatives
        selected = []
        for activity in request.conditions["activities"]:
            match = next(
                (
                    candidate
                    for candidate in pool
                    if activity in candidate.activities and candidate not in selected
                ),
                None,
            )
            if match is not None:
                selected.append(match)
        selected.extend(candidate for candidate in pool if candidate not in selected)
        selected = selected[:3]
        content_ids = [candidate.content_id for candidate in selected]
        if self.invalid_content_id:
            content_ids[0] = "NOT-IN-SQLITE"
        return AiCoursePlan(
            title="공공데이터로 만든 유성 데이트",
            overall_comment="실제 저장된 대전 장소만 이어 만든 코스예요.",
            assistant_message="요청한 조건으로 코스를 구성했어요.",
            tags=["#유성구", "#공공데이터"],
            places=[
                AiCoursePlace(
                    content_id=content_id,
                    estimated_stay_minutes=60,
                    space_type=SpaceType.INDOOR,
                    sweet_comment="함께 천천히 둘러보세요.",
                )
                for content_id in content_ids
            ],
            warnings=[],
        )

    @staticmethod
    def _updated_memory(request: AiCourseRequest) -> AiConversationMemory:
        previous = request.memory
        new_summary = " / ".join(item for item in (previous.summary, request.user_request) if item)[
            -1500:
        ]
        notes = [*previous.preference_notes, request.user_request[:160]][-12:]
        return previous.model_copy(
            update={
                "summary": new_summary,
                "preference_notes": list(dict.fromkeys(notes)),
            }
        )

    async def generate(self, request: AiCourseRequest) -> AiCoursePlan:
        self.requests.append(request)
        return self._plan(request)

    async def respond(self, request: AiCourseRequest) -> AiChatTurn:
        self.requests.append(request)
        message = request.user_request
        memory = self._updated_memory(request)
        if request.edit_action is not None or any(
            keyword in message for keyword in ("바꿔", "추가", "빼", "줄여", "늘려", "재생성")
        ):
            plan = self._plan(request)
            return AiChatTurn(
                intent=ChatTurnIntent.COURSE_EDIT,
                assistant_message=plan.assistant_message,
                proposed_course=AiCourseContent.model_validate(plan.model_dump()),
                warnings=plan.warnings,
                memory=memory,
            )
        if any(keyword in message for keyword in ("왜", "어디", "몇 시", "얼마나")):
            return AiChatTurn(
                intent=ChatTurnIntent.COURSE_QUESTION,
                assistant_message="현재 코스를 기준으로 차근차근 설명해 드릴게요.",
                memory=memory,
            )
        if any(keyword in message for keyword in ("안녕", "고마워", "기분")):
            return AiChatTurn(
                intent=ChatTurnIntent.CASUAL_CONVERSATION,
                assistant_message="안녕하세요! 오늘도 편안하게 이야기해요.",
                memory=memory,
            )
        return AiChatTurn(
            intent=ChatTurnIntent.CLARIFICATION_REQUIRED,
            assistant_message="어느 장소를 어떤 방향으로 조정할까요?",
            memory=memory.model_copy(update={"pending_clarification": message}),
        )


class StubbornAiProvider(RecordingAiProvider):
    """Keep the current places even when regeneration asks for a new combination."""

    def _plan(self, request: AiCourseRequest) -> AiCoursePlan:
        if request.current_draft is None:
            return super()._plan(request)
        current = [candidate for candidate in request.candidates if candidate.is_current]
        return AiCoursePlan(
            title="기존 코스 유지",
            overall_comment="검증할 수 없는 변경은 적용하지 않습니다.",
            assistant_message="기존 코스를 유지했어요.",
            tags=["#대전데이트"],
            places=[
                AiCoursePlace(
                    content_id=candidate.content_id,
                    estimated_stay_minutes=60,
                    space_type=SpaceType.INDOOR,
                    sweet_comment="함께 둘러보세요.",
                )
                for candidate in current[:3]
            ],
            warnings=[],
        )


class LeakyOnceAiProvider(RecordingAiProvider):
    """Expose an internal term once so the application-level repair can be verified."""

    async def generate(self, request: AiCourseRequest) -> AiCoursePlan:
        self.requests.append(request)
        plan = self._plan(request)
        if not request.validation_errors:
            return plan.model_copy(update={"assistant_message": "DB 후보를 ANY 조건으로 골랐어요."})
        return plan


class IntentChangingRepairProvider(RecordingAiProvider):
    """Try to turn a casual answer repair into an unrelated course edit."""

    async def respond(self, request: AiCourseRequest) -> AiChatTurn:
        self.requests.append(request)
        memory = self._updated_memory(request)
        if not request.validation_errors:
            return AiChatTurn(
                intent=ChatTurnIntent.CASUAL_CONVERSATION,
                assistant_message="DB 후보를 확인할게요.",
                memory=memory,
            )
        plan = self._plan(request)
        return AiChatTurn(
            intent=ChatTurnIntent.COURSE_EDIT,
            assistant_message=plan.assistant_message,
            proposed_course=AiCourseContent.model_validate(plan.model_dump()),
            memory=memory,
        )


class ChatApiTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        path = Path(self.temporary_directory.name) / "chat-test.db"
        self.engine = create_async_engine(f"sqlite+aiosqlite:///{path.as_posix()}")
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        self.public_places = _public_places()
        self.public_content_ids = {str(place["content_id"]) for place in self.public_places}
        self.profile_id = str(uuid4())
        timestamp = now_seoul().isoformat()
        async with self.sessions() as session:
            session.add_all(Place(**place) for place in self.public_places)
            session.add(
                UserProfile(
                    id=self.profile_id,
                    nickname="유성데이트단",
                    nickname_normalized="유성데이트단",
                    password=PASSWORD,
                    created_at=timestamp,
                    updated_at=timestamp,
                    deleted_at=None,
                )
            )
            await session.commit()

        self.provider = RecordingAiProvider()
        self.app = create_app(Settings(openai_candidate_limit=20))

        async def override_session() -> AsyncIterator[AsyncSession]:
            async with self.sessions() as session:
                yield session

        self.app.dependency_overrides[get_database_session] = override_session
        self.app.dependency_overrides[get_ai_course_provider] = lambda: self.provider
        self.app.dependency_overrides[get_weather_provider] = lambda: None
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=self.app, raise_app_exceptions=False),
            base_url="http://testserver",
        )
        self.headers = {
            "X-Profile-Id": self.profile_id,
            "X-User-Password": PASSWORD,
        }

    async def asyncTearDown(self) -> None:
        await self.client.aclose()
        await self.engine.dispose()
        self.temporary_directory.cleanup()

    def _create_body(self) -> dict[str, object]:
        return {
            "date": (now_seoul().date() + timedelta(days=1)).isoformat(),
            "timeSlot": "AFTERNOON",
            "startTime": "14:00",
            "district": "YUSEONG_GU",
            "spaceType": "INDOOR",
            "moods": ["QUIET", "EMOTIONAL"],
            "activities": ["CULTURE_EXHIBITION", "FOOD"],
            "scheduleDensity": "RELAXED",
            "transportation": "PUBLIC_TRANSIT",
            "initialMessage": "조용한 장소와 식당을 넣어줘.",
        }

    async def test_create_edit_confirm_uses_only_stored_public_places(self) -> None:
        created = await self.client.post(
            "/api/v1/chat/sessions", json=self._create_body(), headers=self.headers
        )
        self.assertEqual(201, created.status_code, created.text)
        created_body = created.json()
        self.assertEqual(
            {"success", "code", "message", "data", "meta", "timestamp", "traceId"},
            set(created_body),
        )
        self.assertEqual("CHAT_SESSION_CREATED", created_body["code"])
        created_data = created_body["data"]
        self.assertEqual(
            {"sessionId", "status", "assistantMessage", "courseDraft"}, set(created_data)
        )
        session_id = created_data["sessionId"]
        draft = created_data["courseDraft"]
        self.assertEqual(
            {
                "draftId",
                "version",
                "title",
                "date",
                "timeSlot",
                "overallComment",
                "estimatedTotalMinutes",
                "conditions",
                "tags",
                "weather",
                "places",
                "map",
            },
            set(draft),
        )
        self.assertEqual("14:00", draft["conditions"]["startTime"])
        self.assertEqual(1, draft["version"])
        self.assertEqual(3, len(draft["places"]))
        self.assertTrue(
            {place["place"]["contentId"] for place in draft["places"]}.issubset(
                self.public_content_ids
            )
        )
        self.assertTrue(self.provider.requests[0].weather is not None)
        self.assertFalse(self.provider.requests[0].weather["available"])

        detail = await self.client.get(f"/api/v1/chat/sessions/{session_id}", headers=self.headers)
        self.assertEqual(200, detail.status_code)
        detail_body = detail.json()
        self.assertEqual("COMMON_OK", detail_body["code"])
        self.assertEqual(
            {"sessionId", "status", "conditions", "messages", "courseDraft"},
            set(detail_body["data"]),
        )
        self.assertEqual(2, len(detail_body["data"]["messages"]))
        self.assertEqual(
            {"messageId", "role", "content", "createdAt"},
            set(detail_body["data"]["messages"][0]),
        )

        edited = await self.client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"quickAction": "REGENERATE", "expectedDraftVersion": 1},
            headers=self.headers,
        )
        self.assertEqual(200, edited.status_code, edited.text)
        edited_body = edited.json()
        self.assertEqual("CHAT_DRAFT_UPDATED", edited_body["code"])
        edited_data = edited_body["data"]
        self.assertEqual(
            {"userMessage", "assistantMessage", "changeSummary", "courseDraft"},
            set(edited_data),
        )
        self.assertTrue(edited_data["changeSummary"]["changed"])
        self.assertEqual(2, edited_data["courseDraft"]["version"])

        confirmed = await self.client.post(
            f"/api/v1/chat/sessions/{session_id}/confirm",
            json={"draftId": draft["draftId"], "expectedVersion": 2},
            headers={**self.headers, "Idempotency-Key": str(uuid4())},
        )
        self.assertEqual(201, confirmed.status_code, confirmed.text)
        confirmed_body = confirmed.json()
        self.assertEqual("CHAT_SESSION_CONFIRMED", confirmed_body["code"])
        course = confirmed_body["data"]
        self.assertEqual(
            {
                "courseId",
                "status",
                "sourceType",
                "title",
                "date",
                "timeSlot",
                "overallComment",
                "estimatedTotalMinutes",
                "conditions",
                "tags",
                "weather",
                "places",
                "map",
                "progress",
                "oneLineComment",
                "createdAt",
                "completedAt",
            },
            set(course),
        )
        self.assertEqual("AI_CHAT", course["sourceType"])
        self.assertEqual(3, len(course["places"]))
        self.assertTrue(
            {place["place"]["contentId"] for place in course["places"]}.issubset(
                self.public_content_ids
            )
        )

        current = await self.client.get("/api/v1/date-courses/current", headers=self.headers)
        self.assertEqual(200, current.status_code)
        self.assertEqual(course["courseId"], current.json()["data"]["courseId"])

    async def test_schedule_uses_coordinate_travel_time_and_transportation(self) -> None:
        created = await self.client.post(
            "/api/v1/chat/sessions", json=self._create_body(), headers=self.headers
        )
        self.assertEqual(201, created.status_code, created.text)
        draft = created.json()["data"]["courseDraft"]
        places = draft["places"]
        scheduled = [datetime.fromisoformat(place["scheduledAt"]) for place in places]

        for index in range(len(places) - 1):
            current = places[index]
            following = places[index + 1]
            current_location = current["place"]
            following_location = following["place"]
            travel_minutes = estimate_travel_minutes(
                (current_location["latitude"], current_location["longitude"]),
                (following_location["latitude"], following_location["longitude"]),
                Transportation.PUBLIC_TRANSIT,
            )
            expected_interval = (
                current["estimatedStayMinutes"]
                + travel_minutes
                + TRANSITION_BUFFER_MINUTES[ScheduleDensity.RELAXED]
            )
            actual_interval = int((scheduled[index + 1] - scheduled[index]).total_seconds() / 60)
            self.assertEqual(expected_interval, actual_interval)

        final_end = scheduled[-1] + timedelta(minutes=places[-1]["estimatedStayMinutes"])
        self.assertEqual(
            int((final_end - scheduled[0]).total_seconds() / 60),
            draft["estimatedTotalMinutes"],
        )

    async def test_casual_talk_and_course_question_preserve_draft_and_memory(self) -> None:
        created = await self.client.post(
            "/api/v1/chat/sessions", json=self._create_body(), headers=self.headers
        )
        created_data = created.json()["data"]
        session_id = created_data["sessionId"]
        original = created_data["courseDraft"]

        casual = await self.client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"message": "안녕! 오늘 기분은 어때?", "expectedDraftVersion": 1},
            headers=self.headers,
        )
        self.assertEqual(200, casual.status_code, casual.text)
        casual_data = casual.json()["data"]
        self.assertFalse(casual_data["changeSummary"]["changed"])
        self.assertEqual(original, casual_data["courseDraft"])

        question = await self.client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"message": "이 코스는 왜 이렇게 구성했어?", "expectedDraftVersion": 1},
            headers=self.headers,
        )
        self.assertEqual(200, question.status_code, question.text)
        question_data = question.json()["data"]
        self.assertFalse(question_data["changeSummary"]["changed"])
        self.assertEqual(original, question_data["courseDraft"])
        self.assertIn("안녕! 오늘 기분은 어때?", self.provider.requests[-1].memory.summary)

        detail = await self.client.get(f"/api/v1/chat/sessions/{session_id}", headers=self.headers)
        self.assertEqual(6, len(detail.json()["data"]["messages"]))

    async def test_prohibited_user_input_is_not_sent_to_ai_or_stored(self) -> None:
        blocked_body = self._create_body()
        blocked_body["initialMessage"] = "씨\u200b발 아무 데나 넣어줘"
        blocked_create = await self.client.post(
            "/api/v1/chat/sessions", json=blocked_body, headers=self.headers
        )
        self.assertEqual(422, blocked_create.status_code, blocked_create.text)
        self.assertEqual("CHAT_INVALID_EDIT_REQUEST", blocked_create.json()["code"])
        self.assertEqual([], self.provider.requests)

        created = await self.client.post(
            "/api/v1/chat/sessions", json=self._create_body(), headers=self.headers
        )
        session_id = created.json()["data"]["sessionId"]
        request_count = len(self.provider.requests)
        blocked_message = await self.client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"message": "이 코스 씨 발", "expectedDraftVersion": 1},
            headers=self.headers,
        )
        self.assertEqual(422, blocked_message.status_code, blocked_message.text)
        self.assertEqual("CHAT_INVALID_EDIT_REQUEST", blocked_message.json()["code"])
        self.assertEqual(request_count, len(self.provider.requests))

        detail = await self.client.get(f"/api/v1/chat/sessions/{session_id}", headers=self.headers)
        self.assertEqual(2, len(detail.json()["data"]["messages"]))

    async def test_internal_response_terms_are_repaired_before_returning(self) -> None:
        provider = LeakyOnceAiProvider()
        self.app.dependency_overrides[get_ai_course_provider] = lambda: provider
        created = await self.client.post(
            "/api/v1/chat/sessions", json=self._create_body(), headers=self.headers
        )
        self.assertEqual(201, created.status_code, created.text)
        assistant = created.json()["data"]["assistantMessage"]["content"]
        self.assertNotIn("DB", assistant)
        self.assertNotIn("ANY", assistant)
        self.assertEqual(2, len(provider.requests))
        self.assertTrue(provider.requests[-1].validation_errors)

    async def test_response_repair_cannot_change_casual_talk_into_course_edit(self) -> None:
        provider = IntentChangingRepairProvider()
        self.app.dependency_overrides[get_ai_course_provider] = lambda: provider
        created = await self.client.post(
            "/api/v1/chat/sessions", json=self._create_body(), headers=self.headers
        )
        original = created.json()["data"]["courseDraft"]

        response = await self.client.post(
            f"/api/v1/chat/sessions/{created.json()['data']['sessionId']}/messages",
            json={"message": "안녕", "expectedDraftVersion": 1},
            headers=self.headers,
        )
        self.assertEqual(200, response.status_code, response.text)
        data = response.json()["data"]
        self.assertFalse(data["changeSummary"]["changed"])
        self.assertEqual(original, data["courseDraft"])
        self.assertEqual(QUALITY_FALLBACK_WARNING, data["assistantMessage"]["content"])

    async def test_discard_returns_the_documented_null_payload(self) -> None:
        created = await self.client.post(
            "/api/v1/chat/sessions", json=self._create_body(), headers=self.headers
        )
        self.assertEqual(201, created.status_code, created.text)
        session_id = created.json()["data"]["sessionId"]

        discarded = await self.client.delete(
            f"/api/v1/chat/sessions/{session_id}", headers=self.headers
        )
        self.assertEqual(200, discarded.status_code, discarded.text)
        discarded_body = discarded.json()
        self.assertEqual(
            {"success", "code", "message", "data", "meta", "timestamp", "traceId"},
            set(discarded_body),
        )
        self.assertEqual("CHAT_SESSION_DISCARDED", discarded_body["code"])
        self.assertIsNone(discarded_body["data"])

    async def test_unknown_ai_place_is_rejected_and_session_is_not_saved(self) -> None:
        invalid_provider = RecordingAiProvider(invalid_content_id=True)
        self.app.dependency_overrides[get_ai_course_provider] = lambda: invalid_provider
        response = await self.client.post(
            "/api/v1/chat/sessions", json=self._create_body(), headers=self.headers
        )
        self.assertEqual(502, response.status_code, response.text)
        self.assertEqual("CHAT_AI_PROVIDER_ERROR", response.json()["code"])
        async with self.sessions() as session:
            count = await session.scalar(select(func.count()).select_from(ChatSession))
        self.assertEqual(0, count)

    async def test_missing_ai_configuration_and_version_conflict_follow_contract(self) -> None:
        self.app.dependency_overrides[get_ai_course_provider] = lambda: None
        unavailable = await self.client.post(
            "/api/v1/chat/sessions", json=self._create_body(), headers=self.headers
        )
        self.assertEqual(503, unavailable.status_code)
        self.assertEqual("CHAT_AI_TEMPORARILY_UNAVAILABLE", unavailable.json()["code"])

        self.app.dependency_overrides[get_ai_course_provider] = lambda: self.provider
        created = await self.client.post(
            "/api/v1/chat/sessions", json=self._create_body(), headers=self.headers
        )
        session_id = created.json()["data"]["sessionId"]
        conflict = await self.client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"message": "다른 곳으로 바꿔줘", "expectedDraftVersion": 99},
            headers=self.headers,
        )
        self.assertEqual(409, conflict.status_code)
        self.assertEqual("CHAT_DRAFT_VERSION_CONFLICT", conflict.json()["code"])

        invalid_edit = await self.client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"message": "", "expectedDraftVersion": 1},
            headers=self.headers,
        )
        self.assertEqual(422, invalid_edit.status_code)
        self.assertEqual("CHAT_INVALID_EDIT_REQUEST", invalid_edit.json()["code"])

        too_long = await self.client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"message": "가" * 1001, "expectedDraftVersion": 1},
            headers=self.headers,
        )
        self.assertEqual(422, too_long.status_code)
        self.assertEqual("CHAT_MESSAGE_TOO_LONG", too_long.json()["code"])

    async def test_edit_passes_bounded_conversation_and_distance_context(self) -> None:
        created = await self.client.post(
            "/api/v1/chat/sessions", json=self._create_body(), headers=self.headers
        )
        session_id = created.json()["data"]["sessionId"]

        first_edit = await self.client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"quickAction": "REGENERATE", "expectedDraftVersion": 1},
            headers=self.headers,
        )
        self.assertEqual(200, first_edit.status_code, first_edit.text)
        version = first_edit.json()["data"]["courseDraft"]["version"]

        second_edit = await self.client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={
                "message": "방금 코스에서 식사 장소만 더 가깝게 바꿔줘.",
                "expectedDraftVersion": version,
            },
            headers=self.headers,
        )
        self.assertEqual(200, second_edit.status_code, second_edit.text)

        latest_request = self.provider.requests[-1]
        self.assertEqual(
            ["USER", "ASSISTANT", "USER", "ASSISTANT"],
            [message.role for message in latest_request.conversation],
        )
        self.assertEqual("방금 코스에서 식사 장소만 더 가깝게 바꿔줘.", latest_request.user_request)
        self.assertTrue(
            all(
                candidate.distance_to_current_course_km is not None
                for candidate in latest_request.candidates
            )
        )
        self.assertTrue(any(candidate.is_current for candidate in latest_request.candidates))
        self.assertGreater(
            len({candidate.category for candidate in latest_request.candidates[:8]}), 1
        )

    async def test_failed_regeneration_is_repaired_once_then_preserves_draft(self) -> None:
        provider = StubbornAiProvider()
        self.app.dependency_overrides[get_ai_course_provider] = lambda: provider
        created = await self.client.post(
            "/api/v1/chat/sessions", json=self._create_body(), headers=self.headers
        )
        created_data = created.json()["data"]
        original = created_data["courseDraft"]

        edited = await self.client.post(
            f"/api/v1/chat/sessions/{created_data['sessionId']}/messages",
            json={"quickAction": "REGENERATE", "expectedDraftVersion": 1},
            headers=self.headers,
        )
        self.assertEqual(200, edited.status_code, edited.text)
        data = edited.json()["data"]
        self.assertFalse(data["changeSummary"]["changed"])
        self.assertEqual(original, data["courseDraft"])
        self.assertEqual(
            ["요청 조건을 안전하게 반영하지 못해 기존 코스를 유지했습니다."],
            data["changeSummary"]["warnings"],
        )
        self.assertEqual(3, len(provider.requests))
        self.assertTrue(provider.requests[-1].validation_errors)


if __name__ == "__main__":
    unittest.main()
