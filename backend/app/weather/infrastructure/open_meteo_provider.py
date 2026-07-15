"""Open-Meteo keyless hourly forecast adapter."""

from datetime import date, datetime
from typing import Any

import httpx

from app.common.domain.enums import District
from app.common.domain.time import SEOUL_TIMEZONE, now_seoul
from app.weather.domain.entities import HourlyForecast, WeatherForecast, WeatherProviderError

DISTRICT_COORDINATES = {
    District.DONG_GU: (36.312, 127.454),
    District.JUNG_GU: (36.325, 127.421),
    District.SEO_GU: (36.355, 127.383),
    District.YUSEONG_GU: (36.362, 127.356),
    District.DAEDEOK_GU: (36.346, 127.415),
    District.ANY: (36.350, 127.385),
}


class OpenMeteoWeatherProvider:
    def __init__(
        self,
        *,
        base_url: str,
        timeout_seconds: float,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds
        self.client = client

    async def forecast(self, target_date: date, district: District) -> WeatherForecast:
        latitude, longitude = DISTRICT_COORDINATES[district]
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "temperature_2m,precipitation_probability,weather_code",
            "timezone": "Asia/Seoul",
            "start_date": target_date.isoformat(),
            "end_date": target_date.isoformat(),
        }
        try:
            if self.client is not None:
                response = await self.client.get(self.base_url, params=params)
            else:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            return self._parse(response.json())
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exception:
            raise WeatherProviderError(type(exception).__name__) from exception

    @staticmethod
    def _parse(payload: dict[str, Any]) -> WeatherForecast:
        hourly = payload["hourly"]
        times = hourly["time"]
        temperatures = hourly["temperature_2m"]
        probabilities = hourly["precipitation_probability"]
        weather_codes = hourly["weather_code"]
        if not (len(times) == len(temperatures) == len(probabilities) == len(weather_codes)):
            raise WeatherProviderError("hourly array length mismatch")
        hours = []
        for timestamp, temperature, probability, weather_code in zip(
            times, temperatures, probabilities, weather_codes, strict=True
        ):
            if temperature is None or weather_code is None:
                continue
            precipitation_type, sky = _normalized_condition(int(weather_code))
            hours.append(
                HourlyForecast(
                    hour=datetime.fromisoformat(str(timestamp)).hour,
                    temperature=float(temperature),
                    precipitation_probability=int(probability or 0),
                    precipitation_type=precipitation_type,
                    sky=sky,
                )
            )
        if not hours:
            raise WeatherProviderError("hourly forecast unavailable")
        return WeatherForecast(
            hours=tuple(hours),
            observed_at=now_seoul().astimezone(SEOUL_TIMEZONE),
        )


def _normalized_condition(weather_code: int) -> tuple[int, int]:
    """Map WMO weather codes to the provider-neutral precipitation and sky values."""
    if weather_code == 0:
        return 0, 1
    if weather_code in {1, 2}:
        return 0, 3
    if weather_code in {3, 45, 48}:
        return 0, 4
    if weather_code in {56, 57, 66, 67}:
        return 2, 4
    if weather_code in {71, 73, 75, 77}:
        return 3, 4
    return 1, 4
