"""Database access adapter for the Common domain."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class CommonRepository:
    """Read-only repository for operational database checks."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def database_is_available(self) -> bool:
        """Execute the smallest useful connectivity query."""
        result = await self.session.execute(text("SELECT 1"))
        return result.scalar_one() == 1
