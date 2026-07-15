"""Application-level exceptions translated by global handlers."""

from app.common.application.dto import ErrorDetailDto


class BusinessException(Exception):
    """A safe, expected failure with an API error contract."""

    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        errors: list[ErrorDetailDto] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.errors = errors or []
