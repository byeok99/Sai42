"""FastAPI dependencies for Identity authentication."""

from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.application.rate_limiter import AuthRateLimiter
from app.auth.application.service import AuthService
from app.auth.domain.entities import AuthenticatedProfile
from app.auth.infrastructure.repository import AuthRepository
from app.database import get_database_session


def get_auth_rate_limiter(request: Request) -> AuthRateLimiter:
    """Return the application-scoped single-worker auth limiter."""
    return request.app.state.auth_rate_limiter


def request_client_ip(request: Request) -> str:
    """Return the client address resolved by the ASGI server."""
    return request.client.host if request.client else "unknown"


async def get_current_profile(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_database_session)],
    rate_limiter: Annotated[AuthRateLimiter, Depends(get_auth_rate_limiter)],
    profile_id: Annotated[str | None, Header(alias="X-Profile-Id")] = None,
    password: Annotated[str | None, Header(alias="X-User-Password")] = None,
) -> AuthenticatedProfile:
    """Validate both auth headers and inject the active profile."""
    service = AuthService(AuthRepository(session), rate_limiter)
    return await service.authenticate_headers(
        profile_id_header=profile_id,
        password_header=password,
        client_ip=request_client_ip(request),
    )
