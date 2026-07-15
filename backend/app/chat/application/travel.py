"""Coordinate-based travel-time estimates for course scheduling."""

from math import ceil

from app.chat.application.quality import haversine_km
from app.common.domain.enums import Transportation

FLEXIBLE_WALK_THRESHOLD_KM = 1.2
ROUNDING_UNIT_MINUTES = 5

# Urban effective speeds include ordinary route friction. A route factor converts straight-line
# WGS84 distance into a conservative network-distance estimate without using external map data.
TRAVEL_PROFILES: dict[Transportation, tuple[float, float, int]] = {
    Transportation.WALK: (1.20, 4.5, 0),
    Transportation.PUBLIC_TRANSIT: (1.35, 18.0, 8),
    Transportation.CAR: (1.30, 24.0, 5),
}


def estimate_travel_minutes(
    first: tuple[float, float],
    second: tuple[float, float],
    transportation: Transportation | None,
) -> int:
    """Estimate point-to-point travel time from stored coordinates and the selected mode."""

    distance_km = haversine_km(*first, *second)
    if distance_km < 0.05:
        return 0

    mode = transportation or Transportation.FLEXIBLE
    if mode == Transportation.FLEXIBLE:
        mode = (
            Transportation.WALK
            if distance_km <= FLEXIBLE_WALK_THRESHOLD_KM
            else Transportation.PUBLIC_TRANSIT
        )

    route_factor, effective_speed_kmh, overhead_minutes = TRAVEL_PROFILES[mode]
    raw_minutes = distance_km * route_factor / effective_speed_kmh * 60 + overhead_minutes
    rounded = ceil(raw_minutes / ROUNDING_UNIT_MINUTES) * ROUNDING_UNIT_MINUTES
    return max(ROUNDING_UNIT_MINUTES, rounded)
