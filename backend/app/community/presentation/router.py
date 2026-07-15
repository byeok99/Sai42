"""Community post, like, and copied-course HTTP routes."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Path, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.domain.entities import AuthenticatedProfile
from app.auth.presentation.dependencies import get_current_profile, get_optional_current_profile
from app.common.application.dto import BaseDto, ErrorResponseDto
from app.common.application.idempotency import IdempotencyService
from app.common.domain.enums import (
    ActivityType,
    District,
    Mood,
    RankingSort,
    ScheduleDensity,
    SpaceType,
    TimeSlot,
)
from app.common.infrastructure.idempotency_repository import IdempotencyRepository
from app.common.presentation.responses import success_response
from app.community.application.dto import (
    CommunityLikeDto,
    CommunityPostDetailDto,
    CommunityPostSummaryDto,
    PublishCommunityPostRequestDto,
    UpdateCommunityPostRequestDto,
)
from app.community.application.service import CommunityService
from app.community.domain.query import CommunityPostCriteria
from app.community.infrastructure.repository import CommunityRepository
from app.course.application.dto import CopyCourseRequestDto, StartCommunityCourseDto
from app.database import get_database_session

router = APIRouter(prefix="/community/posts", tags=["Community"])

AUTH_ERROR: dict[str, Any] = {"model": ErrorResponseDto, "description": "인증 실패"}
NOT_FOUND_ERROR: dict[str, Any] = {
    "model": ErrorResponseDto,
    "description": "게시글 또는 완료 코스를 찾을 수 없습니다.",
}
CONFLICT_ERROR: dict[str, Any] = {
    "model": ErrorResponseDto,
    "description": "게시글 또는 활성 코스 상태가 요청과 충돌합니다.",
}


@router.get("", response_model=BaseDto[list[CommunityPostSummaryDto]], summary="공개 코스 목록")
async def list_community_posts(
    session: Annotated[AsyncSession, Depends(get_database_session)],
    profile: Annotated[AuthenticatedProfile | None, Depends(get_optional_current_profile)],
    sort: Annotated[RankingSort, Query()] = RankingSort.POPULAR,
    district: Annotated[list[District] | None, Query()] = None,
    time_slot: Annotated[list[TimeSlot] | None, Query(alias="timeSlot")] = None,
    space_type: Annotated[list[SpaceType] | None, Query(alias="spaceType")] = None,
    mood: Annotated[list[Mood] | None, Query()] = None,
    activity: Annotated[list[ActivityType] | None, Query()] = None,
    density: Annotated[list[ScheduleDensity] | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=50)] = 20,
) -> BaseDto[list[CommunityPostSummaryDto]]:
    service = CommunityService(CommunityRepository(session))
    posts, meta = await service.list_posts(
        CommunityPostCriteria(
            sort=sort,
            districts=tuple(district or []),
            time_slots=tuple(time_slot or []),
            space_types=tuple(space_type or []),
            moods=tuple(mood or []),
            activities=tuple(activity or []),
            densities=tuple(density or []),
        ),
        profile=profile,
        page=page,
        size=size,
    )
    return success_response(posts, meta=meta)


@router.get(
    "/{postId}",
    response_model=BaseDto[CommunityPostDetailDto],
    summary="공개 코스 상세",
    responses={404: NOT_FOUND_ERROR},
)
async def get_community_post(
    session: Annotated[AsyncSession, Depends(get_database_session)],
    profile: Annotated[AuthenticatedProfile | None, Depends(get_optional_current_profile)],
    post_id: Annotated[str, Path(alias="postId")],
) -> BaseDto[CommunityPostDetailDto]:
    return success_response(
        await CommunityService(CommunityRepository(session)).get_detail(post_id, profile=profile)
    )


@router.post(
    "",
    response_model=BaseDto[CommunityPostDetailDto],
    summary="삭제 게시글 재공개",
    responses={401: AUTH_ERROR, 403: AUTH_ERROR, 404: NOT_FOUND_ERROR, 409: CONFLICT_ERROR},
)
async def republish_community_post(
    body: PublishCommunityPostRequestDto,
    request: Request,
    profile: Annotated[AuthenticatedProfile, Depends(get_current_profile)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    idempotency_key: Annotated[UUID | None, Header(alias="Idempotency-Key")] = None,
) -> BaseDto[CommunityPostDetailDto] | JSONResponse:
    service = CommunityService(CommunityRepository(session))
    idempotency = IdempotencyService(IdempotencyRepository(session))

    async def republish() -> BaseDto[CommunityPostDetailDto]:
        return success_response(await service.republish(profile, body))

    return await idempotency.execute(
        scope_key=f"profile:{profile.id}",
        method="POST",
        path=request.url.path,
        key=idempotency_key,
        request_fingerprint=idempotency.fingerprint(body.model_dump(mode="json", by_alias=True)),
        status_code=status.HTTP_200_OK,
        response_factory=republish,
    )


@router.patch(
    "/{postId}",
    response_model=BaseDto[CommunityPostDetailDto],
    summary="공개 코스 한 줄 코멘트 수정",
    responses={401: AUTH_ERROR, 403: AUTH_ERROR, 404: NOT_FOUND_ERROR, 409: CONFLICT_ERROR},
)
async def update_community_post(
    body: UpdateCommunityPostRequestDto,
    profile: Annotated[AuthenticatedProfile, Depends(get_current_profile)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    post_id: Annotated[str, Path(alias="postId")],
) -> BaseDto[CommunityPostDetailDto]:
    return success_response(
        await CommunityService(CommunityRepository(session)).update(profile, post_id, body)
    )


@router.delete(
    "/{postId}",
    response_model=BaseDto[None],
    summary="공개 코스 삭제",
    responses={401: AUTH_ERROR, 403: AUTH_ERROR, 404: NOT_FOUND_ERROR},
)
async def delete_community_post(
    profile: Annotated[AuthenticatedProfile, Depends(get_current_profile)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    post_id: Annotated[str, Path(alias="postId")],
) -> BaseDto[None]:
    await CommunityService(CommunityRepository(session)).delete(profile, post_id)
    return success_response(None, code="COMMUNITY_POST_DELETED", message="게시글을 삭제했습니다.")


@router.put(
    "/{postId}/like",
    response_model=BaseDto[CommunityLikeDto],
    summary="공개 코스 좋아요",
    responses={401: AUTH_ERROR, 404: NOT_FOUND_ERROR, 409: CONFLICT_ERROR},
)
async def like_community_post(
    profile: Annotated[AuthenticatedProfile, Depends(get_current_profile)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    post_id: Annotated[str, Path(alias="postId")],
) -> BaseDto[CommunityLikeDto]:
    return success_response(
        await CommunityService(CommunityRepository(session)).set_like(profile, post_id, liked=True)
    )


@router.delete(
    "/{postId}/like",
    response_model=BaseDto[CommunityLikeDto],
    summary="공개 코스 좋아요 취소",
    responses={401: AUTH_ERROR, 404: NOT_FOUND_ERROR, 409: CONFLICT_ERROR},
)
async def unlike_community_post(
    profile: Annotated[AuthenticatedProfile, Depends(get_current_profile)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    post_id: Annotated[str, Path(alias="postId")],
) -> BaseDto[CommunityLikeDto]:
    return success_response(
        await CommunityService(CommunityRepository(session)).set_like(profile, post_id, liked=False)
    )


@router.post(
    "/{postId}/start",
    response_model=BaseDto[StartCommunityCourseDto],
    status_code=status.HTTP_201_CREATED,
    summary="공개 코스 진행 시작",
    responses={401: AUTH_ERROR, 404: NOT_FOUND_ERROR, 409: CONFLICT_ERROR},
)
async def start_community_course(
    body: CopyCourseRequestDto,
    request: Request,
    profile: Annotated[AuthenticatedProfile, Depends(get_current_profile)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    post_id: Annotated[str, Path(alias="postId")],
    idempotency_key: Annotated[UUID | None, Header(alias="Idempotency-Key")] = None,
) -> BaseDto[StartCommunityCourseDto] | JSONResponse:
    service = CommunityService(CommunityRepository(session))
    idempotency = IdempotencyService(IdempotencyRepository(session))

    async def start() -> BaseDto[StartCommunityCourseDto]:
        return success_response(await service.start_course(profile, post_id, body))

    return await idempotency.execute(
        scope_key=f"profile:{profile.id}",
        method="POST",
        path=request.url.path,
        key=idempotency_key,
        request_fingerprint=idempotency.fingerprint(body.model_dump(mode="json", by_alias=True)),
        status_code=status.HTTP_201_CREATED,
        response_factory=start,
    )
