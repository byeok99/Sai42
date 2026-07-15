"""SQLAlchemy queries for a profile's completed course history."""

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.domain.enums import District
from app.course.infrastructure.models import DateCourse, DateCoursePlace


@dataclass(frozen=True, slots=True)
class HistoryCourseRow:
    course: DateCourse
    hearted_place_count: int
    total_place_count: int


class HistoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_completed(
        self,
        profile_id: str,
        *,
        year: int | None,
        month: int | None,
        district: District | None,
        offset: int,
        limit: int,
    ) -> tuple[list[HistoryCourseRow], int]:
        place_counts = (
            select(
                DateCoursePlace.date_course_id.label("course_id"),
                func.sum(DateCoursePlace.hearted).label("hearted_count"),
                func.count(DateCoursePlace.id).label("total_count"),
            )
            .group_by(DateCoursePlace.date_course_id)
            .subquery()
        )
        query = (
            select(
                DateCourse,
                func.coalesce(place_counts.c.hearted_count, 0),
                func.coalesce(place_counts.c.total_count, 0),
            )
            .outerjoin(place_counts, place_counts.c.course_id == DateCourse.id)
            .where(DateCourse.profile_id == profile_id, DateCourse.status == "COMPLETED")
        )
        if year is not None:
            query = query.where(func.substr(DateCourse.date, 1, 4) == f"{year:04d}")
        if month is not None:
            query = query.where(func.substr(DateCourse.date, 6, 2) == f"{month:02d}")
        if district is not None:
            query = query.where(DateCourse.main_district == district.value)
        total = await self.session.scalar(
            select(func.count()).select_from(query.order_by(None).subquery())
        )
        rows = (
            await self.session.execute(
                query.order_by(DateCourse.completed_at.desc(), DateCourse.id)
                .offset(offset)
                .limit(limit)
            )
        ).all()
        return (
            [HistoryCourseRow(row[0], int(row[1]), int(row[2])) for row in rows],
            total or 0,
        )

    async def find_course(self, course_id: str) -> DateCourse | None:
        return await self.session.get(DateCourse, course_id)
