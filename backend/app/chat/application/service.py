"""Chat session, AI course draft, revision, confirmation, and discard use cases."""

import json
from datetime import datetime, timedelta
from math import floor
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
from app.chat.domain.entities import (
    AiCoursePlan,
    AiCourseProviderError,
    AiCourseProviderUnavailable,
    AiCourseRequest,
    PlaceCandidate,
)
from app.chat.domain.enums import ChatMessageRole, ChatSessionStatus, CourseEditAction
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

GAP_MINUTES = {
    ScheduleDensity.RELAXED: 30,
    ScheduleDensity.NORMAL: 20,
    ScheduleDensity.TIGHT: 10,
}


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

    async def create_session(
        self,
        profile: AuthenticatedProfile,
        request: CreateChatSessionRequestDto,
    ) -> CreateChatSessionDto:
        if request.initial_message and len(request.initial_message) > 1000:
            self._raise_message_too_long()
        if await self.course_repository.find_active_course(profile.id):
            self._raise_active_course_exists()
        self._validate_start(request.date, request.start_time)
        weather = await self._weather(request)
        places = await self.repository.list_recommendable_places(request.district)
        candidates = self._rank_candidates(
            places,
            activities=request.activities,
            current_ids=set(),
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
        plan = await self._generate(
            conditions=conditions.model_dump(mode="json", by_alias=True),
            weather=weather.model_dump(mode="json", by_alias=True),
            candidates=candidates,
            user_request=user_request,
            current_draft=None,
        )
        draft = self._build_draft(
            plan,
            candidates=candidates,
            conditions=conditions,
            weather=weather,
            version=1,
        )
        now = now_seoul()
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
        self._validate_edit_request(request)
        chat_session = await self._owned_active_session(profile.id, session_id)
        if chat_session.draft_version != request.expected_draft_version:
            self._raise_draft_conflict()
        current = self._required_draft(chat_session)
        conditions = current.conditions
        current_ids = {item.place.content_id for item in current.places if item.place.content_id}
        places = await self.repository.list_recommendable_places(conditions.district)
        candidates = self._rank_candidates(
            places,
            activities=conditions.activities,
            current_ids=current_ids,
            action=request.quick_action,
        )
        user_content = (
            request.message
            if request.message is not None
            else QUICK_ACTION_MESSAGES[request.quick_action]
        )
        plan = await self._generate(
            conditions=conditions.model_dump(mode="json", by_alias=True),
            weather=(
                current.weather.model_dump(mode="json", by_alias=True) if current.weather else None
            ),
            candidates=candidates,
            user_request=user_content,
            current_draft=current.model_dump(mode="json", by_alias=True),
        )
        proposed = self._build_draft(
            plan,
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
        now = now_seoul()
        user_message = self._message(ChatMessageRole.USER, user_content, now)
        assistant_message = self._message(ChatMessageRole.ASSISTANT, plan.assistant_message, now)
        messages = self._messages(chat_session)
        messages.extend([user_message, assistant_message])
        chat_session.messages_json = self._json(self._messages_payload(messages))
        chat_session.updated_at = now.isoformat()
        if changed:
            chat_session.draft_version = proposed.version
            chat_session.draft_json = self._json(proposed.model_dump(mode="json", by_alias=True))
        await self.repository.commit()
        return SendChatMessageDto(
            user_message=user_message,
            assistant_message=assistant_message,
            change_summary=CourseDraftChangeSummaryDto(
                changed=changed,
                warnings=plan.warnings,
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
                )
            )
        except AiCourseProviderUnavailable:
            raise BusinessException(
                status_code=503,
                code="CHAT_AI_TEMPORARILY_UNAVAILABLE",
                message="AI 코스 생성 서비스를 잠시 사용할 수 없습니다.",
            ) from None
        except AiCourseProviderError:
            raise BusinessException(
                status_code=502,
                code="CHAT_AI_PROVIDER_ERROR",
                message="AI 코스 생성 응답을 처리할 수 없습니다.",
            ) from None

    def _build_draft(
        self,
        plan: AiCoursePlan,
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
                message="AI가 공공데이터 후보에 없는 장소를 반환했습니다.",
            )
        start = datetime.combine(
            typed_conditions.date,
            typed_conditions.start_time,
            tzinfo=now_seoul().tzinfo,
        )
        cursor = start
        gap = GAP_MINUTES[typed_conditions.schedule_density]
        draft_places = []
        for order, ai_place in enumerate(plan.places, start=1):
            candidate = candidate_by_id[ai_place.content_id]
            draft_places.append(
                CourseDraftPlaceDto(
                    course_place_id=str(uuid4()),
                    order=order,
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
            cursor += timedelta(minutes=ai_place.estimated_stay_minutes + gap)
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
        current_ids: set[str],
        action: CourseEditAction | None,
    ) -> list[PlaceCandidate]:
        def score(place: Place) -> tuple[int, str]:
            stored_activities = set(self._list_json(place.activities_json))
            value = 10 * len(stored_activities & {item.value for item in activities})
            value += 2 if place.image_url else 0
            value += 20 if place.content_id in current_ids else 0
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

        ranked = sorted(places, key=score)[: self.candidate_limit]
        return [self._candidate(place) for place in ranked]

    @staticmethod
    def _candidate(place: Place) -> PlaceCandidate:
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
            activities=ChatService._list_json(place.activities_json),
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
    def _validate_edit_request(request: SendChatMessageRequestDto) -> None:
        has_message = request.message is not None and bool(request.message)
        if has_message and len(request.message or "") > 1000:
            ChatService._raise_message_too_long()
        if has_message == (request.quick_action is not None):
            raise BusinessException(
                status_code=422,
                code="CHAT_INVALID_EDIT_REQUEST",
                message="message와 quickAction 중 정확히 하나를 전달해 주세요.",
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
