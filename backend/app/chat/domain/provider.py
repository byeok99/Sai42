"""AI course provider boundary."""

from typing import Protocol

from app.chat.domain.entities import AiChatTurn, AiCoursePlan, AiCourseRequest


class AiCourseProvider(Protocol):
    async def generate(self, request: AiCourseRequest) -> AiCoursePlan:
        """Generate an initial course using only supplied SQLite place IDs."""

    async def respond(self, request: AiCourseRequest) -> AiChatTurn:
        """Classify and answer a chat turn, optionally proposing a course edit."""
