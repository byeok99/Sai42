"""Common domain enums exposed by the options endpoint."""

from enum import StrEnum


class TimeSlot(StrEnum):
    MORNING = "MORNING"
    AFTERNOON = "AFTERNOON"
    FULL_DAY = "FULL_DAY"


class District(StrEnum):
    DONG_GU = "DONG_GU"
    JUNG_GU = "JUNG_GU"
    SEO_GU = "SEO_GU"
    YUSEONG_GU = "YUSEONG_GU"
    DAEDEOK_GU = "DAEDEOK_GU"
    ANY = "ANY"


class SpaceType(StrEnum):
    INDOOR = "INDOOR"
    OUTDOOR = "OUTDOOR"
    ANY = "ANY"


class Mood(StrEnum):
    QUIET = "QUIET"
    EMOTIONAL = "EMOTIONAL"
    LIVELY = "LIVELY"
    SPECIAL = "SPECIAL"


class ActivityType(StrEnum):
    TOURISM = "TOURISM"
    CULTURE_EXHIBITION = "CULTURE_EXHIBITION"
    FOOD = "FOOD"
    SHOPPING = "SHOPPING"
    WALK = "WALK"
    LEPORTS = "LEPORTS"


class ScheduleDensity(StrEnum):
    RELAXED = "RELAXED"
    NORMAL = "NORMAL"
    TIGHT = "TIGHT"


class Transportation(StrEnum):
    WALK = "WALK"
    PUBLIC_TRANSIT = "PUBLIC_TRANSIT"
    CAR = "CAR"
    FLEXIBLE = "FLEXIBLE"


class RankingSort(StrEnum):
    POPULAR = "POPULAR"
    LATEST = "LATEST"
