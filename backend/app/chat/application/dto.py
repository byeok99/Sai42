"""Chat session and mutable course-draft HTTP contracts."""

from datetime import date, datetime, time
from typing import Any

from pydantic import Field, field_validator

from app.chat.domain.enums import ChatMessageRole, ChatSessionStatus, CourseEditAction
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
from app.course.application.dto import (
    CourseConditionDto,
    CourseMapDto,
    CoursePlaceSnapshotDto,
)
from app.weather.application.dto import WeatherSummaryDto


class CreateChatSessionRequestDto(ApiDto):
    date: date
    time_slot: TimeSlot
    start_time: time
    district: District
    space_type: SpaceType
    moods: list[Mood] = Field(min_length=1, max_length=4)
    activities: list[ActivityType] = Field(min_length=1, max_length=5)
    schedule_density: ScheduleDensity
    transportation: Transportation
    initial_message: str | None = None

    @field_validator("moods", "activities")
    @classmethod
    def require_unique_values(cls, value: list[Any]) -> list[Any]:
        if len(value) != len(set(value)):
            raise ValueError("중복된 조건을 전달할 수 없습니다.")
        return value

    @field_validator("initial_message", mode="before")
    @classmethod
    def normalize_initial_message(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None
        return value

    def conditions(self) -> CourseConditionDto:
        return CourseConditionDto(**self.model_dump(exclude={"initial_message"}))


class ChatMessageDto(ApiDto):
    message_id: str
    role: ChatMessageRole
    content: str
    created_at: datetime


class CourseDraftPlaceDto(ApiDto):
    course_place_id: str
    order: int
    scheduled_at: datetime
    estimated_stay_minutes: int
    place: CoursePlaceSnapshotDto
    sweet_comment: str


class CourseDraftDto(ApiDto):
    draft_id: str
    version: int
    title: str
    date: date
    time_slot: TimeSlot
    overall_comment: str
    estimated_total_minutes: int
    conditions: CourseConditionDto
    tags: list[str]
    weather: WeatherSummaryDto | None
    places: list[CourseDraftPlaceDto] = Field(min_length=2, max_length=4)
    map: CourseMapDto


class CreateChatSessionDto(ApiDto):
    session_id: str
    status: ChatSessionStatus
    assistant_message: ChatMessageDto
    course_draft: CourseDraftDto


class ChatSessionDto(ApiDto):
    session_id: str
    status: ChatSessionStatus
    conditions: CourseConditionDto
    messages: list[ChatMessageDto]
    course_draft: CourseDraftDto | None


class SendChatMessageRequestDto(ApiDto):
    message: str | None = None
    quick_action: CourseEditAction | None = None
    expected_draft_version: int = Field(ge=1)

    @field_validator("message", mode="before")
    @classmethod
    def trim_message(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class CourseDraftChangeSummaryDto(ApiDto):
    changed: bool
    warnings: list[str]


class SendChatMessageDto(ApiDto):
    user_message: ChatMessageDto
    assistant_message: ChatMessageDto
    change_summary: CourseDraftChangeSummaryDto
    course_draft: CourseDraftDto


class ConfirmChatSessionRequestDto(ApiDto):
    draft_id: str
    expected_version: int = Field(ge=1)
