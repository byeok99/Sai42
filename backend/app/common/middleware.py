"""Request tracing middleware."""

import logging
from contextvars import ContextVar, Token
from uuid import UUID, uuid4

from starlette.datastructures import Headers, MutableHeaders
from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

_trace_id_context: ContextVar[UUID | None] = ContextVar("trace_id", default=None)
logger = logging.getLogger(__name__)


def _parse_or_create_trace_id(value: str | None) -> UUID:
    if value is not None:
        try:
            return UUID(value)
        except ValueError:
            pass
    return uuid4()


def current_trace_id() -> UUID:
    """Return the request trace ID, creating one only outside request scope."""
    return _trace_id_context.get() or uuid4()


def request_trace_id(request: Request) -> UUID:
    """Read the trace ID persisted on the ASGI request state."""
    value = getattr(request.state, "trace_id", None)
    if isinstance(value, UUID):
        return value
    return current_trace_id()


class TraceIdMiddleware:
    """Propagate a valid X-Request-Id or generate a UUID for the request."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        trace_id = _parse_or_create_trace_id(headers.get("x-request-id"))
        scope.setdefault("state", {})["trace_id"] = trace_id
        token: Token[UUID | None] = _trace_id_context.set(trace_id)
        response_started = False

        async def send_with_trace_id(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
                response_headers = MutableHeaders(scope=message)
                response_headers["X-Request-Id"] = str(trace_id)
            await send(message)

        try:
            await self.app(scope, receive, send_with_trace_id)
        except Exception as exception:
            if response_started:
                raise
            logger.error(
                "Unhandled error (trace_id=%s, exception_type=%s)",
                trace_id,
                type(exception).__name__,
            )
            from app.common.responses import error_response

            response = error_response(
                status_code=500,
                code="COMMON_INTERNAL_SERVER_ERROR",
                message="요청 처리 중 오류가 발생했습니다.",
                trace_id=trace_id,
            )
            await response(scope, receive, send_with_trace_id)
        finally:
            _trace_id_context.reset(token)
