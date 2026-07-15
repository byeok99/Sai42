"""SQLAlchemy queries over the stored TourAPI public place dataset."""

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.place.domain.constants import PLACE_CATEGORY_BY_CONTENT_TYPE_ID
from app.place.domain.query import PlaceSearchCriteria
from app.place.infrastructure.models import Place

CONTENT_TYPE_ID_BY_CATEGORY = {
    category: content_type_id
    for content_type_id, category in PLACE_CATEGORY_BY_CONTENT_TYPE_ID.items()
}


class PlaceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _filtered_query(criteria: PlaceSearchCriteria) -> Select[tuple[Place]]:
        query = select(Place).where(Place.is_recommendable == 1)
        if criteria.keyword:
            query = query.where(
                or_(
                    Place.title.contains(criteria.keyword, autoescape=True),
                    Place.address.contains(criteria.keyword, autoescape=True),
                )
            )
        if criteria.district:
            query = query.where(Place.district == criteria.district.value)
        if criteria.categories:
            content_type_ids = [
                CONTENT_TYPE_ID_BY_CATEGORY[category.value] for category in criteria.categories
            ]
            query = query.where(Place.content_type_id.in_(content_type_ids))
        if criteria.space_type:
            query = query.where(Place.space_type == criteria.space_type.value)
        if criteria.has_image is True:
            query = query.where(Place.image_url != "")
        elif criteria.has_image is False:
            query = query.where(Place.image_url == "")
        return query

    async def list_page(
        self,
        criteria: PlaceSearchCriteria,
        *,
        offset: int,
        limit: int,
    ) -> tuple[list[Place], int]:
        base_query = self._filtered_query(criteria)
        count = await self.session.scalar(
            select(func.count()).select_from(base_query.order_by(None).subquery())
        )
        result = await self.session.scalars(
            base_query.order_by(Place.title, Place.content_id).offset(offset).limit(limit)
        )
        return list(result), count or 0

    async def list_candidates(
        self,
        criteria: PlaceSearchCriteria,
        *,
        minimum_latitude: float,
        maximum_latitude: float,
        minimum_longitude: float,
        maximum_longitude: float,
    ) -> list[Place]:
        query = self._filtered_query(criteria).where(
            Place.latitude.between(minimum_latitude, maximum_latitude),
            Place.longitude.between(minimum_longitude, maximum_longitude),
        )
        return list(await self.session.scalars(query))

    async def find_by_content_id(self, content_id: str) -> Place | None:
        return await self.session.scalar(
            select(Place).where(
                Place.content_id == content_id,
                Place.is_recommendable == 1,
            )
        )
