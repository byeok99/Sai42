"""Place browsing and geographic-search use cases."""

from math import cos, radians

from app.common.application.dto import ErrorDetailDto, PageMetaDto
from app.common.application.errors import BusinessException
from app.common.domain.enums import District, SpaceType
from app.place.application.dto import (
    NearbyPlaceDto,
    NearbyPlacesDto,
    PlaceDetailDto,
    PlaceSourceDto,
    PlaceSummaryDto,
)
from app.place.domain.constants import (
    PLACE_CATEGORY_BY_CONTENT_TYPE_ID,
    SOURCE_LICENSE,
    SOURCE_PROVIDER,
)
from app.place.domain.distance import EARTH_RADIUS_KM, haversine_km
from app.place.domain.enums import PlaceCategory
from app.place.domain.query import PlaceSearchCriteria
from app.place.infrastructure.models import Place
from app.place.infrastructure.repository import PlaceRepository

MINIMUM_RADIUS_KM = 0.1
MAXIMUM_RADIUS_KM = 30.0


class PlaceService:
    def __init__(self, repository: PlaceRepository) -> None:
        self.repository = repository

    @staticmethod
    def parse_categories(raw_categories: str | None) -> tuple[PlaceCategory, ...]:
        if raw_categories is None:
            return ()
        values = [value.strip() for value in raw_categories.split(",")]
        try:
            if not all(values):
                raise ValueError
            return tuple(dict.fromkeys(PlaceCategory(value) for value in values))
        except ValueError:
            raise BusinessException(
                status_code=422,
                code="COMMON_VALIDATION_ERROR",
                message="요청 값을 확인해 주세요.",
                errors=[
                    ErrorDetailDto(
                        field="category",
                        reason="INVALID_PLACE_CATEGORY",
                        rejected_value=raw_categories,
                    )
                ],
            ) from None

    async def search(
        self,
        *,
        keyword: str | None,
        district: District | None,
        categories: tuple[PlaceCategory, ...],
        space_type: SpaceType | None,
        latitude: float | None,
        longitude: float | None,
        radius_km: float | None,
        has_image: bool | None,
        page: int,
        size: int,
    ) -> tuple[list[PlaceSummaryDto], PageMetaDto]:
        self._validate_filter_values(district, space_type)
        coordinates = self._validate_coordinates(latitude, longitude, radius_km)
        criteria = PlaceSearchCriteria(
            keyword=keyword.strip() if keyword and keyword.strip() else None,
            district=district,
            categories=categories,
            space_type=space_type,
            has_image=has_image,
        )
        if coordinates is None:
            places, total = await self.repository.list_page(
                criteria, offset=(page - 1) * size, limit=size
            )
        else:
            latitude, longitude, radius_km = coordinates
            candidates = await self._radius_candidates(
                criteria, latitude=latitude, longitude=longitude, radius_km=radius_km
            )
            ranked = sorted(
                (
                    (haversine_km(latitude, longitude, place.latitude, place.longitude), place)
                    for place in candidates
                ),
                key=lambda item: (item[0], item[1].content_id),
            )
            places_in_radius = [place for distance, place in ranked if distance <= radius_km]
            total = len(places_in_radius)
            places = places_in_radius[(page - 1) * size : page * size]
        return [self._summary(place) for place in places], self._page_meta(page, size, total)

    async def get_detail(self, content_id: str) -> PlaceDetailDto:
        place = await self._required_place(content_id)
        summary = self._summary(place)
        return PlaceDetailDto(
            **summary.model_dump(),
            content_type_id=place.content_type_id,
            address_detail=place.address_detail,
            telephone=place.telephone or None,
            source=PlaceSourceDto(
                provider=SOURCE_PROVIDER,
                license=SOURCE_LICENSE,
                original_modified_at=place.source_modified_at,
            ),
        )

    async def get_nearby(
        self,
        content_id: str,
        *,
        radius_km: float,
        categories: tuple[PlaceCategory, ...],
        limit: int,
    ) -> NearbyPlacesDto:
        self._validate_radius(radius_km)
        origin = await self._required_place(content_id)
        candidates = await self._radius_candidates(
            PlaceSearchCriteria(categories=categories),
            latitude=origin.latitude,
            longitude=origin.longitude,
            radius_km=radius_km,
        )
        ranked = []
        for place in candidates:
            if place.content_id == origin.content_id:
                continue
            distance = haversine_km(
                origin.latitude, origin.longitude, place.latitude, place.longitude
            )
            if distance <= radius_km:
                ranked.append((distance, place))
        ranked.sort(key=lambda item: (item[0], item[1].content_id))
        return NearbyPlacesDto(
            origin=self._summary(origin),
            places=[
                NearbyPlaceDto(place=self._summary(place), distance_km=round(distance, 3))
                for distance, place in ranked[:limit]
            ],
        )

    async def _required_place(self, content_id: str) -> Place:
        place = await self.repository.find_by_content_id(content_id)
        if place is None:
            raise BusinessException(
                status_code=404,
                code="PLACE_NOT_FOUND",
                message="장소를 찾을 수 없습니다.",
            )
        return place

    async def _radius_candidates(
        self,
        criteria: PlaceSearchCriteria,
        *,
        latitude: float,
        longitude: float,
        radius_km: float,
    ) -> list[Place]:
        latitude_delta = radius_km / EARTH_RADIUS_KM * 180
        longitude_factor = max(cos(radians(latitude)), 0.000001)
        longitude_delta = latitude_delta / longitude_factor
        return await self.repository.list_candidates(
            criteria,
            minimum_latitude=max(-90, latitude - latitude_delta),
            maximum_latitude=min(90, latitude + latitude_delta),
            minimum_longitude=max(-180, longitude - longitude_delta),
            maximum_longitude=min(180, longitude + longitude_delta),
        )

    @staticmethod
    def _summary(place: Place) -> PlaceSummaryDto:
        return PlaceSummaryDto(
            content_id=place.content_id,
            name=place.title,
            category=PlaceCategory(PLACE_CATEGORY_BY_CONTENT_TYPE_ID[place.content_type_id]),
            district=District(place.district) if place.district else None,
            address=place.address,
            latitude=place.latitude,
            longitude=place.longitude,
            image_url=place.image_url or None,
            indoor_outdoor=SpaceType(place.space_type) if place.space_type else None,
        )

    @staticmethod
    def _validate_filter_values(district: District | None, space_type: SpaceType | None) -> None:
        for field, value in (("district", district), ("spaceType", space_type)):
            if value and value.value == "ANY":
                raise BusinessException(
                    status_code=422,
                    code="COMMON_VALIDATION_ERROR",
                    message="요청 값을 확인해 주세요.",
                    errors=[
                        ErrorDetailDto(field=field, reason="ANY_NOT_ALLOWED", rejected_value=value)
                    ],
                )

    @classmethod
    def _validate_coordinates(
        cls,
        latitude: float | None,
        longitude: float | None,
        radius_km: float | None,
    ) -> tuple[float, float, float] | None:
        values = (latitude, longitude, radius_km)
        if all(value is None for value in values):
            return None
        if (
            any(value is None for value in values)
            or not (-90 <= latitude <= 90)
            or not (-180 <= longitude <= 180)
        ):
            raise BusinessException(
                status_code=422,
                code="PLACE_INVALID_COORDINATES",
                message="위도, 경도와 반경을 올바르게 입력해 주세요.",
            )
        cls._validate_radius(radius_km)
        return latitude, longitude, radius_km

    @staticmethod
    def _validate_radius(radius_km: float) -> None:
        if not MINIMUM_RADIUS_KM <= radius_km <= MAXIMUM_RADIUS_KM:
            raise BusinessException(
                status_code=422,
                code="PLACE_RADIUS_OUT_OF_RANGE",
                message="검색 반경은 0.1km 이상 30km 이하여야 합니다.",
            )

    @staticmethod
    def _page_meta(page: int, size: int, total: int) -> PageMetaDto:
        total_pages = (total + size - 1) // size
        return PageMetaDto(
            page=page,
            size=size,
            total_elements=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
        )
