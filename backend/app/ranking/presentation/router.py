"""Public ranking aggregate routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.application.dto import BaseDto
from app.common.presentation.responses import success_response
from app.community.application.dto import DateMastersDto
from app.community.application.service import CommunityService
from app.community.infrastructure.repository import CommunityRepository
from app.database import get_database_session

router = APIRouter(prefix="/rankings", tags=["Ranking"])


@router.get("/masters", response_model=BaseDto[DateMastersDto], summary="데이트 마스터 랭킹")
async def get_date_masters(
    session: Annotated[AsyncSession, Depends(get_database_session)],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> BaseDto[DateMastersDto]:
    return success_response(await CommunityService(CommunityRepository(session)).get_masters(limit))
