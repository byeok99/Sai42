"""Weather API and Open-Meteo payload contract tests."""

import unittest
from datetime import timedelta

import httpx

from app.common.domain.enums import District
from app.common.domain.time import now_seoul
from app.config import Settings
from app.main import create_app
from app.weather.infrastructure.open_meteo_provider import OpenMeteoWeatherProvider
from app.weather.presentation.dependencies import get_weather_provider


class WeatherApiTest(unittest.IsolatedAsyncioTestCase):
    async def test_open_meteo_forecast_is_normalized_for_the_requested_time_slot(self) -> None:
        target = now_seoul().date()

        def handler(_: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "hourly": {
                        "time": [
                            f"{target.isoformat()}T12:00",
                            f"{target.isoformat()}T13:00",
                            f"{target.isoformat()}T14:00",
                        ],
                        "temperature_2m": [24, 25, 26],
                        "precipitation_probability": [20, 60, 50],
                        "weather_code": [2, 61, 63],
                    }
                },
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = OpenMeteoWeatherProvider(
                base_url="https://weather.test/forecast",
                timeout_seconds=1,
                client=client,
            )
            app = create_app(Settings())
            app.dependency_overrides[get_weather_provider] = lambda: provider
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
                base_url="http://testserver",
            ) as api_client:
                response = await api_client.get(
                    "/api/v1/weather",
                    params={
                        "date": target.isoformat(),
                        "district": District.YUSEONG_GU,
                        "timeSlot": "AFTERNOON",
                    },
                )

        self.assertEqual(200, response.status_code, response.text)
        data = response.json()["data"]
        self.assertTrue(data["available"])
        self.assertEqual(24, data["temperatureMin"])
        self.assertEqual(26, data["temperatureMax"])
        self.assertEqual(60, data["precipitationProbability"])
        self.assertEqual("RAIN", data["condition"])
        self.assertEqual("INDOOR", data["recommendation"]["preferredSpaceType"])

    async def test_missing_provider_falls_back_and_invalid_date_is_rejected(self) -> None:
        app = create_app(Settings())
        app.dependency_overrides[get_weather_provider] = lambda: None
        today = now_seoul().date()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://testserver",
        ) as client:
            fallback = await client.get(
                "/api/v1/weather",
                params={"date": today.isoformat(), "district": "ANY", "timeSlot": "FULL_DAY"},
            )
            invalid = await client.get(
                "/api/v1/weather",
                params={
                    "date": (today + timedelta(days=4)).isoformat(),
                    "district": "SEO_GU",
                    "timeSlot": "MORNING",
                },
            )

        self.assertEqual(200, fallback.status_code)
        data = fallback.json()["data"]
        self.assertFalse(data["available"])
        self.assertEqual("ANY", data["recommendation"]["preferredSpaceType"])
        self.assertIsNone(data["recommendation"]["indoorRatio"])
        self.assertEqual(422, invalid.status_code)
        self.assertEqual("WEATHER_DATE_OUT_OF_RANGE", invalid.json()["code"])


if __name__ == "__main__":
    unittest.main()
