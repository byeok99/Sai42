"""Provider-independent AI course planning entities."""

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.chat.domain.enums import ChatTurnIntent
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
    requested_activity_matches: list[str] = Field(default_factory=list)
    is_current: bool = False
    distance_to_current_course_km: float | None = Field(default=None, ge=0)


class AiConversationMessage(BaseModel):
    """A bounded prior chat turn supplied as context to the provider."""

    model_config = ConfigDict(frozen=True)

    role: Literal["USER", "ASSISTANT"]
    content: str = Field(min_length=1, max_length=1000)


MemoryNote = Annotated[str, Field(min_length=1, max_length=160)]
MemoryContentId = Annotated[str, Field(min_length=1, max_length=100)]


class AiConversationMemory(BaseModel):
    """Compact, session-scoped facts retained beyond the recent-message window."""

    summary: str = Field(default="", max_length=1500)
    preference_notes: list[MemoryNote] = Field(default_factory=list, max_length=12)
    must_keep_content_ids: list[MemoryContentId] = Field(default_factory=list, max_length=4)
    excluded_content_ids: list[MemoryContentId] = Field(default_factory=list, max_length=20)
    pending_clarification: str | None = Field(default=None, max_length=300)


class AiCoursePlace(BaseModel):
    """A model-selected place reference constrained to supplied candidate IDs."""

    content_id: str
    estimated_stay_minutes: int = Field(ge=30, le=240)
    space_type: Literal[SpaceType.INDOOR, SpaceType.OUTDOOR]
    sweet_comment: str = Field(min_length=1, max_length=200)


class AiCourseContent(BaseModel):
    """Course fields shared by initial generation and an in-chat edit proposal."""

    title: str = Field(min_length=1, max_length=60)
    overall_comment: str = Field(min_length=1, max_length=500)
    tags: list[str] = Field(min_length=1, max_length=5)
    places: list[AiCoursePlace] = Field(min_length=2, max_length=4)


class AiCoursePlan(AiCourseContent):
    """Structured output for an initial course generation."""

    assistant_message: str = Field(min_length=1, max_length=500)
    warnings: list[str] = Field(default_factory=list, max_length=5)


class AiChatTurn(BaseModel):
    """Structured output that separates conversation from an actual course edit."""

    intent: ChatTurnIntent
    assistant_message: str = Field(min_length=1, max_length=500)
    proposed_course: AiCourseContent | None = None
    warnings: list[str] = Field(default_factory=list, max_length=5)
    memory: AiConversationMemory = Field(default_factory=AiConversationMemory)

    @model_validator(mode="after")
    def require_course_only_for_edit(self) -> "AiChatTurn":
        has_course = self.proposed_course is not None
        if (self.intent == ChatTurnIntent.COURSE_EDIT) != has_course:
            raise ValueError("course edit intent and proposed course must be provided together")
        return self


class AiCourseRequest(BaseModel):
    """Complete, stateless context passed to a course-planning provider."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    conditions: dict[str, Any]
    weather: dict[str, Any] | None
    candidates: list[PlaceCandidate]
    user_request: str
    current_draft: dict[str, Any] | None = None
    conversation: list[AiConversationMessage] = Field(default_factory=list)
    memory: AiConversationMemory = Field(default_factory=AiConversationMemory)
    edit_action: str | None = None
    validation_errors: list[str] = Field(default_factory=list)
