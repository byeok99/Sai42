"""Normalized weather conditions independent from a provider payload."""

from enum import StrEnum


class WeatherCondition(StrEnum):
    CLEAR = "CLEAR"
    CLOUDY = "CLOUDY"
    OVERCAST = "OVERCAST"
    LIGHT_RAIN = "LIGHT_RAIN"
    RAIN = "RAIN"
    RAIN_SNOW = "RAIN_SNOW"
    SNOW = "SNOW"
