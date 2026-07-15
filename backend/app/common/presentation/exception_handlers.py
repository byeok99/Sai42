"""Global exception-to-ErrorResponseDto conversion."""

import logging
from typing import Any

import httpx
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from pydantic.alias_generators import to_camel
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.common.application.dto import ErrorDetailDto
from app.common.application.errors import BusinessException
from app.common.presentation.middleware import request_trace_id
from app.common.presentation.responses import error_response

logger = logging.getLogger(__name__)

SENSITIVE_FIELD_TOKENS = frozenset({"password", "x-user-password", "authorization", "secret"})


def _field_name(location: tuple[Any, ...]) -> str | None:
    parts = [str(part) for part in location]
    if parts and parts[0] in {"body", "path", "query", "header", "cookie"}:
        parts = parts[1:]
    if not parts:
        return None
    return ".".join(to_camel(part) for part in parts)


def _is_sensitive(location: tuple[Any, ...]) -> bool:
    return any(str(part).lower() in SENSITIVE_FIELD_TOKENS for part in location)


def _safe_rejected_value(value: Any, *, sensitive: bool) -> Any | None:
    if sensitive or isinstance(value, (dict, list, tuple, set, bytes)):
        return None
    if isinstance(value, str):
        return value[:200]
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return None


def _validation_errors(exception: RequestValidationError) -> list[ErrorDetailDto]:
    details: list[ErrorDetailDto] = []
    for error in exception.errors():
        location = tuple(error.get("loc", ()))
        reason = str(error.get("type", "VALIDATION_ERROR")).replace(".", "_").upper()
        details.append(
            ErrorDetailDto(
                field=_field_name(location),
                reason=reason,
                rejected_value=_safe_rejected_value(
                    error.get("input"),
                    sensitive=_is_sensitive(location),
                ),
            )
        )
    return details


async def handle_business_exception(request: Request, exception: BusinessException):
    return error_response(
        status_code=exception.status_code,
        code=exception.code,
        message=exception.message,
        errors=exception.errors,
        trace_id=request_trace_id(request),
    )


async def handle_validation_exception(request: Request, exception: RequestValidationError):
    json_is_invalid = any(error.get("type") == "json_invalid" for error in exception.errors())
    message = "JSON 요청 형식을 확인해 주세요." if json_is_invalid else "요청 값을 확인해 주세요."
    return error_response(
        status_code=400 if json_is_invalid else 422,
        code="COMMON_BAD_REQUEST" if json_is_invalid else "COMMON_VALIDATION_ERROR",
        message=message,
        errors=_validation_errors(exception),
        trace_id=request_trace_id(request),
    )


async def handle_http_exception(request: Request, exception: StarletteHTTPException):
    messages = {
        400: "잘못된 요청입니다.",
        401: "인증 정보가 필요합니다.",
        403: "요청한 리소스에 접근할 수 없습니다.",
        404: "요청한 리소스를 찾을 수 없습니다.",
        405: "허용되지 않은 HTTP 메서드입니다.",
        429: "요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.",
    }
    codes = {
        400: "COMMON_BAD_REQUEST",
        404: "COMMON_NOT_FOUND",
        429: "COMMON_RATE_LIMIT_EXCEEDED",
    }
    return error_response(
        status_code=exception.status_code,
        code=codes.get(exception.status_code, "COMMON_BAD_REQUEST"),
        message=messages.get(exception.status_code, "요청을 처리할 수 없습니다."),
        trace_id=request_trace_id(request),
    )


async def handle_sqlalchemy_exception(request: Request, exception: SQLAlchemyError):
    trace_id = request_trace_id(request)
    logger.error(
        "Database error (trace_id=%s, exception_type=%s)", trace_id, type(exception).__name__
    )
    return error_response(
        status_code=500,
        code="COMMON_INTERNAL_SERVER_ERROR",
        message="요청 처리 중 오류가 발생했습니다.",
        trace_id=trace_id,
    )


async def handle_external_timeout(request: Request, exception: httpx.TimeoutException):
    trace_id = request_trace_id(request)
    logger.warning("External service timeout (trace_id=%s): %s", trace_id, type(exception).__name__)
    return error_response(
        status_code=503,
        code="COMMON_EXTERNAL_SERVICE_UNAVAILABLE",
        message="외부 서비스가 일시적으로 응답하지 않습니다.",
        trace_id=trace_id,
    )


async def handle_external_http_error(request: Request, exception: httpx.HTTPError):
    trace_id = request_trace_id(request)
    logger.warning("External service error (trace_id=%s): %s", trace_id, type(exception).__name__)
    return error_response(
        status_code=502,
        code="COMMON_EXTERNAL_SERVICE_ERROR",
        message="외부 서비스 응답을 처리할 수 없습니다.",
        trace_id=trace_id,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Install the common error contract for all current and future routes."""
    app.add_exception_handler(BusinessException, handle_business_exception)
    app.add_exception_handler(RequestValidationError, handle_validation_exception)
    app.add_exception_handler(StarletteHTTPException, handle_http_exception)
    app.add_exception_handler(SQLAlchemyError, handle_sqlalchemy_exception)
    app.add_exception_handler(httpx.TimeoutException, handle_external_timeout)
    app.add_exception_handler(httpx.HTTPError, handle_external_http_error)
