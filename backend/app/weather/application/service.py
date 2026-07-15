"""Weather lookup, normalization, and recommendation rules."""

from datetime import date, timedelta

from app.common.application.errors import BusinessException
from app.common.domain.enums import District, SpaceType, TimeSlot
from app.common.domain.time import now_seoul
from app.weather.application.dto import WeatherRecommendationDto, WeatherSummaryDto
from app.weather.domain.entities import HourlyForecast, WeatherProviderError
from app.weather.domain.enums import WeatherCondition
from app.weather.domain.provider import WeatherProvider

PROVIDER_NAME = "Open-Meteo"
HOURS_BY_SLOT = {
    TimeSlot.MORNING: range(6, 12),
    TimeSlot.AFTERNOON: range(12, 22),
    TimeSlot.FULL_DAY: range(6, 22),
}


class WeatherService:
    def __init__(self, provider: WeatherProvider | None) -> None:
        self.provider = provider

    async def get_weather(
        self, *, target_date: date, district: District, time_slot: TimeSlot
    ) -> WeatherSummaryDto:
        today = now_seoul().date()
        if target_date < today or target_date > today + timedelta(days=3):
            raise BusinessException(
                status_code=422,
                code="WEATHER_DATE_OUT_OF_RANGE",
                message="날씨는 오늘부터 글피까지 조회할 수 있습니다.",
            )
        if self.provider is None:
            return self.unavailable(target_date, district, time_slot)
        try:
            forecast = await self.provider.forecast(target_date, district)
            selected = [item for item in forecast.hours if item.hour in HOURS_BY_SLOT[time_slot]]
            if not selected:
                raise WeatherProviderError("time slot unavailable")
        except WeatherProviderError:
            return self.unavailable(target_date, district, time_slot)

        condition = self._condition(selected)
        recommendation = self._recommendation(condition)
        return WeatherSummaryDto(
            available=True,
            district=district,
            date=target_date,
            time_slot=time_slot,
            summary=self._summary(condition),
            temperature_min=min(item.temperature for item in selected),
            temperature_max=max(item.temperature for item in selected),
            precipitation_probability=max(item.precipitation_probability for item in selected),
            condition=condition,
            recommendation=recommendation,
            provider=PROVIDER_NAME,
            observed_at=forecast.observed_at,
        )

    @staticmethod
    def _condition(items: list[HourlyForecast]) -> WeatherCondition:
        precipitation_types = {item.precipitation_type for item in items}
        max_probability = max(item.precipitation_probability for item in items)
        if 3 in precipitation_types:
            return WeatherCondition.SNOW
        if 2 in precipitation_types:
            return WeatherCondition.RAIN_SNOW
        if precipitation_types & {1, 4}:
            return WeatherCondition.LIGHT_RAIN if max_probability < 50 else WeatherCondition.RAIN
        max_sky = max(item.sky for item in items)
        if max_sky >= 4:
            return WeatherCondition.OVERCAST
        if max_sky >= 3:
            return WeatherCondition.CLOUDY
        return WeatherCondition.CLEAR

    @staticmethod
    def _summary(condition: WeatherCondition) -> str:
        return {
            WeatherCondition.CLEAR: "대체로 맑은 날씨예요.",
            WeatherCondition.CLOUDY: "구름이 많은 날씨예요.",
            WeatherCondition.OVERCAST: "흐린 날씨가 이어질 전망이에요.",
            WeatherCondition.LIGHT_RAIN: "선택 시간대에 약한 비 예보가 있어요.",
            WeatherCondition.RAIN: "선택 시간대에 비 예보가 있어요.",
            WeatherCondition.RAIN_SNOW: "선택 시간대에 비 또는 눈 예보가 있어요.",
            WeatherCondition.SNOW: "선택 시간대에 눈 예보가 있어요.",
        }[condition]

    @staticmethod
    def _recommendation(condition: WeatherCondition) -> WeatherRecommendationDto:
        if condition in {
            WeatherCondition.LIGHT_RAIN,
            WeatherCondition.RAIN,
            WeatherCondition.RAIN_SNOW,
            WeatherCondition.SNOW,
        }:
            return WeatherRecommendationDto(
                preferred_space_type=SpaceType.INDOOR,
                indoor_ratio=0.7,
                message="강수 예보를 반영해 실내 장소를 중심으로 추천할게요.",
            )
        if condition == WeatherCondition.CLEAR:
            return WeatherRecommendationDto(
                preferred_space_type=SpaceType.OUTDOOR,
                indoor_ratio=0.3,
                message="맑은 날씨를 즐길 수 있도록 야외 장소도 함께 추천할게요.",
            )
        return WeatherRecommendationDto(
            preferred_space_type=SpaceType.ANY,
            indoor_ratio=0.5,
            message="실내외 장소를 균형 있게 추천할게요.",
        )

    @staticmethod
    def unavailable(
        target_date: date, district: District, time_slot: TimeSlot
    ) -> WeatherSummaryDto:
        return WeatherSummaryDto(
            available=False,
            district=district,
            date=target_date,
            time_slot=time_slot,
            summary=None,
            temperature_min=None,
            temperature_max=None,
            precipitation_probability=None,
            condition=None,
            recommendation=WeatherRecommendationDto(
                preferred_space_type=SpaceType.ANY,
                indoor_ratio=None,
                message="날씨를 확인하지 못해 입력한 공간 조건만 반영할게요.",
            ),
            provider=PROVIDER_NAME,
            observed_at=None,
        )
