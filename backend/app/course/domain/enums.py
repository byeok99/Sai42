"""DateCourse lifecycle values fixed by the API and database contracts."""

from enum import StrEnum


class DateCourseStatus(StrEnum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"


class DateCourseSourceType(StrEnum):
    AI_CHAT = "AI_CHAT"
    RANKING_COPY = "RANKING_COPY"
    HISTORY_RESTART = "HISTORY_RESTART"
