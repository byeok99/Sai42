"""Common application use cases."""

from app.common.application.errors import BusinessException
from app.common.application.schemas import HealthDto, MetaOptionsDto, OptionDto
from app.common.domain.enums import (
    ActivityType,
    District,
    Mood,
    RankingSort,
    ScheduleDensity,
    SpaceType,
    TimeSlot,
    Transportation,
)
from app.common.infrastructure.repository import CommonRepository
from app.config import Settings


def _options(values: list[tuple[str, str]]) -> list[OptionDto]:
    return [OptionDto(value=value, label=label) for value, label in values]


class CommonService:
    """Application service for public operational metadata."""

    def __init__(self, repository: CommonRepository, settings: Settings) -> None:
        self.repository = repository
        self.settings = settings

    async def get_health(self) -> HealthDto:
        """Report service health while keeping unimplemented providers explicit."""
        if not await self.repository.database_is_available():
            raise BusinessException(
                status_code=500,
                code="COMMON_INTERNAL_SERVER_ERROR",
                message="데이터베이스 상태를 확인할 수 없습니다.",
            )
        return HealthDto(
            status="UP",
            database="UP",
            ai_provider="NOT_CONFIGURED",
            weather_provider="NOT_CONFIGURED",
            version=self.settings.app_version,
        )

    @staticmethod
    def get_options() -> MetaOptionsDto:
        """Return the API enum values with stable Korean labels."""
        return MetaOptionsDto(
            time_slots=_options(
                [
                    (TimeSlot.MORNING, "오전"),
                    (TimeSlot.AFTERNOON, "오후"),
                    (TimeSlot.FULL_DAY, "종일"),
                ]
            ),
            districts=_options(
                [
                    (District.DONG_GU, "동구"),
                    (District.JUNG_GU, "중구"),
                    (District.SEO_GU, "서구"),
                    (District.YUSEONG_GU, "유성구"),
                    (District.DAEDEOK_GU, "대덕구"),
                    (District.ANY, "상관없음"),
                ]
            ),
            space_types=_options(
                [
                    (SpaceType.INDOOR, "실내"),
                    (SpaceType.OUTDOOR, "실외"),
                    (SpaceType.ANY, "상관없음"),
                ]
            ),
            moods=_options(
                [
                    (Mood.QUIET, "조용한"),
                    (Mood.EMOTIONAL, "감성적인"),
                    (Mood.LIVELY, "활기찬"),
                    (Mood.SPECIAL, "특별한"),
                ]
            ),
            activity_types=_options(
                [
                    (ActivityType.TOURISM, "관광"),
                    (ActivityType.CULTURE_EXHIBITION, "문화·전시"),
                    (ActivityType.FOOD, "음식"),
                    (ActivityType.SHOPPING, "쇼핑"),
                    (ActivityType.WALK, "산책"),
                    (ActivityType.LEPORTS, "레포츠"),
                ]
            ),
            schedule_densities=_options(
                [
                    (ScheduleDensity.RELAXED, "널널하게"),
                    (ScheduleDensity.NORMAL, "적당하게"),
                    (ScheduleDensity.TIGHT, "빠듯하게"),
                ]
            ),
            transportations=_options(
                [
                    (Transportation.WALK, "도보"),
                    (Transportation.PUBLIC_TRANSIT, "대중교통"),
                    (Transportation.CAR, "자가용"),
                    (Transportation.FLEXIBLE, "유동적"),
                ]
            ),
            ranking_sorts=_options(
                [
                    (RankingSort.POPULAR, "인기순"),
                    (RankingSort.LATEST, "최신순"),
                ]
            ),
        )
