"""Community and ranking response contracts."""

from datetime import date, datetime
from uuid import UUID

from pydantic import Field, field_validator

from app.common.application.dto import ApiDto
from app.common.domain.enums import District, TimeSlot
from app.course.application.dto import (
    CopyCourseRequestDto,
    CourseConditionDto,
    CourseMapDto,
    CoursePlaceDto,
)


class CommunityPostSummaryDto(ApiDto):
    rank: int
    post_id: str
    course_id: str
    course_title: str
    main_district: District
    author_nickname: str
    one_line_comment: str
    course_like_count: int
    place_heart_count: int
    liked_by_me: bool
    tags: list[str]
    published_at: datetime


class CommunityPostDetailDto(ApiDto):
    post_id: str
    owner: bool
    course_id: str
    course_title: str
    author_nickname: str
    one_line_comment: str
    date: date
    time_slot: TimeSlot
    overall_comment: str
    conditions: CourseConditionDto
    tags: list[str]
    places: list[CoursePlaceDto]
    map: CourseMapDto
    course_like_count: int
    place_heart_count: int
    liked_by_me: bool
    published_at: datetime


class PublishCommunityPostRequestDto(ApiDto):
    date_course_id: str
    one_line_comment: str = Field(max_length=80)

    @field_validator("one_line_comment", mode="before")
    @classmethod
    def trim_comment(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class UpdateCommunityPostRequestDto(ApiDto):
    one_line_comment: str = Field(max_length=80)

    @field_validator("one_line_comment", mode="before")
    @classmethod
    def trim_comment(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class CommunityLikeDto(ApiDto):
    post_id: str
    liked_by_me: bool
    like_count: int


class DateMasterDto(ApiDto):
    rank: int
    profile_id: UUID
    nickname: str
    published_course_count: int
    received_like_count: int


class DateMastersDto(ApiDto):
    masters: list[DateMasterDto]


__all__ = [
    "CommunityLikeDto",
    "CommunityPostDetailDto",
    "CommunityPostSummaryDto",
    "CopyCourseRequestDto",
    "DateMasterDto",
    "DateMastersDto",
    "PublishCommunityPostRequestDto",
    "UpdateCommunityPostRequestDto",
]
