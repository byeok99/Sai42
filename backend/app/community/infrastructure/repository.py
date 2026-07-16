"""SQLAlchemy read/write adapter for community posts, likes, and masters."""

from dataclasses import dataclass

from sqlalchemy import exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.infrastructure.models import UserProfile
from app.community.domain.query import CommunityPostCriteria
from app.community.infrastructure.models import CommunityLike, CommunityPost
from app.course.infrastructure.models import DateCourse, DateCoursePlace


@dataclass(frozen=True, slots=True)
class CommunityPostRow:
    post: CommunityPost
    course: DateCourse
    like_count: int
    liked_by_me: bool


class CommunityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _base_query(profile_id: str | None = None):
        like_counts = (
            select(
                CommunityLike.community_post_id.label("post_id"),
                func.count(CommunityLike.id).label("like_count"),
            )
            .group_by(CommunityLike.community_post_id)
            .subquery()
        )
        liked = (
            exists().where(
                CommunityLike.community_post_id == CommunityPost.id,
                CommunityLike.profile_id == profile_id,
            )
            if profile_id
            else False
        )
        course_like_count = func.coalesce(like_counts.c.like_count, 0).label("course_like_count")
        return (
            select(
                CommunityPost,
                DateCourse,
                course_like_count,
                liked,
            )
            .join(DateCourse, DateCourse.id == CommunityPost.date_course_id)
            .outerjoin(like_counts, like_counts.c.post_id == CommunityPost.id)
        )

    async def list_published(
        self,
        criteria: CommunityPostCriteria,
        *,
        profile_id: str | None,
        offset: int,
        limit: int,
    ) -> tuple[list[CommunityPostRow], int]:
        query = self._base_query(profile_id).where(CommunityPost.status == "PUBLISHED")
        if criteria.districts:
            query = query.where(DateCourse.main_district.in_([v.value for v in criteria.districts]))
        if criteria.time_slots:
            query = query.where(DateCourse.time_slot.in_([v.value for v in criteria.time_slots]))
        if criteria.space_types:
            query = query.where(DateCourse.space_type.in_([v.value for v in criteria.space_types]))
        if criteria.densities:
            query = query.where(
                DateCourse.schedule_density.in_([v.value for v in criteria.densities])
            )
        if criteria.moods:
            query = query.where(
                or_(*(DateCourse.moods_json.contains(f'"{v.value}"') for v in criteria.moods))
            )
        if criteria.activities:
            query = query.where(
                or_(
                    *(
                        DateCourse.activities_json.contains(f'"{v.value}"')
                        for v in criteria.activities
                    )
                )
            )
        total = await self.session.scalar(
            select(func.count()).select_from(query.order_by(None).subquery())
        )
        like_count_expression = query.selected_columns.course_like_count
        if criteria.sort.value == "POPULAR":
            query = query.order_by(
                like_count_expression.desc(),
                CommunityPost.published_at.desc(),
                CommunityPost.id,
            )
        else:
            query = query.order_by(CommunityPost.published_at.desc(), CommunityPost.id)
        rows = (await self.session.execute(query.offset(offset).limit(limit))).all()
        return (
            [CommunityPostRow(row[0], row[1], int(row[2]), bool(row[3])) for row in rows],
            total or 0,
        )

    async def find_published(
        self, post_id: str, *, profile_id: str | None
    ) -> CommunityPostRow | None:
        row = (
            await self.session.execute(
                self._base_query(profile_id).where(
                    CommunityPost.id == post_id,
                    CommunityPost.status == "PUBLISHED",
                )
            )
        ).one_or_none()
        return CommunityPostRow(row[0], row[1], int(row[2]), bool(row[3])) if row else None

    async def find_post(self, post_id: str) -> CommunityPost | None:
        return await self.session.get(CommunityPost, post_id)

    async def find_post_by_course(self, course_id: str) -> CommunityPost | None:
        return await self.session.scalar(
            select(CommunityPost).where(CommunityPost.date_course_id == course_id)
        )

    async def find_course(self, course_id: str) -> DateCourse | None:
        return await self.session.get(DateCourse, course_id)

    async def place_heart_totals(self, course_ids: set[str]) -> dict[str, int]:
        if not course_ids:
            return {}
        course_contents = (
            select(DateCoursePlace.date_course_id, DateCoursePlace.content_id)
            .where(
                DateCoursePlace.date_course_id.in_(course_ids),
                DateCoursePlace.content_id.is_not(None),
            )
            .subquery()
        )
        global_hearts = (
            select(
                DateCoursePlace.content_id,
                func.count(DateCoursePlace.id).label("heart_count"),
            )
            .where(DateCoursePlace.hearted == 1, DateCoursePlace.content_id.is_not(None))
            .group_by(DateCoursePlace.content_id)
            .subquery()
        )
        rows = await self.session.execute(
            select(
                course_contents.c.date_course_id,
                func.coalesce(func.sum(global_hearts.c.heart_count), 0),
            )
            .outerjoin(global_hearts, global_hearts.c.content_id == course_contents.c.content_id)
            .group_by(course_contents.c.date_course_id)
        )
        return {course_id: int(total) for course_id, total in rows}

    async def find_like(self, profile_id: str, post_id: str) -> CommunityLike | None:
        return await self.session.scalar(
            select(CommunityLike).where(
                CommunityLike.profile_id == profile_id,
                CommunityLike.community_post_id == post_id,
            )
        )

    async def like_count(self, post_id: str) -> int:
        return (
            await self.session.scalar(
                select(func.count(CommunityLike.id)).where(
                    CommunityLike.community_post_id == post_id
                )
            )
            or 0
        )

    async def add_like(self, like: CommunityLike) -> None:
        self.session.add(like)
        await self.session.flush()

    async def delete_like(self, like: CommunityLike) -> None:
        await self.session.delete(like)
        await self.session.flush()

    async def list_masters(self, limit: int) -> list[tuple[str, str, int, int]]:
        rows = await self.session.execute(
            select(
                UserProfile.id,
                CommunityPost.author_nickname_snapshot,
                func.count(func.distinct(CommunityPost.id)).label("post_count"),
                func.count(CommunityLike.id).label("like_count"),
            )
            .join(CommunityPost, CommunityPost.author_profile_id == UserProfile.id)
            .outerjoin(CommunityLike, CommunityLike.community_post_id == CommunityPost.id)
            .where(CommunityPost.status == "PUBLISHED")
            .group_by(UserProfile.id, CommunityPost.author_nickname_snapshot)
            .order_by(
                func.count(CommunityLike.id).desc(),
                func.count(func.distinct(CommunityPost.id)).desc(),
                CommunityPost.author_nickname_snapshot,
            )
            .limit(limit)
        )
        return [(row[0], row[1], int(row[2]), int(row[3])) for row in rows]

    async def flush(self) -> None:
        await self.session.flush()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
