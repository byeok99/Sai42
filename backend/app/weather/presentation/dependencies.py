"""Weather provider composition dependencies."""

from typing import Annotated

from fastapi import Depends

from app.config import Settings, get_request_settings
from app.weather.domain.provider import WeatherProvider
from app.weather.infrastructure.open_meteo_provider import OpenMeteoWeatherProvider


def get_weather_provider(
    settings: Annotated[Settings, Depends(get_request_settings)],
) -> WeatherProvider:
    return OpenMeteoWeatherProvider(
        base_url=settings.weather_api_base_url,
        timeout_seconds=settings.weather_api_timeout_seconds,
    )
