"""Completed course history and restart use cases."""

from app.auth.domain.entities import AuthenticatedProfile
from app.common.application.dto import PageMetaDto
from app.common.application.errors import BusinessException
from app.common.domain.enums import District
from app.course.application.copy_service import CourseCopyService
from app.course.application.dto import CopyCourseRequestDto, DateCourseDto
from app.course.application.service import DateCourseService
from app.course.domain.enums import DateCourseSourceType
from app.course.infrastructure.repository import DateCourseRepository
from app.history.application.dto import HistoryCourseSummaryDto
from app.history.infrastructure.repository import HistoryRepository


class HistoryService:
    def __init__(self, repository: HistoryRepository) -> None:
        self.repository = repository

    async def list_courses(
        self,
        profile: AuthenticatedProfile,
        *,
        year: int | None,
        month: int | None,
        district: District | None,
        page: int,
        size: int,
    ) -> tuple[list[HistoryCourseSummaryDto], PageMetaDto]:
        rows, total = await self.repository.list_completed(
            profile.id,
            year=year,
            month=month,
            district=district,
            offset=(page - 1) * size,
            limit=size,
        )
        items = [
            HistoryCourseSummaryDto(
                course_id=row.course.id,
                date=row.course.date,
                course_title=row.course.title,
                main_district=row.course.main_district,
                one_line_comment=row.course.completion_comment or "",
                hearted_place_count=row.hearted_place_count,
                total_place_count=row.total_place_count,
                completed_at=row.course.completed_at,
            )
            for row in rows
        ]
        total_pages = (total + size - 1) // size
        return items, PageMetaDto(
            page=page,
            size=size,
            total_elements=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
        )

    async def get_detail(self, profile: AuthenticatedProfile, course_id: str) -> DateCourseDto:
        course = await self._owned_completed_course(profile, course_id)
        return await DateCourseService(DateCourseRepository(self.repository.session)).render_course(
            course
        )

    async def restart(
        self,
        profile: AuthenticatedProfile,
        course_id: str,
        request: CopyCourseRequestDto,
    ) -> DateCourseDto:
        course_repository = DateCourseRepository(self.repository.session)
        if await course_repository.find_active_course(profile.id):
            raise BusinessException(
                status_code=409,
                code="DATE_COURSE_ACTIVE_ALREADY_EXISTS",
                message="이미 진행 중인 데이트 코스가 있습니다.",
            )
        course = await self._owned_completed_course(profile, course_id)
        return await CourseCopyService(course_repository).copy(
            profile=profile,
            source_course=course,
            request=request,
            source_type=DateCourseSourceType.HISTORY_RESTART,
        )

    async def _owned_completed_course(self, profile: AuthenticatedProfile, course_id: str):
        course = await self.repository.find_course(course_id)
        if course is None or course.status != "COMPLETED":
            raise BusinessException(
                status_code=404,
                code="HISTORY_COURSE_NOT_FOUND",
                message="완료 코스를 찾을 수 없습니다.",
            )
        if course.profile_id != profile.id:
            raise BusinessException(
                status_code=403,
                code="HISTORY_COURSE_FORBIDDEN",
                message="본인의 완료 코스만 조회할 수 있습니다.",
            )
        return course
