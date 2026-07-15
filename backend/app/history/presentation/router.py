"""Authenticated completed course history routes."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Path, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.domain.entities import AuthenticatedProfile
from app.auth.presentation.dependencies import get_current_profile
from app.common.application.dto import BaseDto, ErrorResponseDto
from app.common.application.idempotency import IdempotencyService
from app.common.domain.enums import District
from app.common.infrastructure.idempotency_repository import IdempotencyRepository
from app.common.presentation.responses import success_response
from app.course.application.dto import CopyCourseRequestDto, DateCourseDto
from app.database import get_database_session
from app.history.application.dto import HistoryCourseSummaryDto
from app.history.application.service import HistoryService
from app.history.infrastructure.repository import HistoryRepository

router = APIRouter(prefix="/profiles/me/date-courses", tags=["History"])

AUTH_ERROR: dict[str, Any] = {"model": ErrorResponseDto, "description": "인증 실패"}
NOT_FOUND_ERROR: dict[str, Any] = {
    "model": ErrorResponseDto,
    "description": "완료 코스를 찾을 수 없습니다.",
}
CONFLICT_ERROR: dict[str, Any] = {
    "model": ErrorResponseDto,
    "description": "이미 활성 코스가 있습니다.",
}


@router.get("", response_model=BaseDto[list[HistoryCourseSummaryDto]], summary="완료 코스 목록")
async def list_history_courses(
    profile: Annotated[AuthenticatedProfile, Depends(get_current_profile)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    year: Annotated[int | None, Query(ge=2000, le=2100)] = None,
    month: Annotated[int | None, Query(ge=1, le=12)] = None,
    district: Annotated[District | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=50)] = 20,
) -> BaseDto[list[HistoryCourseSummaryDto]]:
    service = HistoryService(HistoryRepository(session))
    courses, meta = await service.list_courses(
        profile,
        year=year,
        month=month,
        district=district,
        page=page,
        size=size,
    )
    return success_response(courses, meta=meta)


@router.get(
    "/{courseId}",
    response_model=BaseDto[DateCourseDto],
    summary="완료 코스 상세",
    responses={401: AUTH_ERROR, 403: AUTH_ERROR, 404: NOT_FOUND_ERROR},
)
async def get_history_course(
    profile: Annotated[AuthenticatedProfile, Depends(get_current_profile)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    course_id: Annotated[str, Path(alias="courseId")],
) -> BaseDto[DateCourseDto]:
    return success_response(
        await HistoryService(HistoryRepository(session)).get_detail(profile, course_id)
    )


@router.post(
    "/{courseId}/restart",
    response_model=BaseDto[DateCourseDto],
    status_code=status.HTTP_201_CREATED,
    summary="완료 코스 다시 진행",
    responses={401: AUTH_ERROR, 403: AUTH_ERROR, 404: NOT_FOUND_ERROR, 409: CONFLICT_ERROR},
)
async def restart_history_course(
    body: CopyCourseRequestDto,
    request: Request,
    profile: Annotated[AuthenticatedProfile, Depends(get_current_profile)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    course_id: Annotated[str, Path(alias="courseId")],
    idempotency_key: Annotated[UUID | None, Header(alias="Idempotency-Key")] = None,
) -> BaseDto[DateCourseDto] | JSONResponse:
    service = HistoryService(HistoryRepository(session))
    idempotency = IdempotencyService(IdempotencyRepository(session))

    async def restart() -> BaseDto[DateCourseDto]:
        return success_response(await service.restart(profile, course_id, body))

    return await idempotency.execute(
        scope_key=f"profile:{profile.id}",
        method="POST",
        path=request.url.path,
        key=idempotency_key,
        request_fingerprint=idempotency.fingerprint(body.model_dump(mode="json", by_alias=True)),
        status_code=status.HTTP_201_CREATED,
        response_factory=restart,
    )
