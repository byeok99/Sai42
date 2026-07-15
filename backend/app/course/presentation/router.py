"""Authenticated Current DateCourse HTTP routes."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Path, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.domain.entities import AuthenticatedProfile
from app.auth.presentation.dependencies import get_current_profile
from app.common.application.dto import BaseDto, ErrorResponseDto
from app.common.application.idempotency import IdempotencyService
from app.common.infrastructure.idempotency_repository import IdempotencyRepository
from app.common.presentation.responses import success_response
from app.course.application.dto import (
    CompleteDateCourseDto,
    CompleteDateCourseRequestDto,
    CoursePlaceHeartDto,
    DateCourseDto,
    DateCourseProgressDto,
)
from app.course.application.service import DateCourseService
from app.course.infrastructure.repository import DateCourseRepository
from app.database import get_database_session

router = APIRouter(prefix="/date-courses/current", tags=["Current"])

AUTH_ERROR: dict[str, Any] = {"model": ErrorResponseDto, "description": "인증 실패"}
NOT_FOUND_ERROR: dict[str, Any] = {
    "model": ErrorResponseDto,
    "description": "현재 코스 또는 코스 장소를 찾을 수 없습니다.",
}
CONFLICT_ERROR: dict[str, Any] = {
    "model": ErrorResponseDto,
    "description": "코스 진행 상태와 요청이 충돌합니다.",
}


@router.get(
    "",
    response_model=BaseDto[DateCourseDto],
    summary="현재 데이트 코스 조회",
    responses={401: AUTH_ERROR},
)
async def get_current_date_course(
    profile: Annotated[AuthenticatedProfile, Depends(get_current_profile)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> BaseDto[DateCourseDto]:
    course = await DateCourseService(DateCourseRepository(session)).get_current(profile)
    if course is None:
        return success_response(
            None,
            code="DATE_COURSE_CURRENT_EMPTY",
            message="현재 진행 중인 데이트 코스가 없습니다.",
        )
    return success_response(course)


@router.put(
    "/places/{coursePlaceId}/complete",
    response_model=BaseDto[DateCourseProgressDto],
    summary="현재 장소 완료",
    responses={401: AUTH_ERROR, 403: AUTH_ERROR, 404: NOT_FOUND_ERROR, 409: CONFLICT_ERROR},
)
async def complete_current_place(
    profile: Annotated[AuthenticatedProfile, Depends(get_current_profile)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    course_place_id: Annotated[str, Path(alias="coursePlaceId")],
) -> BaseDto[DateCourseProgressDto]:
    service = DateCourseService(DateCourseRepository(session))
    return success_response(await service.complete_place(profile, course_place_id))


@router.put(
    "/places/{coursePlaceId}/heart",
    response_model=BaseDto[CoursePlaceHeartDto],
    summary="현재 장소 하트 등록",
    responses={401: AUTH_ERROR, 403: AUTH_ERROR, 404: NOT_FOUND_ERROR},
)
async def heart_current_place(
    profile: Annotated[AuthenticatedProfile, Depends(get_current_profile)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    course_place_id: Annotated[str, Path(alias="coursePlaceId")],
) -> BaseDto[CoursePlaceHeartDto]:
    service = DateCourseService(DateCourseRepository(session))
    return success_response(await service.set_heart(profile, course_place_id, hearted=True))


@router.delete(
    "/places/{coursePlaceId}/heart",
    response_model=BaseDto[CoursePlaceHeartDto],
    summary="현재 장소 하트 취소",
    responses={401: AUTH_ERROR, 403: AUTH_ERROR, 404: NOT_FOUND_ERROR},
)
async def unheart_current_place(
    profile: Annotated[AuthenticatedProfile, Depends(get_current_profile)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    course_place_id: Annotated[str, Path(alias="coursePlaceId")],
) -> BaseDto[CoursePlaceHeartDto]:
    service = DateCourseService(DateCourseRepository(session))
    return success_response(await service.set_heart(profile, course_place_id, hearted=False))


@router.post(
    "/complete",
    response_model=BaseDto[CompleteDateCourseDto],
    status_code=status.HTTP_200_OK,
    summary="현재 데이트 종료 및 자동 공개",
    responses={401: AUTH_ERROR, 404: NOT_FOUND_ERROR, 409: CONFLICT_ERROR},
)
async def complete_current_date_course(
    body: CompleteDateCourseRequestDto,
    request: Request,
    profile: Annotated[AuthenticatedProfile, Depends(get_current_profile)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    idempotency_key: Annotated[UUID | None, Header(alias="Idempotency-Key")] = None,
) -> BaseDto[CompleteDateCourseDto] | JSONResponse:
    service = DateCourseService(DateCourseRepository(session))
    idempotency = IdempotencyService(IdempotencyRepository(session))

    async def complete() -> BaseDto[CompleteDateCourseDto]:
        return success_response(await service.complete_course(profile, body))

    return await idempotency.execute(
        scope_key=f"profile:{profile.id}",
        method="POST",
        path=request.url.path,
        key=idempotency_key,
        request_fingerprint=idempotency.fingerprint(body.model_dump(mode="json", by_alias=True)),
        status_code=status.HTTP_200_OK,
        response_factory=complete,
    )
