"""Identity application use cases."""

import hmac
import re
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError

from app.auth.application.dto import (
    CreateProfileRequestDto,
    MyProfileDto,
    NicknameSuggestionsDto,
    ProfileCreatedDto,
    ProfileVerifiedDto,
    VerifyProfileRequestDto,
)
from app.auth.application.rate_limiter import AuthRateLimiter
from app.auth.domain.entities import AuthenticatedProfile
from app.auth.domain.nickname import (
    nickname_candidates,
    normalize_nickname,
    prepare_nickname,
)
from app.auth.infrastructure.models import UserProfile
from app.auth.infrastructure.repository import AuthRepository, ProfileStats
from app.common.application.errors import BusinessException
from app.common.domain.time import now_seoul

PASSWORD_PATTERN = re.compile(r"^\d{4}$")


def _as_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


class AuthService:
    """Register and authenticate anonymous profiles without issuing tokens."""

    def __init__(self, repository: AuthRepository, rate_limiter: AuthRateLimiter) -> None:
        self.repository = repository
        self.rate_limiter = rate_limiter

    async def get_nickname_suggestions(
        self,
        *,
        count: int,
        seed: str | None,
    ) -> NicknameSuggestionsDto:
        normalized_seed = prepare_nickname(seed) if seed else None
        title_limit = max(200, count * 30)
        titles = await self.repository.list_recommendable_place_titles(
            limit=title_limit,
            seed=normalized_seed,
        )
        if len(titles) < count:
            fallback_titles = await self.repository.list_recommendable_place_titles(
                limit=title_limit,
            )
            titles.extend(title for title in fallback_titles if title not in titles)

        used_nicknames = await self.repository.list_normalized_nicknames()
        suggestions: list[str] = []
        emitted: set[str] = set()
        for title in titles:
            for candidate in nickname_candidates(title, normalized_seed):
                normalized = normalize_nickname(candidate)
                if normalized in used_nicknames or normalized in emitted:
                    continue
                suggestions.append(candidate)
                emitted.add(normalized)
                if len(suggestions) == count:
                    return NicknameSuggestionsDto(suggestions=suggestions)

        return NicknameSuggestionsDto(suggestions=suggestions)

    async def create_profile(
        self,
        request: CreateProfileRequestDto,
        *,
        client_ip: str,
    ) -> ProfileCreatedDto:
        await self.rate_limiter.record_attempt(f"register:{client_ip}")
        nickname_normalized = normalize_nickname(request.nickname)
        if await self.repository.find_active_by_normalized_nickname(nickname_normalized):
            self._raise_duplicate_nickname()

        now = now_seoul().isoformat()
        profile = UserProfile(
            id=str(uuid4()),
            nickname=request.nickname,
            nickname_normalized=nickname_normalized,
            password=request.password,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )
        try:
            await self.repository.add(profile)
            await self.repository.commit()
        except IntegrityError:
            await self.repository.rollback()
            self._raise_duplicate_nickname()

        stats = await self.repository.get_profile_stats(profile.id)
        return self._created_dto(profile, stats)

    async def verify_profile(
        self,
        request: VerifyProfileRequestDto,
        *,
        client_ip: str,
    ) -> ProfileVerifiedDto:
        nickname_normalized = normalize_nickname(request.nickname)
        limit_key = f"verify:{client_ip}:{nickname_normalized}"
        await self.rate_limiter.ensure_allowed(limit_key)
        profile = await self.repository.find_active_by_normalized_nickname(nickname_normalized)
        if profile is None or not hmac.compare_digest(profile.password, request.password):
            await self.rate_limiter.record_failure(limit_key)
            self._raise_invalid_credentials()

        await self.rate_limiter.reset(limit_key)
        stats = await self.repository.get_profile_stats(profile.id)
        return ProfileVerifiedDto(
            profile_id=UUID(profile.id),
            nickname=profile.nickname,
            has_active_date_course=stats.has_active_date_course,
            completed_date_course_count=stats.completed_date_course_count,
            verified_at=now_seoul(),
        )

    async def authenticate_headers(
        self,
        *,
        profile_id_header: str | None,
        password_header: str | None,
        client_ip: str,
    ) -> AuthenticatedProfile:
        raw_scope = (profile_id_header or "missing")[:64]
        limit_key = f"headers:{client_ip}:{raw_scope}"
        await self.rate_limiter.ensure_allowed(limit_key)

        if profile_id_header is None or password_header is None:
            await self.rate_limiter.record_failure(limit_key)
            raise BusinessException(
                status_code=401,
                code="AUTH_CREDENTIALS_REQUIRED",
                message="프로필 ID와 비밀번호가 필요합니다.",
            )

        try:
            parsed_profile_id = UUID(profile_id_header)
            canonical_profile_id = str(parsed_profile_id)
            if parsed_profile_id.version != 4 or canonical_profile_id != profile_id_header.lower():
                raise ValueError
        except (ValueError, AttributeError):
            await self.rate_limiter.record_failure(limit_key)
            raise BusinessException(
                status_code=401,
                code="AUTH_INVALID_PROFILE_ID_FORMAT",
                message="프로필 ID 형식을 확인해 주세요.",
            ) from None

        profile = await self.repository.find_active_by_id(canonical_profile_id)
        password_is_valid = (
            PASSWORD_PATTERN.fullmatch(password_header) is not None
            and profile is not None
            and hmac.compare_digest(profile.password, password_header)
        )
        if not password_is_valid:
            await self.rate_limiter.record_failure(limit_key)
            self._raise_invalid_credentials()

        await self.rate_limiter.reset(limit_key)
        return AuthenticatedProfile(
            id=profile.id,
            nickname=profile.nickname,
            created_at=profile.created_at,
        )

    async def get_my_profile(self, profile: AuthenticatedProfile) -> MyProfileDto:
        stats = await self.repository.get_profile_stats(profile.id)
        return MyProfileDto(
            profile_id=UUID(profile.id),
            nickname=profile.nickname,
            has_active_date_course=stats.has_active_date_course,
            completed_date_course_count=stats.completed_date_course_count,
            published_course_count=stats.published_course_count,
            created_at=_as_datetime(profile.created_at),
        )

    @staticmethod
    def _created_dto(profile: UserProfile, stats: ProfileStats) -> ProfileCreatedDto:
        return ProfileCreatedDto(
            profile_id=UUID(profile.id),
            nickname=profile.nickname,
            has_active_date_course=stats.has_active_date_course,
            completed_date_course_count=stats.completed_date_course_count,
            created_at=_as_datetime(profile.created_at),
        )

    @staticmethod
    def _raise_duplicate_nickname() -> None:
        raise BusinessException(
            status_code=409,
            code="AUTH_NICKNAME_ALREADY_EXISTS",
            message="이미 사용 중인 닉네임입니다.",
        )

    @staticmethod
    def _raise_invalid_credentials() -> None:
        raise BusinessException(
            status_code=401,
            code="AUTH_INVALID_CREDENTIALS",
            message="사용자 정보 또는 비밀번호가 올바르지 않습니다.",
        )
