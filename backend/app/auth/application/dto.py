"""Identity request and response DTOs."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import Field, field_validator

from app.auth.domain.nickname import (
    nickname_contains_forbidden_token,
    prepare_nickname,
)
from app.common.application.dto import ApiDto

Password = Annotated[
    str,
    Field(
        min_length=4,
        max_length=4,
        pattern=r"^\d{4}$",
        repr=False,
        json_schema_extra={"format": "password", "writeOnly": True},
    ),
]


class ProfileCredentialsRequestDto(ApiDto):
    """Nickname and password input shared by registration and verification."""

    nickname: str = Field(min_length=2, max_length=14)
    password: Password

    @field_validator("nickname", mode="before")
    @classmethod
    def normalize_display_nickname(cls, value: object) -> object:
        if isinstance(value, str):
            return prepare_nickname(value)
        return value


class CreateProfileRequestDto(ProfileCredentialsRequestDto):
    """Anonymous profile registration input."""

    @field_validator("nickname")
    @classmethod
    def reject_reserved_nickname(cls, value: str) -> str:
        if nickname_contains_forbidden_token(value):
            raise ValueError("사용할 수 없는 닉네임입니다.")
        return value


class VerifyProfileRequestDto(ProfileCredentialsRequestDto):
    """Credential verification input without token issuance."""


class NicknameSuggestionsDto(ApiDto):
    """Nickname candidates derived from stored public place titles."""

    suggestions: list[str]


class ProfileCreatedDto(ApiDto):
    """Profile registration result."""

    profile_id: UUID
    nickname: str
    has_active_date_course: bool
    completed_date_course_count: int = Field(ge=0)
    created_at: datetime


class ProfileVerifiedDto(ApiDto):
    """Successful credential verification result."""

    profile_id: UUID
    nickname: str
    has_active_date_course: bool
    completed_date_course_count: int = Field(ge=0)
    verified_at: datetime


class MyProfileDto(ApiDto):
    """Authenticated profile summary."""

    profile_id: UUID
    nickname: str
    has_active_date_course: bool
    completed_date_course_count: int = Field(ge=0)
    published_course_count: int = Field(ge=0)
    created_at: datetime
