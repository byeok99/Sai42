"""Current DateCourse HTTP DTO contracts."""

from datetime import date, datetime, time
from typing import Any

from pydantic import Field, field_validator

from app.common.application.dto import ApiDto
from app.common.domain.enums import (
    ActivityType,
    District,
    Mood,
    ScheduleDensity,
    SpaceType,
    TimeSlot,
    Transportation,
)
from app.course.domain.enums import DateCourseSourceType, DateCourseStatus
from app.place.domain.enums import PlaceCategory


class CoordinateDto(ApiDto):
    latitude: float
    longitude: float


class CourseMapDto(ApiDto):
    center_latitude: float | None
    center_longitude: float | None
    polyline: list[CoordinateDto]


class CourseConditionDto(ApiDto):
    date: date
    time_slot: TimeSlot
    start_time: time
    district: District
    space_type: SpaceType
    moods: list[Mood]
    activities: list[ActivityType]
    schedule_density: ScheduleDensity
    transportation: Transportation | None


class CoursePlaceSnapshotDto(ApiDto):
    content_id: str | None
    name: str
    category: PlaceCategory
    district: District | None
    address: str | None
    address_detail: str | None
    latitude: float | None
    longitude: float | None
    image_url: str | None
    indoor_outdoor: SpaceType


class CoursePlaceDto(ApiDto):
    course_place_id: str
    order: int
    scheduled_at: datetime
    estimated_stay_minutes: int
    place: CoursePlaceSnapshotDto
    sweet_comment: str
    hearted_by_me: bool
    heart_count: int


class CourseProgressSummaryDto(ApiDto):
    current_order_no: int
    completed_place_count: int
    total_place_count: int
    progress_percent: int
    all_places_completed: bool


class DateCourseDto(ApiDto):
    course_id: str
    status: DateCourseStatus
    source_type: DateCourseSourceType
    title: str
    date: date
    time_slot: TimeSlot
    overall_comment: str
    estimated_total_minutes: int
    conditions: CourseConditionDto
    tags: list[str]
    weather: dict[str, Any] | None
    places: list[CoursePlaceDto]
    map: CourseMapDto
    progress: CourseProgressSummaryDto
    one_line_comment: str | None
    created_at: datetime
    completed_at: datetime | None


class CompletedPlaceDto(ApiDto):
    course_place_id: str
    order: int
    completed_at: datetime


class DateCourseProgressDto(ApiDto):
    course_id: str
    completed_place: CompletedPlaceDto
    next_place: CoursePlaceDto | None
    current_order_no: int
    completed_place_count: int
    total_place_count: int
    progress_percent: int
    all_places_completed: bool


class CoursePlaceHeartDto(ApiDto):
    course_place_id: str
    hearted_by_me: bool
    heart_count: int
    updated_at: datetime


class CompleteDateCourseRequestDto(ApiDto):
    one_line_comment: str = Field(max_length=80)

    @field_validator("one_line_comment", mode="before")
    @classmethod
    def trim_comment(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class PublishedCommunityPostDto(ApiDto):
    post_id: str
    course_id: str
    status: str
    one_line_comment: str
    published_at: datetime


class CompleteDateCourseDto(ApiDto):
    completed_course: DateCourseDto
    community_post: PublishedCommunityPostDto
