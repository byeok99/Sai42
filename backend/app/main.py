"""FastAPI application bootstrap."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.application.rate_limiter import AuthRateLimiter
from app.auth.presentation.router import router as auth_router
from app.common.presentation.dependencies import validate_optional_request_id
from app.common.presentation.exception_handlers import register_exception_handlers
from app.common.presentation.middleware import TraceIdMiddleware
from app.common.presentation.responses import DEFAULT_ERROR_RESPONSES
from app.common.presentation.router import router as common_router
from app.community.presentation.router import router as community_router
from app.config import Settings, get_settings
from app.course.presentation.router import router as current_course_router
from app.database import dispose_database_engine
from app.history.presentation.router import router as history_router
from app.place.presentation.router import router as place_router
from app.ranking.presentation.router import router as ranking_router

OPENAPI_TAGS = [
    {
        "name": "Common",
        "description": "서버 상태와 API 공통 선택 옵션을 제공합니다.",
    },
    {
        "name": "Identity",
        "description": "익명 프로필 등록, 검증과 요청별 헤더 인증을 제공합니다.",
    },
    {
        "name": "Place",
        "description": "SQLite에 적재된 공공 장소 검색, 상세 및 주변 장소 조회를 제공합니다.",
    },
    {
        "name": "Current",
        "description": "현재 데이트 코스 조회, 순차 진행, 장소 하트와 종료를 제공합니다.",
    },
    {
        "name": "Community",
        "description": "완료 코스 공개, 조회, 수정, 좋아요와 코스 복사를 제공합니다.",
    },
    {
        "name": "Ranking",
        "description": "공개 코스 기반 데이트 마스터 집계를 제공합니다.",
    },
    {
        "name": "History",
        "description": "본인의 완료 코스 조회와 새로운 현재 코스 재진행을 제공합니다.",
    },
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
    application.state.auth_rate_limiter = AuthRateLimiter(
        max_attempts=resolved_settings.auth_rate_limit_max_attempts,
        window_seconds=resolved_settings.auth_rate_limit_window_seconds,
    )

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
    application.include_router(auth_router, prefix=resolved_settings.api_prefix)
    application.include_router(place_router, prefix=resolved_settings.api_prefix)
    application.include_router(current_course_router, prefix=resolved_settings.api_prefix)
    application.include_router(community_router, prefix=resolved_settings.api_prefix)
    application.include_router(ranking_router, prefix=resolved_settings.api_prefix)
    application.include_router(history_router, prefix=resolved_settings.api_prefix)
    return application


app = create_app()
