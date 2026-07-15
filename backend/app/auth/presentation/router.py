"""Identity HTTP routes."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.application.dto import (
    CreateProfileRequestDto,
    MyProfileDto,
    NicknameSuggestionsDto,
    ProfileCreatedDto,
    ProfileVerifiedDto,
    VerifyProfileRequestDto,
)
from app.auth.application.rate_limiter import AuthRateLimiter
from app.auth.application.service import AuthService
from app.auth.domain.entities import AuthenticatedProfile
from app.auth.infrastructure.repository import AuthRepository
from app.auth.presentation.dependencies import (
    get_auth_rate_limiter,
    get_current_profile,
    request_client_ip,
)
from app.common.application.dto import BaseDto, ErrorResponseDto
from app.common.presentation.responses import success_response
from app.database import get_database_session

router = APIRouter(tags=["Identity"])

UNAUTHORIZED_RESPONSE: dict[str, Any] = {
    "model": ErrorResponseDto,
    "description": "인증 정보가 없거나 올바르지 않습니다.",
}
RATE_LIMIT_RESPONSE: dict[str, Any] = {
    "model": ErrorResponseDto,
    "description": "인증 시도가 허용 범위를 초과했습니다.",
}


@router.get(
    "/auth/nickname-suggestions",
    response_model=BaseDto[NicknameSuggestionsDto],
    summary="닉네임 추천",
    description="SQLite의 추천 가능 공공 장소 이름을 기반으로 미사용 닉네임을 추천합니다.",
)
async def get_nickname_suggestions(
    session: Annotated[AsyncSession, Depends(get_database_session)],
    rate_limiter: Annotated[AuthRateLimiter, Depends(get_auth_rate_limiter)],
    count: Annotated[int, Query(ge=1, le=10)] = 5,
    seed: Annotated[str | None, Query(max_length=30)] = None,
) -> BaseDto[NicknameSuggestionsDto]:
    service = AuthService(AuthRepository(session), rate_limiter)
    return success_response(
        await service.get_nickname_suggestions(count=count, seed=seed),
    )


@router.post(
    "/auth/profiles",
    response_model=BaseDto[ProfileCreatedDto],
    status_code=status.HTTP_201_CREATED,
    summary="익명 프로필 등록",
    responses={
        409: {
            "model": ErrorResponseDto,
            "description": "이미 사용 중인 닉네임입니다.",
        },
        429: RATE_LIMIT_RESPONSE,
    },
)
async def create_profile(
    body: CreateProfileRequestDto,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_database_session)],
    rate_limiter: Annotated[AuthRateLimiter, Depends(get_auth_rate_limiter)],
) -> BaseDto[ProfileCreatedDto]:
    service = AuthService(AuthRepository(session), rate_limiter)
    return success_response(
        await service.create_profile(body, client_ip=request_client_ip(request)),
    )


@router.post(
    "/auth/verify",
    response_model=BaseDto[ProfileVerifiedDto],
    summary="기존 프로필 검증",
    responses={
        401: UNAUTHORIZED_RESPONSE,
        429: RATE_LIMIT_RESPONSE,
    },
)
async def verify_profile(
    body: VerifyProfileRequestDto,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_database_session)],
    rate_limiter: Annotated[AuthRateLimiter, Depends(get_auth_rate_limiter)],
) -> BaseDto[ProfileVerifiedDto]:
    service = AuthService(AuthRepository(session), rate_limiter)
    return success_response(
        await service.verify_profile(body, client_ip=request_client_ip(request)),
    )


@router.get(
    "/profiles/me",
    response_model=BaseDto[MyProfileDto],
    summary="내 프로필 조회",
    responses={
        401: UNAUTHORIZED_RESPONSE,
        429: RATE_LIMIT_RESPONSE,
    },
)
async def get_my_profile(
    current_profile: Annotated[AuthenticatedProfile, Depends(get_current_profile)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    rate_limiter: Annotated[AuthRateLimiter, Depends(get_auth_rate_limiter)],
) -> BaseDto[MyProfileDto]:
    service = AuthService(AuthRepository(session), rate_limiter)
    return success_response(await service.get_my_profile(current_profile))
