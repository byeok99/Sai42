"""Chat session, AI course draft, revision, confirmation, and discard use cases."""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from math import floor
from time import perf_counter
from typing import NoReturn
from uuid import uuid4

from sqlalchemy.exc import IntegrityError

from app.auth.domain.entities import AuthenticatedProfile
from app.chat.application.dto import (
    ChatMessageDto,
    ChatSessionDto,
    ConfirmChatSessionRequestDto,
    CourseDraftChangeSummaryDto,
    CourseDraftDto,
    CourseDraftPlaceDto,
    CreateChatSessionDto,
    CreateChatSessionRequestDto,
    SendChatMessageDto,
    SendChatMessageRequestDto,
)
from app.chat.application.quality import (
    CoursePlanQualityPolicy,
    haversine_km,
    public_response_violations,
    sanitize_chat_turn,
    sanitize_course_plan,
)
from app.chat.application.travel import estimate_travel_minutes
from app.chat.domain.content_filter import contains_prohibited_language
from app.chat.domain.entities import (
    AiChatTurn,
    AiConversationMemory,
    AiConversationMessage,
    AiCourseContent,
    AiCoursePlan,
    AiCourseProviderError,
    AiCourseProviderUnavailable,
    AiCourseRequest,
    PlaceCandidate,
)
from app.chat.domain.enums import (
    ChatMessageRole,
    ChatSessionStatus,
    ChatTurnIntent,
    CourseEditAction,
)
from app.chat.domain.provider import AiCourseProvider
from app.chat.infrastructure.models import ChatSession
from app.chat.infrastructure.repository import ChatRepository
from app.common.application.errors import BusinessException
from app.common.domain.enums import ActivityType, District, ScheduleDensity, SpaceType
from app.common.domain.time import now_seoul
from app.course.application.dto import (
    CoordinateDto,
    CourseMapDto,
    CoursePlaceSnapshotDto,
    DateCourseDto,
)
from app.course.application.service import DateCourseService
from app.course.infrastructure.models import DateCourse, DateCoursePlace
from app.course.infrastructure.repository import DateCourseRepository
from app.place.domain.constants import PLACE_CATEGORY_BY_CONTENT_TYPE_ID
from app.place.domain.enums import PlaceCategory
from app.place.infrastructure.models import Place
from app.weather.application.dto import WeatherSummaryDto
from app.weather.application.service import WeatherService

QUICK_ACTION_MESSAGES = {
    CourseEditAction.CHANGE_CAFE: "코스의 한 장소를 카페 후보로 바꿔줘.",
    CourseEditAction.ADD_NIGHT_VIEW: "야경을 즐길 수 있는 장소를 추가하거나 교체해줘.",
    CourseEditAction.REDUCE_ROUTE: "장소 수를 유지하면서 이동 동선을 줄여줘.",
    CourseEditAction.INCREASE_INDOOR: "실내 장소 비중을 높여줘.",
    CourseEditAction.REGENERATE: "같은 조건으로 다른 장소 조합을 만들어줘.",
}

TRANSITION_BUFFER_MINUTES = {
    ScheduleDensity.RELAXED: 15,
    ScheduleDensity.NORMAL: 10,
    ScheduleDensity.TIGHT: 5,
}

MAX_CONVERSATION_MESSAGES = 8
MAX_CONVERSATION_CHARACTERS = 4000
logger = logging.getLogger("uvicorn.error")
QUALITY_FALLBACK_WARNING = "요청 조건을 안전하게 반영하지 못해 기존 코스를 유지했습니다."


