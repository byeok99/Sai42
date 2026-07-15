"""Weather provider composition dependencies."""

from typing import Annotated

from fastapi import Depends, Request

from app.config import Settings, get_request_settings
from app.weather.domain.provider import WeatherProvider
from app.weather.infrastructure.open_meteo_provider import OpenMeteoWeatherProvider


async def get_weather_provider(
    request: Request,
    settings: Annotated[Settings, Depends(get_request_settings)],
) -> WeatherProvider:
    provider = getattr(request.app.state, "weather_provider", None)
    if provider is not None:
        return provider
    async with request.app.state.weather_provider_lock:
        provider = getattr(request.app.state, "weather_provider", None)
        if provider is None:
            provider = OpenMeteoWeatherProvider(
                base_url=settings.weather_api_base_url,
                timeout_seconds=settings.weather_api_timeout_seconds,
            )
            request.app.state.weather_provider = provider
    return provider
