"""Validated place-search criteria passed into persistence."""

from dataclasses import dataclass

from app.common.domain.enums import District, SpaceType
from app.place.domain.enums import PlaceCategory


@dataclass(frozen=True, slots=True)
class PlaceSearchCriteria:
    keyword: str | None = None
    district: District | None = None
    categories: tuple[PlaceCategory, ...] = ()
    space_type: SpaceType | None = None
    has_image: bool | None = None
