"""Chat session and course-edit values exposed by the API contract."""

from enum import StrEnum


class ChatSessionStatus(StrEnum):
    ACTIVE = "ACTIVE"
    CONFIRMED = "CONFIRMED"
    DISCARDED = "DISCARDED"
    EXPIRED = "EXPIRED"


class ChatMessageRole(StrEnum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"


class ChatTurnIntent(StrEnum):
    """Internal conversation intents; these values are never exposed by the HTTP API."""

    COURSE_EDIT = "COURSE_EDIT"
    COURSE_QUESTION = "COURSE_QUESTION"
    CASUAL_CONVERSATION = "CASUAL_CONVERSATION"
    CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"


class CourseEditAction(StrEnum):
    CHANGE_CAFE = "CHANGE_CAFE"
    ADD_NIGHT_VIEW = "ADD_NIGHT_VIEW"
    REDUCE_ROUTE = "REDUCE_ROUTE"
    INCREASE_INDOOR = "INCREASE_INDOOR"
    REGENERATE = "REGENERATE"
