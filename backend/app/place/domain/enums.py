"""Place-specific values defined by the public API contract."""

from enum import StrEnum


class PlaceCategory(StrEnum):
    ATTRACTION = "ATTRACTION"
    CULTURAL_FACILITY = "CULTURAL_FACILITY"
    TRAVEL_COURSE = "TRAVEL_COURSE"
    LEPORTS = "LEPORTS"
    ACCOMMODATION = "ACCOMMODATION"
    SHOPPING = "SHOPPING"
    RESTAURANT = "RESTAURANT"
