"""Community list filters independent from HTTP and SQLAlchemy."""

from dataclasses import dataclass

from app.common.domain.enums import (
    ActivityType,
    District,
    Mood,
    RankingSort,
    ScheduleDensity,
    SpaceType,
    TimeSlot,
)


@dataclass(frozen=True, slots=True)
class CommunityPostCriteria:
    sort: RankingSort
    districts: tuple[District, ...] = ()
    time_slots: tuple[TimeSlot, ...] = ()
    space_types: tuple[SpaceType, ...] = ()
    moods: tuple[Mood, ...] = ()
    activities: tuple[ActivityType, ...] = ()
    densities: tuple[ScheduleDensity, ...] = ()
