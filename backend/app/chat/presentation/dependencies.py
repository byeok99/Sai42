"""AI course provider composition dependencies."""

from typing import Annotated

from fastapi import Depends

from app.chat.domain.provider import AiCourseProvider
from app.chat.infrastructure.openai_provider import OpenAiCourseProvider
from app.config import Settings, get_request_settings


def get_ai_course_provider(
    settings: Annotated[Settings, Depends(get_request_settings)],
) -> AiCourseProvider | None:
    if settings.openai_api_key is None:
        return None
    api_key = settings.openai_api_key.get_secret_value().strip()
    if not api_key:
        return None
    return OpenAiCourseProvider(
        api_key=api_key,
        model=settings.openai_model,
        timeout_seconds=settings.openai_timeout_seconds,
        max_retries=settings.openai_max_retries,
    )