class ChatService:
    def __init__(
        self,
        repository: ChatRepository,
        course_repository: DateCourseRepository,
        ai_provider: AiCourseProvider | None,
        weather_service: WeatherService,
        *,
        candidate_limit: int,
    ) -> None:
        self.repository = repository
        self.course_repository = course_repository
        self.ai_provider = ai_provider
        self.weather_service = weather_service
        self.candidate_limit = candidate_limit
        self.quality_policy = CoursePlanQualityPolicy()

    async def create_session(
        self,
        profile: AuthenticatedProfile,
        request: CreateChatSessionRequestDto,
    ) -> CreateChatSessionDto:
        started_at = perf_counter()
        if request.initial_message:
            self._validate_user_input(request.initial_message)
        if await self.course_repository.find_active_course(profile.id):
            self._raise_active_course_exists()
        self._validate_start(request.date, request.start_time)
        context_started_at = perf_counter()
        weather, places = await asyncio.gather(
            self._weather(request),
            self.repository.list_recommendable_places(request.district),
        )
        context_elapsed_ms = (perf_counter() - context_started_at) * 1000
        candidates = self._rank_candidates(
            places,
            activities=request.activities,
            current_draft=None,
            action=None,
        )
        if len(candidates) < 2:
            raise BusinessException(
                status_code=422,
                code="CHAT_NO_RECOMMENDABLE_PLACES",
                message="조건에 맞는 추천 가능 공공데이터 장소가 부족합니다.",
            )
        conditions = request.conditions()
        user_request = request.initial_message or "입력한 조건으로 데이트 코스를 만들어줘."
        generation_started_at = perf_counter()
        plan, violations = await self._generate(
            conditions=conditions.model_dump(mode="json", by_alias=True),
            weather=weather.model_dump(mode="json", by_alias=True),
            candidates=candidates,
            user_request=user_request,
            current_draft=None,
            conversation=[],
            action=None,
        )
        generation_elapsed_ms = (perf_counter() - generation_started_at) * 1000
        if violations:
            self._raise_provider_error()
        draft = self._build_draft(
            plan,
            candidates=candidates,
            conditions=conditions,
            weather=weather,
            version=1,
        )
        now = now_seoul()
        memory = self._initial_memory(request.initial_message)
        messages = []
        if request.initial_message:
            messages.append(self._message(ChatMessageRole.USER, request.initial_message, now))
        assistant = self._message(ChatMessageRole.ASSISTANT, plan.assistant_message, now)
        messages.append(assistant)
        session_id = str(uuid4())
        chat_session = ChatSession(
            id=session_id,
            profile_id=profile.id,
            status=ChatSessionStatus.ACTIVE.value,
            conditions_json=self._json(conditions.model_dump(mode="json", by_alias=True)),
            messages_json=self._json(self._messages_payload(messages)),
            memory_json=self._json(memory.model_dump(mode="json", by_alias=True)),
            draft_json=self._json(draft.model_dump(mode="json", by_alias=True)),
            draft_version=1,
            weather_json=self._json(weather.model_dump(mode="json", by_alias=True)),
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
            confirmed_at=None,
            expires_at=(now + timedelta(hours=24)).isoformat(),
        )
        await self.repository.add_session(chat_session)
        await self.repository.commit()
        logger.info(
            "chat_session_create_completed total_ms=%.1f context_ms=%.1f generation_ms=%.1f "
            "candidate_count=%d selected_place_count=%d",
            (perf_counter() - started_at) * 1000,
            context_elapsed_ms,
            generation_elapsed_ms,
            len(candidates),
            len(plan.places),
        )
        return CreateChatSessionDto(
            session_id=session_id,
            status=ChatSessionStatus.ACTIVE,
            assistant_message=assistant,
            course_draft=draft,
        )

    async def get_session(self, profile: AuthenticatedProfile, session_id: str) -> ChatSessionDto:
        chat_session = await self._owned_session(profile.id, session_id)
        return self._session_dto(chat_session)

    async def send_message(
        self,
        profile: AuthenticatedProfile,
        session_id: str,
        request: SendChatMessageRequestDto,
    ) -> SendChatMessageDto:
        started_at = perf_counter()
        self._validate_edit_request(request)
        chat_session = await self._owned_active_session(profile.id, session_id)
        if chat_session.draft_version != request.expected_draft_version:
            self._raise_draft_conflict()
        current = self._required_draft(chat_session)
        memory = self._memory(chat_session)
        conditions = current.conditions
        context_started_at = perf_counter()
        places = await self.repository.list_recommendable_places(conditions.district)
        candidates = self._rank_candidates(
            places,
            activities=conditions.activities,
            current_draft=current,
            action=request.quick_action,
        )
        context_elapsed_ms = (perf_counter() - context_started_at) * 1000
        user_content = (
            request.message
            if request.message is not None
            else QUICK_ACTION_MESSAGES[request.quick_action]
        )
        generation_started_at = perf_counter()
        turn, violations = await self._generate_turn(
            conditions=conditions.model_dump(mode="json", by_alias=True),
            weather=(
                current.weather.model_dump(mode="json", by_alias=True) if current.weather else None
            ),
            candidates=candidates,
            user_request=user_content,
            current_draft=current.model_dump(mode="json", by_alias=True),
            conversation=self._conversation_context(self._messages(chat_session)),
            memory=memory,
            action=request.quick_action,
        )
        generation_elapsed_ms = (perf_counter() - generation_started_at) * 1000
        if violations:
            proposed = current
            changed = False
            assistant_content = QUALITY_FALLBACK_WARNING
            warnings = [QUALITY_FALLBACK_WARNING]
            updated_memory = self._normalize_memory(memory, user_content)
        elif turn.intent == ChatTurnIntent.COURSE_EDIT:
            course = turn.proposed_course
            if course is None:
                self._raise_provider_error()
            proposed = self._build_draft(
                course,
                candidates=candidates,
                conditions=conditions,
                weather=(
                    WeatherSummaryDto.model_validate(current.weather) if current.weather else None
                ),
                version=current.version + 1,
                draft_id=current.draft_id,
            )
            changed = self._draft_changed(current, proposed)
            if not changed:
                proposed = current
            assistant_content = turn.assistant_message
            warnings = turn.warnings
            updated_memory = self._normalize_memory(turn.memory, user_content)
        else:
            proposed = current
            changed = False
            assistant_content = turn.assistant_message
            warnings = turn.warnings
            updated_memory = self._normalize_memory(turn.memory, user_content)
        now = now_seoul()
        user_message = self._message(ChatMessageRole.USER, user_content, now)
        assistant_message = self._message(ChatMessageRole.ASSISTANT, assistant_content, now)
        messages = self._messages(chat_session)
        messages.extend([user_message, assistant_message])
        chat_session.messages_json = self._json(self._messages_payload(messages))
        chat_session.memory_json = self._json(updated_memory.model_dump(mode="json", by_alias=True))
        chat_session.updated_at = now.isoformat()
        if changed:
            chat_session.draft_version = proposed.version
            chat_session.draft_json = self._json(proposed.model_dump(mode="json", by_alias=True))
        await self.repository.commit()
        logger.info(
            "chat_message_completed total_ms=%.1f context_ms=%.1f generation_ms=%.1f "
            "candidate_count=%d intent=%s changed=%s fallback=%s",
            (perf_counter() - started_at) * 1000,
            context_elapsed_ms,
            generation_elapsed_ms,
            len(candidates),
            turn.intent.value,
            changed,
            bool(violations),
        )
        return SendChatMessageDto(
            user_message=user_message,
            assistant_message=assistant_message,
            change_summary=CourseDraftChangeSummaryDto(
                changed=changed,
                warnings=warnings,
            ),
            course_draft=proposed,
        )

    async def confirm(
        self,
        profile: AuthenticatedProfile,
        session_id: str,
        request: ConfirmChatSessionRequestDto,
    ) -> DateCourseDto:
        chat_session = await self._owned_active_session(profile.id, session_id)
        draft = self._required_draft(chat_session)
        if draft.draft_id != request.draft_id or draft.version != request.expected_version:
            self._raise_draft_conflict()
        if not 2 <= len(draft.places) <= 4:
            self._raise_draft_conflict()
        if await self.course_repository.find_active_course(profile.id):
            self._raise_active_course_exists()

        content_ids = {item.place.content_id for item in draft.places if item.place.content_id}
        stored_places = await self.repository.find_places(content_ids)
        stored_by_id = {place.content_id: place for place in stored_places}
        if len(stored_by_id) != len(draft.places):
            self._raise_draft_conflict()

        now = now_seoul()
        course_id = str(uuid4())
        conditions = draft.conditions
        course = DateCourse(
            id=course_id,
            profile_id=profile.id,
            chat_session_id=chat_session.id,
            status="ACTIVE",
            source_type="AI_CHAT",
            source_course_id=None,
            title=draft.title,
            date=conditions.date.isoformat(),
            start_time=conditions.start_time.strftime("%H:%M"),
            time_slot=conditions.time_slot.value,
            main_district=conditions.district.value,
            space_type=conditions.space_type.value,
            moods_json=self._json([value.value for value in conditions.moods]),
            activities_json=self._json([value.value for value in conditions.activities]),
            schedule_density=conditions.schedule_density.value,
            transportation=(conditions.transportation.value if conditions.transportation else None),
            overall_comment=draft.overall_comment,
            tags_json=self._json(draft.tags),
            weather_json=(
                self._json(draft.weather.model_dump(mode="json", by_alias=True))
                if draft.weather
                else None
            ),
            current_order_no=1,
            completion_comment=None,
            started_at=None,
            completed_at=None,
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
        )
        course_places = [
            self._course_place(course_id, draft_place, stored_by_id, now)
            for draft_place in draft.places
        ]
        chat_session.status = ChatSessionStatus.CONFIRMED.value
        chat_session.confirmed_at = now.isoformat()
        chat_session.updated_at = now.isoformat()
        try:
            await self.course_repository.add_course(course, course_places)
            await self.repository.commit()
        except IntegrityError:
            await self.repository.rollback()
            self._raise_active_course_exists()
        return await DateCourseService(self.course_repository).render_course(course)

    async def discard(self, profile: AuthenticatedProfile, session_id: str) -> None:
        chat_session = await self._owned_active_session(profile.id, session_id)
        chat_session.status = ChatSessionStatus.DISCARDED.value
        chat_session.updated_at = now_seoul().isoformat()
        await self.repository.commit()

    async def _weather(self, request: CreateChatSessionRequestDto) -> WeatherSummaryDto:
        today = now_seoul().date()
        if request.date > today + timedelta(days=3):
            return WeatherService.unavailable(request.date, request.district, request.time_slot)
        return await self.weather_service.get_weather(
            target_date=request.date,
            district=request.district,
            time_slot=request.time_slot,
        )

    async def _generate(
        self,
        *,
        conditions: dict[str, object],
        weather: dict[str, object] | None,
        candidates: list[PlaceCandidate],
        user_request: str,
        current_draft: dict[str, object] | None,
        conversation: list[AiConversationMessage],
        action: CourseEditAction | None,
    ) -> tuple[AiCoursePlan, list[str]]:
        from app.course.application.dto import CourseConditionDto

        typed_conditions = CourseConditionDto.model_validate(conditions)
        typed_current = (
            CourseDraftDto.model_validate(current_draft) if current_draft is not None else None
        )
        plan = sanitize_course_plan(
            await self._request_plan(
                conditions=conditions,
                weather=weather,
                candidates=candidates,
                user_request=user_request,
                current_draft=current_draft,
                conversation=conversation,
                action=action,
                validation_errors=[],
            )
        )
        violations = self._plan_violations(
            plan,
            conditions=typed_conditions,
            candidates=candidates,
            current_draft=typed_current,
            action=action,
        )
        if not violations:
            return plan, []

        logger.info("chat_plan_repair_started violation_count=%d", len(violations))
        repaired = sanitize_course_plan(
            await self._request_plan(
                conditions=conditions,
                weather=weather,
                candidates=candidates,
                user_request=user_request,
                current_draft=current_draft,
                conversation=conversation,
                action=action,
                validation_errors=violations,
            )
        )
        remaining = self._plan_violations(
            repaired,
            conditions=typed_conditions,
            candidates=candidates,
            current_draft=typed_current,
            action=action,
        )
        logger.info(
            "chat_plan_repair_completed remaining_violation_count=%d",
            len(remaining),
        )
        return repaired, remaining

    async def _generate_turn(
        self,
        *,
        conditions: dict[str, object],
        weather: dict[str, object] | None,
        candidates: list[PlaceCandidate],
        user_request: str,
        current_draft: dict[str, object],
        conversation: list[AiConversationMessage],
        memory: AiConversationMemory,
        action: CourseEditAction | None,
    ) -> tuple[AiChatTurn, list[str]]:
        from app.course.application.dto import CourseConditionDto

        typed_conditions = CourseConditionDto.model_validate(conditions)
        typed_current = CourseDraftDto.model_validate(current_draft)
        turn = self._normalize_provider_turn(
            sanitize_chat_turn(
                await self._request_turn(
                    conditions=conditions,
                    weather=weather,
                    candidates=candidates,
                    user_request=user_request,
                    current_draft=current_draft,
                    conversation=conversation,
                    memory=memory,
                    action=action,
                    validation_errors=[],
                )
            ),
            candidates=candidates,
            current_draft=typed_current,
            current_memory=memory,
        )
        violations = self._turn_violations(
            turn,
            conditions=typed_conditions,
            candidates=candidates,
            current_draft=typed_current,
            current_memory=memory,
            action=action,
        )
        if not violations:
            return turn, []

        logger.info(
            "chat_turn_repair_started intent=%s violation_count=%d",
            turn.intent.value,
            len(violations),
        )
        repaired = self._normalize_provider_turn(
            sanitize_chat_turn(
                await self._request_turn(
                    conditions=conditions,
                    weather=weather,
                    candidates=candidates,
                    user_request=user_request,
                    current_draft=current_draft,
                    conversation=conversation,
                    memory=memory,
                    action=action,
                    validation_errors=violations,
                )
            ),
            candidates=candidates,
            current_draft=typed_current,
            current_memory=memory,
        )
        remaining = self._turn_violations(
            repaired,
            conditions=typed_conditions,
            candidates=candidates,
            current_draft=typed_current,
            current_memory=memory,
            action=action,
            expected_intent=turn.intent,
        )
        logger.info(
            "chat_turn_repair_completed intent=%s remaining_violation_count=%d",
            turn.intent.value,
            len(remaining),
        )
        return repaired, remaining

    async def _request_plan(
        self,
        *,
        conditions: dict[str, object],
        weather: dict[str, object] | None,
        candidates: list[PlaceCandidate],
        user_request: str,
        current_draft: dict[str, object] | None,
        conversation: list[AiConversationMessage],
        action: CourseEditAction | None,
        validation_errors: list[str],
    ) -> AiCoursePlan:
        if self.ai_provider is None:
            raise BusinessException(
                status_code=503,
                code="CHAT_AI_TEMPORARILY_UNAVAILABLE",
                message="AI 코스 생성 설정을 사용할 수 없습니다.",
            )
        try:
            return await self.ai_provider.generate(
                AiCourseRequest(
                    conditions=conditions,
                    weather=weather,
                    candidates=candidates,
                    user_request=user_request,
                    current_draft=current_draft,
                    conversation=conversation,
                    edit_action=action.value if action else None,
                    validation_errors=validation_errors,
                )
            )
        except AiCourseProviderUnavailable:
            raise BusinessException(
                status_code=503,
                code="CHAT_AI_TEMPORARILY_UNAVAILABLE",
                message="AI 코스 생성 서비스를 잠시 사용할 수 없습니다.",
            ) from None
        except AiCourseProviderError:
            self._raise_provider_error()

    async def _request_turn(
        self,
        *,
        conditions: dict[str, object],
        weather: dict[str, object] | None,
        candidates: list[PlaceCandidate],
        user_request: str,
        current_draft: dict[str, object],
        conversation: list[AiConversationMessage],
        memory: AiConversationMemory,
        action: CourseEditAction | None,
        validation_errors: list[str],
    ) -> AiChatTurn:
        if self.ai_provider is None:
            raise BusinessException(
                status_code=503,
                code="CHAT_AI_TEMPORARILY_UNAVAILABLE",
                message="AI 코스 생성 설정을 사용할 수 없습니다.",
            )
        try:
            return await self.ai_provider.respond(
                AiCourseRequest(
                    conditions=conditions,
                    weather=weather,
                    candidates=candidates,
                    user_request=user_request,
                    current_draft=current_draft,
                    conversation=conversation,
                    memory=memory,
                    edit_action=action.value if action else None,
                    validation_errors=validation_errors,
                )
            )
        except AiCourseProviderUnavailable:
            raise BusinessException(
                status_code=503,
                code="CHAT_AI_TEMPORARILY_UNAVAILABLE",
                message="AI 코스 생성 서비스를 잠시 사용할 수 없습니다.",
            ) from None
        except AiCourseProviderError:
            self._raise_provider_error()

    def _plan_violations(
        self,
        plan: AiCourseContent,
        *,
        conditions: object,
        candidates: list[PlaceCandidate],
        current_draft: CourseDraftDto | None,
        action: CourseEditAction | None,
    ) -> list[str]:
        violations = self.quality_policy.violations(
            plan,
            conditions=conditions,
            candidates=candidates,
            current_draft=current_draft,
            action=action,
        )
        visible_texts = self._course_visible_texts(plan)
        if isinstance(plan, AiCoursePlan):
            visible_texts.extend([plan.assistant_message, *plan.warnings])
        violations.extend(public_response_violations(visible_texts))
        return violations

    def _turn_violations(
        self,
        turn: AiChatTurn,
        *,
        conditions: object,
        candidates: list[PlaceCandidate],
        current_draft: CourseDraftDto,
        current_memory: AiConversationMemory,
        action: CourseEditAction | None,
        expected_intent: ChatTurnIntent | None = None,
    ) -> list[str]:
        violations: list[str] = []
        if expected_intent is not None and turn.intent != expected_intent:
            violations.append("응답을 고칠 때 직전에 분류한 대화 의도를 변경하지 마세요.")
        if action is not None and turn.intent != ChatTurnIntent.COURSE_EDIT:
            violations.append("빠른 수정 요청은 COURSE_EDIT으로 분류하고 수정 코스를 반환하세요.")
        if turn.proposed_course is not None:
            violations.extend(
                self.quality_policy.violations(
                    turn.proposed_course,
                    conditions=conditions,
                    candidates=candidates,
                    current_draft=current_draft,
                    action=action,
                )
            )

        visible_texts = [turn.assistant_message, *turn.warnings]
        if turn.proposed_course is not None:
            visible_texts.extend(self._course_visible_texts(turn.proposed_course))
        violations.extend(public_response_violations(visible_texts))

        allowed_ids = {candidate.content_id for candidate in candidates}
        allowed_ids.update(
            place.place.content_id
            for place in current_draft.places
            if place.place.content_id is not None
        )
        remembered_ids = {
            *turn.memory.must_keep_content_ids,
            *turn.memory.excluded_content_ids,
        }
        if not remembered_ids.issubset(allowed_ids):
            violations.append("memory에는 입력으로 제공된 실제 장소 ID만 기록하세요.")
        if set(turn.memory.must_keep_content_ids) & set(turn.memory.excluded_content_ids):
            violations.append("같은 장소를 유지 목록과 제외 목록에 동시에 기록하지 마세요.")
        if current_memory.summary and not turn.memory.summary:
            violations.append("기존 memory의 대화 요약을 유지하면서 최신 요청을 반영하세요.")
        return violations

    @staticmethod
    def _normalize_provider_turn(
        turn: AiChatTurn,
        *,
        candidates: list[PlaceCandidate],
        current_draft: CourseDraftDto,
        current_memory: AiConversationMemory,
    ) -> AiChatTurn:
        """Repair bounded memory bookkeeping locally instead of spending another LLM call."""

        allowed_ids = {candidate.content_id for candidate in candidates}
        allowed_ids.update(
            place.place.content_id
            for place in current_draft.places
            if place.place.content_id is not None
        )

        def unique_allowed(values: list[str]) -> list[str]:
            return list(
                dict.fromkeys(
                    value.strip()
                    for value in values
                    if value.strip() and value.strip() in allowed_ids
                )
            )

        must_keep_ids = unique_allowed(turn.memory.must_keep_content_ids)
        must_keep_id_set = set(must_keep_ids)
        excluded_ids = [
            content_id
            for content_id in unique_allowed(turn.memory.excluded_content_ids)
            if content_id not in must_keep_id_set
        ]
        summary = turn.memory.summary.strip() or current_memory.summary.strip()
        normalized_memory = turn.memory.model_copy(
            update={
                "summary": summary,
                "must_keep_content_ids": must_keep_ids,
                "excluded_content_ids": excluded_ids,
            }
        )
        return turn.model_copy(update={"memory": normalized_memory})

    @staticmethod
    def _course_visible_texts(course: AiCourseContent) -> list[str]:
        return [
            course.title,
            course.overall_comment,
            *course.tags,
            *(place.sweet_comment for place in course.places),
        ]

    def _build_draft(
        self,
        plan: AiCourseContent,
        *,
        candidates: list[PlaceCandidate],
        conditions: object,
        weather: WeatherSummaryDto | None,
        version: int,
        draft_id: str | None = None,
    ) -> CourseDraftDto:
        from app.course.application.dto import CourseConditionDto

        typed_conditions = CourseConditionDto.model_validate(conditions)
        candidate_by_id = {candidate.content_id: candidate for candidate in candidates}
        selected_ids = [item.content_id for item in plan.places]
        if len(selected_ids) != len(set(selected_ids)) or any(
            content_id not in candidate_by_id for content_id in selected_ids
        ):
            raise BusinessException(
                status_code=502,
                code="CHAT_AI_PROVIDER_ERROR",
                message="AI가 확인할 수 없는 장소를 반환했습니다.",
            )
        start = datetime.combine(
            typed_conditions.date,
            typed_conditions.start_time,
            tzinfo=now_seoul().tzinfo,
        )
        cursor = start
        transition_buffer = TRANSITION_BUFFER_MINUTES[typed_conditions.schedule_density]
        draft_places = []
        for index, ai_place in enumerate(plan.places):
            candidate = candidate_by_id[ai_place.content_id]
            draft_places.append(
                CourseDraftPlaceDto(
                    course_place_id=str(uuid4()),
                    order=index + 1,
                    scheduled_at=cursor,
                    estimated_stay_minutes=ai_place.estimated_stay_minutes,
                    place=CoursePlaceSnapshotDto(
                        content_id=candidate.content_id,
                        name=candidate.title,
                        category=PlaceCategory(candidate.category),
                        district=District(candidate.district) if candidate.district else None,
                        address=candidate.address,
                        address_detail=candidate.address_detail or None,
                        latitude=candidate.latitude,
                        longitude=candidate.longitude,
                        image_url=candidate.image_url,
                        indoor_outdoor=SpaceType(ai_place.space_type),
                    ),
                    sweet_comment=ai_place.sweet_comment,
                )
            )
            visit_end = cursor + timedelta(minutes=ai_place.estimated_stay_minutes)
            if index < len(plan.places) - 1:
                next_candidate = candidate_by_id[plan.places[index + 1].content_id]
                travel_minutes = estimate_travel_minutes(
                    (candidate.latitude, candidate.longitude),
                    (next_candidate.latitude, next_candidate.longitude),
                    typed_conditions.transportation,
                )
                cursor = visit_end + timedelta(minutes=travel_minutes + transition_buffer)
        last_end = draft_places[-1].scheduled_at + timedelta(
            minutes=draft_places[-1].estimated_stay_minutes
        )
        coordinates = [
            CoordinateDto(latitude=item.place.latitude, longitude=item.place.longitude)
            for item in draft_places
            if item.place.latitude is not None and item.place.longitude is not None
        ]
        return CourseDraftDto(
            draft_id=draft_id or str(uuid4()),
            version=version,
            title=plan.title,
            date=typed_conditions.date,
            time_slot=typed_conditions.time_slot,
            overall_comment=plan.overall_comment,
            estimated_total_minutes=floor((last_end - start).total_seconds() / 60),
            conditions=typed_conditions,
            tags=[tag if tag.startswith("#") else f"#{tag}" for tag in plan.tags],
            weather=weather,
            places=draft_places,
            map=CourseMapDto(
                center_latitude=(
                    sum(item.latitude for item in coordinates) / len(coordinates)
                    if coordinates
                    else None
                ),
                center_longitude=(
                    sum(item.longitude for item in coordinates) / len(coordinates)
                    if coordinates
                    else None
                ),
                polyline=coordinates,
            ),
        )

    def _rank_candidates(
        self,
        places: list[Place],
        *,
        activities: list[ActivityType],
        current_draft: CourseDraftDto | None,
        action: CourseEditAction | None,
    ) -> list[PlaceCandidate]:
        current_ids = (
            {
                item.place.content_id
                for item in current_draft.places
                if item.place.content_id is not None
            }
            if current_draft
            else set()
        )
        current_coordinates = (
            [
                (item.place.latitude, item.place.longitude)
                for item in current_draft.places
                if item.place.latitude is not None and item.place.longitude is not None
            ]
            if current_draft
            else []
        )
        requested_activities = {item.value for item in activities}

        def distance_to_current(place: Place) -> float | None:
            if not current_coordinates:
                return None
            return min(
                haversine_km(place.latitude, place.longitude, latitude, longitude)
                for latitude, longitude in current_coordinates
            )

        def score(place: Place) -> tuple[int, str]:
            stored_activities = set(self._list_json(place.activities_json))
            value = 10 * len(stored_activities & requested_activities)
            value += 2 if place.image_url else 0
            value += 30 if place.content_id in current_ids else 0
            distance = distance_to_current(place)
            if distance is not None:
                distance_weight = 20 if action == CourseEditAction.REDUCE_ROUTE else 2
                value -= round(distance * distance_weight)
            title = place.title.casefold()
            if action == CourseEditAction.CHANGE_CAFE and any(
                keyword in title for keyword in ("카페", "커피", "coffee", "디저트", "베이커리")
            ):
                value += 40
            if action == CourseEditAction.ADD_NIGHT_VIEW and any(
                keyword in title for keyword in ("야경", "전망", "공원", "대교", "엑스포", "산")
            ):
                value += 30
            if action == CourseEditAction.INCREASE_INDOOR and place.content_type_id in {
                14,
                32,
                38,
                39,
            }:
                value += 25
            if action == CourseEditAction.REGENERATE and place.content_id in current_ids:
                value -= 50
            return (-value, place.content_id)

        ranked = sorted(places, key=score)
        selected: list[Place] = []
        selected_ids: set[str] = set()

        def add(place: Place | None) -> None:
            if (
                place is not None
                and place.content_id not in selected_ids
                and len(selected) < self.candidate_limit
            ):
                selected.append(place)
                selected_ids.add(place.content_id)

        for activity in activities:
            add(
                next(
                    (
                        place
                        for place in ranked
                        if activity.value in self._list_json(place.activities_json)
                    ),
                    None,
                )
            )
        if action != CourseEditAction.REGENERATE:
            for place in ranked:
                if place.content_id in current_ids:
                    add(place)
        for category in dict.fromkeys(
            PLACE_CATEGORY_BY_CONTENT_TYPE_ID[place.content_type_id] for place in ranked
        ):
            add(
                next(
                    (
                        place
                        for place in ranked
                        if PLACE_CATEGORY_BY_CONTENT_TYPE_ID[place.content_type_id] == category
                    ),
                    None,
                )
            )
        for place in ranked:
            add(place)

        return [
            self._candidate(
                place,
                requested_activities=requested_activities,
                current_ids=current_ids,
                distance_to_current=distance_to_current(place),
            )
            for place in selected
        ]

    @staticmethod
    def _candidate(
        place: Place,
        *,
        requested_activities: set[str],
        current_ids: set[str],
        distance_to_current: float | None,
    ) -> PlaceCandidate:
        activities = ChatService._list_json(place.activities_json)
        return PlaceCandidate(
            content_id=place.content_id,
            title=place.title,
            category=PLACE_CATEGORY_BY_CONTENT_TYPE_ID[place.content_type_id],
            address=place.address,
            address_detail=place.address_detail,
            district=place.district,
            latitude=place.latitude,
            longitude=place.longitude,
            image_url=place.image_url or None,
            activities=activities,
            requested_activity_matches=sorted(requested_activities & set(activities)),
            is_current=place.content_id in current_ids,
            distance_to_current_course_km=(
                round(distance_to_current, 3) if distance_to_current is not None else None
            ),
        )

    @staticmethod
    def _course_place(
        course_id: str,
        draft_place: CourseDraftPlaceDto,
        stored_by_id: dict[str, Place],
        now: datetime,
    ) -> DateCoursePlace:
        content_id = draft_place.place.content_id
        place = stored_by_id[content_id]
        return DateCoursePlace(
            id=draft_place.course_place_id,
            date_course_id=course_id,
            content_id=content_id,
            order_no=draft_place.order,
            scheduled_at=draft_place.scheduled_at.isoformat(),
            estimated_stay_minutes=draft_place.estimated_stay_minutes,
            sweet_comment=draft_place.sweet_comment,
            hearted=0,
            hearted_at=None,
            completed_at=None,
            title_snapshot=place.title,
            address_snapshot=place.address,
            address_detail_snapshot=place.address_detail or None,
            longitude_snapshot=place.longitude,
            latitude_snapshot=place.latitude,
            content_type_id_snapshot=place.content_type_id,
            district_snapshot=place.district,
            space_type_snapshot=draft_place.place.indoor_outdoor.value,
            image_url_snapshot=place.image_url or None,
            created_at=now.isoformat(),
        )

    async def _owned_session(self, profile_id: str, session_id: str) -> ChatSession:
        chat_session = await self.repository.find_session(session_id)
        if chat_session is None:
            raise BusinessException(
                status_code=404,
                code="CHAT_SESSION_NOT_FOUND",
                message="채팅 세션을 찾을 수 없습니다.",
            )
        if chat_session.profile_id != profile_id:
            raise BusinessException(
                status_code=403,
                code="CHAT_SESSION_FORBIDDEN",
                message="본인의 채팅 세션만 조회할 수 있습니다.",
            )
        return chat_session

    async def _owned_active_session(self, profile_id: str, session_id: str) -> ChatSession:
        chat_session = await self._owned_session(profile_id, session_id)
        if chat_session.status == ChatSessionStatus.CONFIRMED.value:
            raise BusinessException(
                status_code=409,
                code="CHAT_SESSION_ALREADY_CONFIRMED",
                message="이미 확정된 채팅 세션입니다.",
            )
        if chat_session.status != ChatSessionStatus.ACTIVE.value:
            raise BusinessException(
                status_code=404,
                code="CHAT_SESSION_NOT_FOUND",
                message="사용 가능한 채팅 세션이 아닙니다.",
            )
        return chat_session

    @staticmethod
    def _required_draft(chat_session: ChatSession) -> CourseDraftDto:
        if chat_session.draft_json is None:
            raise BusinessException(
                status_code=409,
                code="CHAT_DRAFT_VERSION_CONFLICT",
                message="현재 코스 초안을 확인할 수 없습니다.",
            )
        return CourseDraftDto.model_validate(json.loads(chat_session.draft_json))

    @staticmethod
    def _session_dto(chat_session: ChatSession) -> ChatSessionDto:
        from app.course.application.dto import CourseConditionDto

        return ChatSessionDto(
            session_id=chat_session.id,
            status=ChatSessionStatus(chat_session.status),
            conditions=CourseConditionDto.model_validate(json.loads(chat_session.conditions_json)),
            messages=ChatService._messages(chat_session),
            course_draft=(
                CourseDraftDto.model_validate(json.loads(chat_session.draft_json))
                if chat_session.draft_json
                else None
            ),
        )

    @staticmethod
    def _messages(chat_session: ChatSession) -> list[ChatMessageDto]:
        return [
            ChatMessageDto.model_validate(item) for item in json.loads(chat_session.messages_json)
        ]

    @staticmethod
    def _memory(chat_session: ChatSession) -> AiConversationMemory:
        try:
            return AiConversationMemory.model_validate(json.loads(chat_session.memory_json))
        except (TypeError, ValueError):
            return AiConversationMemory()

    @staticmethod
    def _initial_memory(initial_message: str | None) -> AiConversationMemory:
        if initial_message is None:
            return AiConversationMemory()
        return AiConversationMemory(
            summary=f"사용자의 최초 요청: {initial_message}",
            preference_notes=[initial_message[:160]],
        )

    @staticmethod
    def _normalize_memory(
        memory: AiConversationMemory,
        latest_user_message: str | None = None,
    ) -> AiConversationMemory:
        def unique(values: list[str]) -> list[str]:
            return list(dict.fromkeys(value.strip() for value in values if value.strip()))

        summary = memory.summary.strip()
        if latest_user_message and latest_user_message not in summary:
            summary = f"{summary}\n최근 사용자 발화: {latest_user_message}".strip()[-1500:]
        return memory.model_copy(
            update={
                "summary": summary,
                "preference_notes": unique(memory.preference_notes),
                "must_keep_content_ids": unique(memory.must_keep_content_ids),
                "excluded_content_ids": unique(memory.excluded_content_ids),
                "pending_clarification": (
                    memory.pending_clarification.strip() if memory.pending_clarification else None
                ),
            }
        )

    @staticmethod
    def _message(role: ChatMessageRole, content: str, created_at: datetime) -> ChatMessageDto:
        return ChatMessageDto(
            message_id=str(uuid4()),
            role=role,
            content=content,
            created_at=created_at,
        )

    @staticmethod
    def _messages_payload(messages: list[ChatMessageDto]) -> list[dict[str, object]]:
        return [message.model_dump(mode="json", by_alias=True) for message in messages]

    @staticmethod
    def _conversation_context(messages: list[ChatMessageDto]) -> list[AiConversationMessage]:
        selected: list[AiConversationMessage] = []
        remaining_characters = MAX_CONVERSATION_CHARACTERS
        for message in reversed(messages[-MAX_CONVERSATION_MESSAGES:]):
            if remaining_characters <= 0:
                break
            content = message.content[:remaining_characters]
            if not content:
                continue
            selected.append(
                AiConversationMessage(
                    role=message.role.value,
                    content=content,
                )
            )
            remaining_characters -= len(content)
        return list(reversed(selected))

    @staticmethod
    def _draft_changed(current: CourseDraftDto, proposed: CourseDraftDto) -> bool:
        current_payload = ChatService._comparable_draft(current)
        proposed_payload = ChatService._comparable_draft(proposed)
        return current_payload != proposed_payload

    @staticmethod
    def _comparable_draft(draft: CourseDraftDto) -> dict[str, object]:
        payload = draft.model_dump(mode="json")
        payload.pop("version", None)
        for place in payload["places"]:
            place.pop("course_place_id", None)
        return payload

    @staticmethod
    def _validate_start(target_date: object, start_time: object) -> None:
        from datetime import date, time

        if not isinstance(target_date, date) or not isinstance(start_time, time):
            return
        if start_time.tzinfo is not None:
            ChatService._raise_invalid_date()
        scheduled = datetime.combine(target_date, start_time, tzinfo=now_seoul().tzinfo)
        if scheduled <= now_seoul():
            ChatService._raise_invalid_date()

    @staticmethod
    def _raise_invalid_date() -> None:
        raise BusinessException(
            status_code=422,
            code="CHAT_INVALID_DATE_CONDITION",
            message="현재 이후의 날짜와 시작 시간을 입력해 주세요.",
        )

    @staticmethod
    def _raise_active_course_exists() -> None:
        raise BusinessException(
            status_code=409,
            code="DATE_COURSE_ACTIVE_ALREADY_EXISTS",
            message="이미 진행 중인 데이트 코스가 있습니다.",
        )

    @staticmethod
    def _raise_draft_conflict() -> None:
        raise BusinessException(
            status_code=409,
            code="CHAT_DRAFT_VERSION_CONFLICT",
            message="코스 초안 버전이 현재 상태와 일치하지 않습니다.",
        )

    @staticmethod
    def _raise_provider_error() -> NoReturn:
        raise BusinessException(
            status_code=502,
            code="CHAT_AI_PROVIDER_ERROR",
            message="AI 코스 생성 응답을 처리할 수 없습니다.",
        )

    @staticmethod
    def _validate_edit_request(request: SendChatMessageRequestDto) -> None:
        has_message = request.message is not None and bool(request.message)
        if has_message:
            ChatService._validate_user_input(request.message or "")
        if has_message == (request.quick_action is not None):
            raise BusinessException(
                status_code=422,
                code="CHAT_INVALID_EDIT_REQUEST",
                message="message와 quickAction 중 정확히 하나를 전달해 주세요.",
            )

    @staticmethod
    def _validate_user_input(message: str) -> None:
        if len(message) > 1000:
            ChatService._raise_message_too_long()
        if contains_prohibited_language(message):
            raise BusinessException(
                status_code=422,
                code="CHAT_INVALID_EDIT_REQUEST",
                message=(
                    "사용할 수 없는 표현이 포함되어 있습니다. 다른 표현으로 다시 요청해 주세요."
                ),
            )

    @staticmethod
    def _raise_message_too_long() -> None:
        raise BusinessException(
            status_code=422,
            code="CHAT_MESSAGE_TOO_LONG",
            message="AI 대화 메시지는 1000자 이하로 입력해 주세요.",
        )

    @staticmethod
    def _list_json(value: str) -> list[str]:
        try:
            parsed = json.loads(value)
        except (TypeError, json.JSONDecodeError):
            return []
        return [str(item) for item in parsed] if isinstance(parsed, list) else []

    @staticmethod
    def _json(value: object) -> str:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
