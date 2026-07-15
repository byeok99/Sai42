"""Weather summary and recommendation response contracts."""

from datetime import date, datetime

from app.common.application.dto import ApiDto
from app.common.domain.enums import District, SpaceType, TimeSlot
from app.weather.domain.enums import WeatherCondition


class WeatherRecommendationDto(ApiDto):
    preferred_space_type: SpaceType
    indoor_ratio: float | None
    message: str


class WeatherSummaryDto(ApiDto):
    available: bool
    district: District
    date: date
    time_slot: TimeSlot
    summary: str | None
    temperature_min: float | None
    temperature_max: float | None
    precipitation_probability: int | None
    condition: WeatherCondition | None
    recommendation: WeatherRecommendationDto
    provider: str
    observed_at: datetime | None
