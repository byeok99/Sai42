"""SQLAlchemy persistence operations for chat sessions and real place candidates."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat.infrastructure.models import ChatSession
from app.common.domain.enums import District
from app.place.infrastructure.models import Place


class ChatRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def find_session(self, session_id: str) -> ChatSession | None:
        return await self.session.get(ChatSession, session_id)

    async def list_recommendable_places(self, district: District) -> list[Place]:
        query = select(Place).where(Place.is_recommendable == 1)
        if district != District.ANY:
            query = query.where(Place.district == district.value)
        return list(await self.session.scalars(query.order_by(Place.content_id)))

    async def find_places(self, content_ids: set[str]) -> list[Place]:
        if not content_ids:
            return []
        return list(
            await self.session.scalars(
                select(Place).where(
                    Place.content_id.in_(content_ids),
                    Place.is_recommendable == 1,
                )
            )
        )

    async def add_session(self, chat_session: ChatSession) -> None:
        self.session.add(chat_session)
        await self.session.flush()

    async def flush(self) -> None:
        await self.session.flush()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
