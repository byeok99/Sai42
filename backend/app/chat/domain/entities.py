"""Provider-independent AI course planning entities."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.common.domain.enums import SpaceType


class AiCourseProviderError(RuntimeError):
    """The provider returned an unusable or invalid course plan."""


class AiCourseProviderUnavailable(AiCourseProviderError):
    """The provider cannot currently serve a course-planning request."""


class PlaceCandidate(BaseModel):
    """A real recommendable place loaded from the tracked SQLite database."""

    model_config = ConfigDict(frozen=True)

    content_id: str
    title: str
    category: str
    address: str
    address_detail: str
    district: str | None
    latitude: float
    longitude: float
    image_url: str | None
    activities: list[str]


class AiCoursePlace(BaseModel):
    """A model-selected place reference constrained to supplied candidate IDs."""

    content_id: str
    estimated_stay_minutes: int = Field(ge=30, le=240)
    space_type: Literal[SpaceType.INDOOR, SpaceType.OUTDOOR]
    sweet_comment: str = Field(min_length=1, max_length=200)


class AiCoursePlan(BaseModel):
    """Structured output requested from the OpenAI Responses API."""

    title: str = Field(min_length=1, max_length=60)
    overall_comment: str = Field(min_length=1, max_length=500)
    assistant_message: str = Field(min_length=1, max_length=500)
    tags: list[str] = Field(min_length=1, max_length=5)
    places: list[AiCoursePlace] = Field(min_length=2, max_length=4)
    warnings: list[str] = Field(default_factory=list, max_length=5)


class AiCourseRequest(BaseModel):
    """Complete, stateless context passed to a course-planning provider."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    conditions: dict[str, Any]
    weather: dict[str, Any] | None
    candidates: list[PlaceCandidate]
    user_request: str
    current_draft: dict[str, Any] | None = None
