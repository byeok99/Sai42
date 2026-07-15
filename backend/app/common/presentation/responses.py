"""Factories and OpenAPI metadata for the common response envelopes."""

from typing import Any, TypeVar
from uuid import UUID

from fastapi.responses import JSONResponse

from app.common.application.dto import BaseDto, ErrorDetailDto, ErrorResponseDto, PageMetaDto
from app.common.domain.time import now_seoul
from app.common.presentation.middleware import current_trace_id

DataT = TypeVar("DataT")


def success_response(  # noqa: UP047 - keep TypeVar aligned with the Pydantic generic DTO
    data: DataT | None,
    *,
    code: str = "COMMON_OK",
    message: str = "요청이 성공적으로 처리되었습니다.",
    meta: PageMetaDto | None = None,
) -> BaseDto[DataT]:
    """Build a success envelope using the active request trace."""
    return BaseDto[DataT](
        success=True,
        code=code,
        message=message,
        data=data,
        meta=meta,
        timestamp=now_seoul(),
        trace_id=current_trace_id(),
    )


def error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    errors: list[ErrorDetailDto] | None = None,
    trace_id: UUID | None = None,
) -> JSONResponse:
    """Build a serialized ErrorResponseDto JSON response."""
    body = ErrorResponseDto(
        success=False,
        code=code,
        message=message,
        errors=errors or [],
        timestamp=now_seoul(),
        trace_id=trace_id or current_trace_id(),
    )
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(mode="json", by_alias=True),
    )


ERROR_RESPONSE_EXAMPLE: dict[str, Any] = {
    "success": False,
    "code": "COMMON_VALIDATION_ERROR",
    "message": "요청 값을 확인해 주세요.",
    "errors": [
        {
            "field": "page",
            "reason": "GREATER_THAN_EQUAL",
            "rejectedValue": 0,
        }
    ],
    "timestamp": "2026-07-15T14:31:00+09:00",
    "traceId": "b4cd1da0-3c6c-4e80-a4ea-d74f0edc46e1",
}

DEFAULT_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {
        "model": ErrorResponseDto,
        "description": "JSON 파싱 또는 요청 조합 오류",
        "content": {"application/json": {"example": ERROR_RESPONSE_EXAMPLE}},
    },
    422: {
        "model": ErrorResponseDto,
        "description": "필드 검증 또는 업무 규칙 위반",
        "content": {"application/json": {"example": ERROR_RESPONSE_EXAMPLE}},
    },
    500: {
        "model": ErrorResponseDto,
        "description": "서버 내부 오류",
        "content": {"application/json": {"example": ERROR_RESPONSE_EXAMPLE}},
    },
}
