"""Authenticated AI chat and mutable course-draft HTTP routes."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Path, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.domain.entities import AuthenticatedProfile
from app.auth.presentation.dependencies import get_current_profile
from app.chat.application.dto import (
    ChatSessionDto,
    ConfirmChatSessionRequestDto,
    CreateChatSessionDto,
    CreateChatSessionRequestDto,
    SendChatMessageDto,
    SendChatMessageRequestDto,
)
from app.chat.application.service import ChatService
from app.chat.domain.provider import AiCourseProvider
from app.chat.infrastructure.repository import ChatRepository
from app.chat.presentation.dependencies import get_ai_course_provider
from app.common.application.dto import BaseDto, ErrorResponseDto
from app.common.application.idempotency import IdempotencyService
from app.common.infrastructure.idempotency_repository import IdempotencyRepository
from app.common.presentation.responses import success_response
from app.config import Settings, get_request_settings
from app.course.application.dto import DateCourseDto
from app.course.infrastructure.repository import DateCourseRepository
from app.database import get_database_session
from app.weather.application.service import WeatherService
from app.weather.domain.provider import WeatherProvider
from app.weather.presentation.dependencies import get_weather_provider

router = APIRouter(prefix="/chat/sessions", tags=["Chat"])

AUTH_ERROR: dict[str, Any] = {"model": ErrorResponseDto, "description": "인증 실패"}
NOT_FOUND_ERROR: dict[str, Any] = {
    "model": ErrorResponseDto,
    "description": "채팅 세션을 찾을 수 없습니다.",
}
CONFLICT_ERROR: dict[str, Any] = {
    "model": ErrorResponseDto,
    "description": "세션·초안 버전 또는 현재 코스 상태가 충돌합니다.",
}
PROVIDER_ERROR: dict[str, Any] = {
    "model": ErrorResponseDto,
    "description": "AI 공급자 응답 오류",
}


def _service(
    session: AsyncSession,
    ai_provider: AiCourseProvider | None,
    weather_provider: WeatherProvider | None,
    settings: Settings,
) -> ChatService:
    return ChatService(
        ChatRepository(session),
        DateCourseRepository(session),
        ai_provider,
        WeatherService(weather_provider),
        candidate_limit=settings.openai_candidate_limit,
    )


@router.post(
    "",
    response_model=BaseDto[CreateChatSessionDto],
    status_code=status.HTTP_201_CREATED,
    summary="AI 채팅 세션과 최초 코스 초안 생성",
    responses={401: AUTH_ERROR, 409: CONFLICT_ERROR, 502: PROVIDER_ERROR, 503: PROVIDER_ERROR},
)
async def create_chat_session(
    body: CreateChatSessionRequestDto,
    profile: Annotated[AuthenticatedProfile, Depends(get_current_profile)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    ai_provider: Annotated[AiCourseProvider | None, Depends(get_ai_course_provider)],
    weather_provider: Annotated[WeatherProvider | None, Depends(get_weather_provider)],
    settings: Annotated[Settings, Depends(get_request_settings)],
) -> BaseDto[CreateChatSessionDto]:
    result = await _service(session, ai_provider, weather_provider, settings).create_session(
        profile, body
    )
    return success_response(
        result,
        code="CHAT_SESSION_CREATED",
        message="코스 초안을 만들었습니다.",
    )


@router.get(
    "/{sessionId}",
    response_model=BaseDto[ChatSessionDto],
    summary="AI 채팅 세션과 현재 초안 조회",
    responses={401: AUTH_ERROR, 403: AUTH_ERROR, 404: NOT_FOUND_ERROR},
)
async def get_chat_session(
    profile: Annotated[AuthenticatedProfile, Depends(get_current_profile)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    ai_provider: Annotated[AiCourseProvider | None, Depends(get_ai_course_provider)],
    weather_provider: Annotated[WeatherProvider | None, Depends(get_weather_provider)],
    settings: Annotated[Settings, Depends(get_request_settings)],
    session_id: Annotated[str, Path(alias="sessionId")],
) -> BaseDto[ChatSessionDto]:
    result = await _service(session, ai_provider, weather_provider, settings).get_session(
        profile, session_id
    )
    return success_response(result)


@router.post(
    "/{sessionId}/messages",
    response_model=BaseDto[SendChatMessageDto],
    summary="자연어 또는 빠른 수정으로 코스 초안 변경",
    responses={
        401: AUTH_ERROR,
        403: AUTH_ERROR,
        404: NOT_FOUND_ERROR,
        409: CONFLICT_ERROR,
        502: PROVIDER_ERROR,
        503: PROVIDER_ERROR,
    },
)
async def send_chat_message(
    body: SendChatMessageRequestDto,
    profile: Annotated[AuthenticatedProfile, Depends(get_current_profile)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    ai_provider: Annotated[AiCourseProvider | None, Depends(get_ai_course_provider)],
    weather_provider: Annotated[WeatherProvider | None, Depends(get_weather_provider)],
    settings: Annotated[Settings, Depends(get_request_settings)],
    session_id: Annotated[str, Path(alias="sessionId")],
) -> BaseDto[SendChatMessageDto]:
    result = await _service(session, ai_provider, weather_provider, settings).send_message(
        profile, session_id, body
    )
    return success_response(result, code="CHAT_DRAFT_UPDATED", message="코스 초안을 검토했습니다.")


@router.post(
    "/{sessionId}/confirm",
    response_model=BaseDto[DateCourseDto],
    status_code=status.HTTP_201_CREATED,
    summary="코스 초안 확정",
    responses={401: AUTH_ERROR, 403: AUTH_ERROR, 404: NOT_FOUND_ERROR, 409: CONFLICT_ERROR},
)
async def confirm_chat_session(
    body: ConfirmChatSessionRequestDto,
    request: Request,
    profile: Annotated[AuthenticatedProfile, Depends(get_current_profile)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    ai_provider: Annotated[AiCourseProvider | None, Depends(get_ai_course_provider)],
    weather_provider: Annotated[WeatherProvider | None, Depends(get_weather_provider)],
    settings: Annotated[Settings, Depends(get_request_settings)],
    session_id: Annotated[str, Path(alias="sessionId")],
    idempotency_key: Annotated[UUID | None, Header(alias="Idempotency-Key")] = None,
) -> BaseDto[DateCourseDto] | JSONResponse:
    service = _service(session, ai_provider, weather_provider, settings)
    idempotency = IdempotencyService(IdempotencyRepository(session))

    async def confirm() -> BaseDto[DateCourseDto]:
        course = await service.confirm(profile, session_id, body)
        return success_response(
            course,
            code="CHAT_SESSION_CONFIRMED",
            message="코스를 확정했습니다.",
        )

    return await idempotency.execute(
        scope_key=f"profile:{profile.id}",
        method="POST",
        path=request.url.path,
        key=idempotency_key,
        request_fingerprint=idempotency.fingerprint(body.model_dump(mode="json", by_alias=True)),
        status_code=status.HTTP_201_CREATED,
        response_factory=confirm,
    )


@router.delete(
    "/{sessionId}",
    response_model=BaseDto[None],
    summary="확정 전 AI 코스 초안 폐기",
    responses={401: AUTH_ERROR, 403: AUTH_ERROR, 404: NOT_FOUND_ERROR, 409: CONFLICT_ERROR},
)
async def discard_chat_session(
    profile: Annotated[AuthenticatedProfile, Depends(get_current_profile)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    ai_provider: Annotated[AiCourseProvider | None, Depends(get_ai_course_provider)],
    weather_provider: Annotated[WeatherProvider | None, Depends(get_weather_provider)],
    settings: Annotated[Settings, Depends(get_request_settings)],
    session_id: Annotated[str, Path(alias="sessionId")],
) -> BaseDto[None]:
    await _service(session, ai_provider, weather_provider, settings).discard(profile, session_id)
    return success_response(
        None,
        code="CHAT_SESSION_DISCARDED",
        message="코스 초안을 폐기했습니다.",
    )
