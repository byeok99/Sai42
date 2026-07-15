"""Provider-neutral weather forecast entities."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class HourlyForecast:
    hour: int
    temperature: float
    precipitation_probability: int
    precipitation_type: int
    sky: int


@dataclass(frozen=True, slots=True)
class WeatherForecast:
    hours: tuple[HourlyForecast, ...]
    observed_at: datetime


class WeatherProviderError(Exception):
    """Raised for safe fallback when a provider cannot supply a forecast."""
