"""SQLAlchemy repository for the Identity domain."""

from dataclasses import dataclass

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.infrastructure.models import UserProfile
from app.place.infrastructure.models import Place


@dataclass(frozen=True, slots=True)
class ProfileStats:
    """Profile aggregates available before course tables are introduced."""

    has_active_date_course: bool = False
    completed_date_course_count: int = 0
    published_course_count: int = 0


class AuthRepository:
    """Own Identity persistence and public-place title reads."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def find_active_by_id(self, profile_id: str) -> UserProfile | None:
        result = await self.session.execute(
            select(UserProfile).where(
                UserProfile.id == profile_id,
                UserProfile.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def find_active_by_normalized_nickname(
        self,
        nickname_normalized: str,
    ) -> UserProfile | None:
        result = await self.session.execute(
            select(UserProfile).where(
                UserProfile.nickname_normalized == nickname_normalized,
                UserProfile.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_normalized_nicknames(self) -> set[str]:
        result = await self.session.execute(select(UserProfile.nickname_normalized))
        return set(result.scalars())

    async def list_recommendable_place_titles(
        self,
        *,
        limit: int,
        seed: str | None = None,
    ) -> list[str]:
        statement = select(Place.title).where(Place.is_recommendable == 1)
        if seed:
            statement = statement.where(
                or_(
                    Place.title.contains(seed, autoescape=True),
                    Place.address.contains(seed, autoescape=True),
                    Place.description.contains(seed, autoescape=True),
                )
            )
        result = await self.session.execute(statement.order_by(Place.content_id).limit(limit))
        return list(result.scalars())

    async def add(self, profile: UserProfile) -> None:
        self.session.add(profile)
        await self.session.flush()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

    async def get_profile_stats(self, _: str) -> ProfileStats:
        """Return factual zero aggregates until the course/community tables exist."""
        return ProfileStats()
