"""Framework-independent Identity domain entities."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AuthenticatedProfile:
    """An authenticated active profile safe to pass between application layers."""

    id: str
    nickname: str
    created_at: str
