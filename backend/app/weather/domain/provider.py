"""Port implemented by external weather infrastructure."""

from datetime import date
from typing import Protocol

from app.common.domain.enums import District
from app.weather.domain.entities import WeatherForecast


class WeatherProvider(Protocol):
    async def forecast(self, target_date: date, district: District) -> WeatherForecast: ...
