"""Shared success and error DTO contracts."""

from datetime import datetime
from typing import Any, Generic, Literal, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

DataT = TypeVar("DataT")


class ApiDto(BaseModel):
    """Base Pydantic configuration for every HTTP DTO."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class PageMetaDto(ApiDto):
    """One-based pagination metadata."""

    page: int = Field(ge=1)
    size: int = Field(ge=1)
    total_elements: int = Field(ge=0)
    total_pages: int = Field(ge=0)
    has_next: bool
    has_previous: bool


class BaseDto(ApiDto, Generic[DataT]):  # noqa: UP046 - Pydantic generic schema compatibility
    """Success envelope used by every API endpoint."""

    success: Literal[True]
    code: str
    message: str
    data: DataT | None
    meta: PageMetaDto | None
    timestamp: datetime
    trace_id: UUID


class ErrorDetailDto(ApiDto):
    """A sanitized field or business-rule error."""

    field: str | None = None
    reason: str
    rejected_value: Any | None = None


class ErrorResponseDto(ApiDto):
    """Failure envelope used by every exception handler."""

    success: Literal[False]
    code: str
    message: str
    errors: list[ErrorDetailDto]
    timestamp: datetime
    trace_id: UUID
