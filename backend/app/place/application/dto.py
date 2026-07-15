"""Place API request-independent response contracts."""

from datetime import datetime

from app.common.application.dto import ApiDto
from app.common.domain.enums import District, SpaceType
from app.place.domain.enums import PlaceCategory


class PlaceSummaryDto(ApiDto):
    content_id: str
    name: str
    category: PlaceCategory
    district: District | None
    address: str
    latitude: float
    longitude: float
    image_url: str | None
    indoor_outdoor: SpaceType | None


class PlaceSourceDto(ApiDto):
    provider: str
    license: str
    original_modified_at: datetime | None


class PlaceDetailDto(PlaceSummaryDto):
    content_type_id: int
    address_detail: str
    telephone: str | None
    source: PlaceSourceDto


class NearbyPlaceDto(ApiDto):
    place: PlaceSummaryDto
    distance_km: float


class NearbyPlacesDto(ApiDto):
    origin: PlaceSummaryDto
    places: list[NearbyPlaceDto]
