"""Public Place HTTP routes backed by the stored public dataset."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.domain.entities import AuthenticatedProfile
from app.auth.presentation.dependencies import get_optional_current_profile
from app.common.application.dto import BaseDto, ErrorResponseDto
from app.common.domain.enums import District, SpaceType
from app.common.presentation.responses import success_response
from app.database import get_database_session
from app.place.application.dto import NearbyPlacesDto, PlaceDetailDto, PlaceSummaryDto
from app.place.application.service import PlaceService
from app.place.infrastructure.repository import PlaceRepository

router = APIRouter(prefix="/places", tags=["Place"])

PLACE_RULE_ERROR: dict[str, Any] = {
    "model": ErrorResponseDto,
    "description": "좌표 또는 검색 반경 규칙을 충족하지 않습니다.",
}
OPTIONAL_AUTH_ERROR: dict[str, Any] = {
    "model": ErrorResponseDto,
    "description": "전달한 선택 인증 정보가 올바르지 않습니다.",
}
AUTH_RATE_LIMIT_ERROR: dict[str, Any] = {
    "model": ErrorResponseDto,
    "description": "선택 인증 시도가 허용 범위를 초과했습니다.",
}


@router.get(
    "",
    response_model=BaseDto[list[PlaceSummaryDto]],
    summary="장소 목록 조회",
    description=(
        "SQLite에 적재된 추천 가능 공공 장소를 검색합니다. 반경 검색에는 위도, 경도, "
        "반경을 모두 전달해야 하며 category는 쉼표로 구분합니다."
    ),
    responses={401: OPTIONAL_AUTH_ERROR, 422: PLACE_RULE_ERROR, 429: AUTH_RATE_LIMIT_ERROR},
)
async def search_places(
    session: Annotated[AsyncSession, Depends(get_database_session)],
    _current_profile: Annotated[AuthenticatedProfile | None, Depends(get_optional_current_profile)],
    keyword: Annotated[str | None, Query(max_length=100)] = None,
    district: Annotated[District | None, Query()] = None,
    category: Annotated[str | None, Query(description="쉼표로 구분한 PlaceCategory 목록")] = None,
    space_type: Annotated[SpaceType | None, Query(alias="spaceType")] = None,
    latitude: Annotated[float | None, Query()] = None,
    longitude: Annotated[float | None, Query()] = None,
    radius_km: Annotated[float | None, Query(alias="radiusKm")] = None,
    has_image: Annotated[bool | None, Query(alias="hasImage")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> BaseDto[list[PlaceSummaryDto]]:
    service = PlaceService(PlaceRepository(session))
    places, meta = await service.search(
        keyword=keyword,
        district=district,
        categories=service.parse_categories(category),
        space_type=space_type,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        has_image=has_image,
        page=page,
        size=size,
    )
    return success_response(places, meta=meta)


@router.get(
    "/{contentId}",
    response_model=BaseDto[PlaceDetailDto],
    summary="장소 상세 조회",
    description="TourAPI contentId로 SQLite에 적재된 공공 장소 상세를 조회합니다.",
    responses={
        401: OPTIONAL_AUTH_ERROR,
        404: {"model": ErrorResponseDto, "description": "장소를 찾을 수 없습니다."},
        429: AUTH_RATE_LIMIT_ERROR,
    },
)
async def get_place(
    session: Annotated[AsyncSession, Depends(get_database_session)],
    _current_profile: Annotated[AuthenticatedProfile | None, Depends(get_optional_current_profile)],
    content_id: Annotated[str, Path(alias="contentId", min_length=1, max_length=50)],
) -> BaseDto[PlaceDetailDto]:
    return success_response(await PlaceService(PlaceRepository(session)).get_detail(content_id))


@router.get(
    "/{contentId}/nearby",
    response_model=BaseDto[NearbyPlacesDto],
    summary="주변 장소 조회",
    description="기준 장소에서 지정 반경 안의 추천 가능 공공 장소를 거리순으로 조회합니다.",
    responses={
        401: OPTIONAL_AUTH_ERROR,
        404: {"model": ErrorResponseDto},
        422: PLACE_RULE_ERROR,
        429: AUTH_RATE_LIMIT_ERROR,
    },
)
async def get_nearby_places(
    session: Annotated[AsyncSession, Depends(get_database_session)],
    _current_profile: Annotated[AuthenticatedProfile | None, Depends(get_optional_current_profile)],
    content_id: Annotated[str, Path(alias="contentId", min_length=1, max_length=50)],
    radius_km: Annotated[float, Query(alias="radiusKm")] = 3.0,
    category: Annotated[str | None, Query(description="쉼표로 구분한 PlaceCategory 목록")] = None,
    limit: Annotated[int, Query(ge=1, le=30)] = 10,
) -> BaseDto[NearbyPlacesDto]:
    service = PlaceService(PlaceRepository(session))
    return success_response(
        await service.get_nearby(
            content_id,
            radius_km=radius_km,
            categories=service.parse_categories(category),
            limit=limit,
        )
    )
