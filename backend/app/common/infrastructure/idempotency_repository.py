"""SQLAlchemy adapter for durable HTTP idempotency claims."""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.infrastructure.models import IdempotencyRecord


class IdempotencyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def find(
        self,
        *,
        scope_key: str,
        method: str,
        path: str,
        key: str,
    ) -> IdempotencyRecord | None:
        return await self.session.scalar(
            select(IdempotencyRecord).where(
                IdempotencyRecord.scope_key == scope_key,
                IdempotencyRecord.http_method == method,
                IdempotencyRecord.request_path == path,
                IdempotencyRecord.idempotency_key == key,
            )
        )

    async def add(self, record: IdempotencyRecord) -> None:
        self.session.add(record)
        await self.session.flush()

    async def delete_by_id(self, record_id: str) -> None:
        await self.session.execute(
            delete(IdempotencyRecord).where(IdempotencyRecord.id == record_id)
        )

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
