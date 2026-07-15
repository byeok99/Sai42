"""DTOs for health and option metadata APIs."""

from typing import Literal

from app.common.application.dto import ApiDto


class HealthDto(ApiDto):
    """Operational status without exposing configuration or secrets."""

    status: Literal["UP"]
    database: Literal["UP"]
    ai_provider: Literal["UP", "DEGRADED", "NOT_CONFIGURED"]
    weather_provider: Literal["UP", "DEGRADED", "NOT_CONFIGURED"]
    version: str


class OptionDto(ApiDto):
    """An enum value and its Korean display label."""

    value: str
    label: str


class MetaOptionsDto(ApiDto):
    """All selector values required by the frontend contract."""

    time_slots: list[OptionDto]
    districts: list[OptionDto]
    space_types: list[OptionDto]
    moods: list[OptionDto]
    activity_types: list[OptionDto]
    schedule_densities: list[OptionDto]
    transportations: list[OptionDto]
    ranking_sorts: list[OptionDto]
