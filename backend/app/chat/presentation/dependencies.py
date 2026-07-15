"""AI course provider composition dependencies."""

from typing import Annotated

from fastapi import Depends, Request

from app.chat.domain.provider import AiCourseProvider
from app.chat.infrastructure.openai_provider import OpenAiCourseProvider
from app.config import Settings, get_request_settings


async def get_ai_course_provider(
    request: Request,
    settings: Annotated[Settings, Depends(get_request_settings)],
) -> AiCourseProvider | None:
    provider = getattr(request.app.state, "ai_course_provider", None)
    if provider is not None:
        return provider
    if settings.openai_api_key is None:
        return None
    api_key = settings.openai_api_key.get_secret_value().strip()
    if not api_key:
        return None
    async with request.app.state.ai_course_provider_lock:
        provider = getattr(request.app.state, "ai_course_provider", None)
        if provider is None:
            provider = OpenAiCourseProvider(
                api_key=api_key,
                model=settings.openai_model,
                timeout_seconds=settings.openai_timeout_seconds,
                max_retries=settings.openai_max_retries,
                reasoning_effort=settings.openai_reasoning_effort,
                prompt_cache_key=settings.openai_prompt_cache_key,
            )
            request.app.state.ai_course_provider = provider
    return provider
