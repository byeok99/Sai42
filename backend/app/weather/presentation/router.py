"""Public weather summary HTTP route with optional profile authentication."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.auth.domain.entities import AuthenticatedProfile
from app.auth.presentation.dependencies import get_optional_current_profile
from app.common.application.dto import BaseDto
from app.common.domain.enums import District, TimeSlot
from app.common.presentation.responses import success_response
from app.weather.application.dto import WeatherSummaryDto
from app.weather.application.service import WeatherService
from app.weather.domain.provider import WeatherProvider
from app.weather.presentation.dependencies import get_weather_provider

router = APIRouter(prefix="/weather", tags=["Weather"])


@router.get(
    "",
    response_model=BaseDto[WeatherSummaryDto],
    summary="대전 지역 날씨 조회",
    description=(
        "Open-Meteo 시간별 예보를 조회합니다. 공급자 장애 시에도 HTTP 200과 "
        "available=false를 반환합니다."
    ),
)
async def get_weather(
    _profile: Annotated[AuthenticatedProfile | None, Depends(get_optional_current_profile)],
    provider: Annotated[WeatherProvider | None, Depends(get_weather_provider)],
    target_date: Annotated[date, Query(alias="date")],
    district: Annotated[District, Query()],
    time_slot: Annotated[TimeSlot, Query(alias="timeSlot")],
) -> BaseDto[WeatherSummaryDto]:
    return success_response(
        await WeatherService(provider).get_weather(
            target_date=target_date,
            district=district,
            time_slot=time_slot,
        )
    )
