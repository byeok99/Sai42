"""FastAPI dependencies for the Common presentation layer."""

from typing import Annotated
from uuid import UUID

from fastapi import Header


def validate_optional_request_id(
    request_id: Annotated[
        UUID | None,
        Header(
            alias="X-Request-Id",
            description="선택 요청 추적 UUID. 응답 traceId와 X-Request-Id에 반영됩니다.",
        ),
    ] = None,
) -> UUID | None:
    """Validate and document the optional request tracing header."""
    return request_id
