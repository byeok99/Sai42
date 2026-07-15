"""Reusable execution boundary for Idempotency-Key protected writes."""

import hashlib
import json
from collections.abc import Awaitable, Callable
from datetime import timedelta
from typing import Any
from uuid import UUID, uuid4

from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.common.application.dto import BaseDto
from app.common.application.errors import BusinessException
from app.common.domain.time import now_seoul
from app.common.infrastructure.idempotency_repository import IdempotencyRepository
from app.common.infrastructure.models import IdempotencyRecord

ResponseFactory = Callable[[], Awaitable[BaseDto[Any]]]


class IdempotencyService:
    def __init__(self, repository: IdempotencyRepository) -> None:
        self.repository = repository

    @staticmethod
    def fingerprint(payload: dict[str, Any]) -> str:
        canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()

    async def execute(
        self,
        *,
        scope_key: str,
        method: str,
        path: str,
        key: UUID | None,
        request_fingerprint: str,
        status_code: int,
        response_factory: ResponseFactory,
    ) -> BaseDto[Any] | JSONResponse:
        if key is None:
            return await response_factory()
        canonical_key = str(key)
        existing = await self.repository.find(
            scope_key=scope_key,
            method=method,
            path=path,
            key=canonical_key,
        )
        if (
            existing is not None
            and existing.status == "PROCESSING"
            and existing.expires_at <= now_seoul().isoformat()
        ):
            await self.repository.delete_by_id(existing.id)
            await self.repository.commit()
            existing = None
        if existing is not None:
            return await self._existing_response(existing, request_fingerprint)

        now = now_seoul()
        record = IdempotencyRecord(
            id=str(uuid4()),
            scope_key=scope_key,
            http_method=method,
            request_path=path,
            idempotency_key=canonical_key,
            request_fingerprint=request_fingerprint,
            status="PROCESSING",
            response_status_code=None,
            response_body_json=None,
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
            expires_at=(now + timedelta(hours=24)).isoformat(),
        )
        try:
            await self.repository.add(record)
            await self.repository.commit()
        except IntegrityError:
            await self.repository.rollback()
            existing = await self.repository.find(
                scope_key=scope_key,
                method=method,
                path=path,
                key=canonical_key,
            )
            if existing is None:
                raise
            return await self._existing_response(existing, request_fingerprint)

        try:
            response = await response_factory()
            record.status = "COMPLETED"
            record.response_status_code = status_code
            record.response_body_json = json.dumps(
                response.model_dump(mode="json", by_alias=True),
                ensure_ascii=False,
                separators=(",", ":"),
            )
            record.updated_at = now_seoul().isoformat()
            await self.repository.commit()
            return response
        except Exception:
            await self.repository.rollback()
            await self.repository.delete_by_id(record.id)
            await self.repository.commit()
            raise

    @staticmethod
    async def _existing_response(
        record: IdempotencyRecord,
        request_fingerprint: str,
    ) -> JSONResponse:
        if record.request_fingerprint != request_fingerprint:
            raise BusinessException(
                status_code=409,
                code="COMMON_IDEMPOTENCY_KEY_REUSED",
                message="같은 멱등성 키를 다른 요청에 사용할 수 없습니다.",
            )
        if record.status == "PROCESSING":
            raise BusinessException(
                status_code=409,
                code="COMMON_IDEMPOTENCY_REQUEST_IN_PROGRESS",
                message="같은 요청이 처리 중입니다.",
            )
        return JSONResponse(
            status_code=record.response_status_code or 200,
            content=json.loads(record.response_body_json or "{}"),
        )
