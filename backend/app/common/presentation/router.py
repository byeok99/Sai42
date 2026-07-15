"""Public Common API routes."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.application.dto import BaseDto
from app.common.application.schemas import HealthDto, MetaOptionsDto
from app.common.application.service import CommonService
from app.common.infrastructure.repository import CommonRepository
from app.common.presentation.responses import success_response
from app.config import Settings, get_request_settings
from app.database import get_database_session

router = APIRouter(tags=["Common"])

HEALTH_SUCCESS_EXAMPLE: dict[str, Any] = {
    "success": True,
    "code": "COMMON_OK",
    "message": "요청이 성공적으로 처리되었습니다.",
    "data": {
        "status": "UP",
        "database": "UP",
        "aiProvider": "NOT_CONFIGURED",
        "weatherProvider": "NOT_CONFIGURED",
        "version": "0.1.0",
    },
    "meta": None,
    "timestamp": "2026-07-15T14:30:00+09:00",
    "traceId": "9bb43f9d-a680-42ca-93bf-8a87a91aaef2",
}

OPTIONS_SUCCESS_EXAMPLE: dict[str, Any] = {
    "success": True,
    "code": "COMMON_OK",
    "message": "요청이 성공적으로 처리되었습니다.",
    "data": {
        "timeSlots": [{"value": "MORNING", "label": "오전"}],
        "districts": [{"value": "YUSEONG_GU", "label": "유성구"}],
        "spaceTypes": [{"value": "INDOOR", "label": "실내"}],
        "moods": [{"value": "EMOTIONAL", "label": "감성적인"}],
        "activityTypes": [{"value": "FOOD", "label": "음식"}],
        "scheduleDensities": [{"value": "RELAXED", "label": "널널하게"}],
        "transportations": [{"value": "PUBLIC_TRANSIT", "label": "대중교통"}],
        "rankingSorts": [{"value": "POPULAR", "label": "인기순"}],
    },
    "meta": None,
    "timestamp": "2026-07-15T14:30:00+09:00",
    "traceId": "9bb43f9d-a680-42ca-93bf-8a87a91aaef2",
}


@router.get(
    "/health",
    response_model=BaseDto[HealthDto],
    summary="서버 상태 조회",
    description="서버와 SQLite 연결 및 외부 공급자 구성 상태를 확인합니다.",
    response_description="서버 상태",
    responses={
        200: {
            "description": "서버와 DB가 정상입니다.",
            "content": {"application/json": {"example": HEALTH_SUCCESS_EXAMPLE}},
        }
    },
)
async def get_health(
    session: Annotated[AsyncSession, Depends(get_database_session)],
    settings: Annotated[Settings, Depends(get_request_settings)],
) -> BaseDto[HealthDto]:
    """Return health data in the global success envelope."""
    service = CommonService(CommonRepository(session), settings)
    return success_response(await service.get_health())


@router.get(
    "/meta/options",
    response_model=BaseDto[MetaOptionsDto],
    summary="공통 선택 옵션 조회",
    description="데이트 조건과 랭킹 정렬에 사용하는 Enum과 표시명을 반환합니다.",
    response_description="공통 선택 옵션",
    responses={
        200: {
            "description": "선택 옵션을 반환합니다.",
            "content": {"application/json": {"example": OPTIONS_SUCCESS_EXAMPLE}},
        }
    },
)
async def get_meta_options() -> BaseDto[MetaOptionsDto]:
    """Return stable selector options without database state."""
    return success_response(CommonService.get_options())
