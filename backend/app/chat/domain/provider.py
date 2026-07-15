"""AI course provider boundary."""

from typing import Protocol

from app.chat.domain.entities import AiCoursePlan, AiCourseRequest


class AiCourseProvider(Protocol):
    async def generate(self, request: AiCourseRequest) -> AiCoursePlan:
        """Generate or revise a course using only supplied SQLite candidate IDs."""
