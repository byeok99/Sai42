"""FastAPI application bootstrap."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.common.dependencies import validate_optional_request_id
from app.common.exception_handlers import register_exception_handlers
from app.common.middleware import TraceIdMiddleware
from app.common.responses import DEFAULT_ERROR_RESPONSES
from app.common.router import router as common_router
from app.config import Settings, get_settings
from app.database import dispose_database_engine

OPENAPI_TAGS = [
    {
        "name": "Common",
        "description": "서버 상태와 API 공통 선택 옵션을 제공합니다.",
    }
]


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Release database resources on graceful shutdown."""
    yield
    await dispose_database_engine()


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create a fully configured application for runtime and API tests."""
    resolved_settings = settings or get_settings()
    application = FastAPI(
        title=resolved_settings.app_name,
        version=resolved_settings.app_version,
        description=(
            "대전 공공데이터 기반 AI 데이트 코스 서비스 API입니다. "
            "모든 도메인 API는 공통 성공·실패 envelope를 사용합니다."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        openapi_tags=OPENAPI_TAGS,
        dependencies=[Depends(validate_optional_request_id)],
        responses=DEFAULT_ERROR_RESPONSES,
        lifespan=lifespan,
    )
    application.state.settings = resolved_settings

    application.add_middleware(TraceIdMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Content-Type",
            "X-Profile-Id",
            "X-User-Password",
            "X-Request-Id",
            "Idempotency-Key",
        ],
        expose_headers=["X-Request-Id"],
    )
    register_exception_handlers(application)
    application.include_router(common_router, prefix=resolved_settings.api_prefix)
    return application


app = create_app()
