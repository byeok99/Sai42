"""SQLAlchemy persistence operations for current DateCourse use cases."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.community.infrastructure.models import CommunityPost
from app.course.infrastructure.models import DateCourse, DateCoursePlace


class DateCourseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def find_active_course(self, profile_id: str) -> DateCourse | None:
        return await self.session.scalar(
            select(DateCourse).where(
                DateCourse.profile_id == profile_id,
                DateCourse.status == "ACTIVE",
            )
        )

    async def list_course_places(self, course_id: str) -> list[DateCoursePlace]:
        return list(
            await self.session.scalars(
                select(DateCoursePlace)
                .where(DateCoursePlace.date_course_id == course_id)
                .order_by(DateCoursePlace.order_no)
            )
        )

    async def find_course_place(self, course_place_id: str) -> DateCoursePlace | None:
        return await self.session.get(DateCoursePlace, course_place_id)

    async def heart_counts(self, content_ids: set[str]) -> dict[str, int]:
        if not content_ids:
            return {}
        rows = await self.session.execute(
            select(DateCoursePlace.content_id, func.count(DateCoursePlace.id))
            .where(
                DateCoursePlace.content_id.in_(content_ids),
                DateCoursePlace.hearted == 1,
            )
            .group_by(DateCoursePlace.content_id)
        )
        return {content_id: count for content_id, count in rows if content_id is not None}

    async def add_community_post(self, post: CommunityPost) -> None:
        self.session.add(post)
        await self.session.flush()

    async def flush(self) -> None:
        await self.session.flush()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
