"""Geographic calculations independent from persistence concerns."""

from math import asin, cos, radians, sin, sqrt

EARTH_RADIUS_KM = 6371.0088


def haversine_km(
    latitude: float,
    longitude: float,
    other_latitude: float,
    other_longitude: float,
) -> float:
    """Return the great-circle distance between two WGS84 coordinates."""
    latitude_delta = radians(other_latitude - latitude)
    longitude_delta = radians(other_longitude - longitude)
    origin_latitude = radians(latitude)
    target_latitude = radians(other_latitude)
    haversine = sin(latitude_delta / 2) ** 2 + (
        cos(origin_latitude) * cos(target_latitude) * sin(longitude_delta / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * asin(sqrt(haversine))
