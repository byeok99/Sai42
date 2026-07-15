"""Shared immutable course-copy workflow for ranking and history starts."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy.exc import IntegrityError

from app.auth.domain.entities import AuthenticatedProfile
from app.common.application.errors import BusinessException
from app.common.domain.time import now_seoul
from app.course.application.dto import CopyCourseRequestDto, DateCourseDto
from app.course.application.service import DateCourseService
from app.course.domain.enums import DateCourseSourceType
from app.course.infrastructure.models import DateCourse, DateCoursePlace
from app.course.infrastructure.repository import DateCourseRepository


class CourseCopyService:
    def __init__(self, repository: DateCourseRepository) -> None:
        self.repository = repository

    async def copy(
        self,
        *,
        profile: AuthenticatedProfile,
        source_course: DateCourse,
        request: CopyCourseRequestDto,
        source_type: DateCourseSourceType,
    ) -> DateCourseDto:
        if await self.repository.find_active_course(profile.id):
            raise BusinessException(
                status_code=409,
                code="DATE_COURSE_ACTIVE_ALREADY_EXISTS",
                message="이미 진행 중인 데이트 코스가 있습니다.",
            )
        if request.start_time.tzinfo is not None:
            self._raise_invalid_start_time()
        new_start = datetime.combine(request.date, request.start_time, tzinfo=now_seoul().tzinfo)
        if new_start <= now_seoul():
            self._raise_invalid_start_time()
        source_places = await self.repository.list_course_places(source_course.id)
        if not 2 <= len(source_places) <= 4:
            raise BusinessException(
                status_code=422,
                code="COURSE_COPY_INVALID_START_TIME",
                message="복사할 수 없는 코스 구성입니다.",
            )
        original_start = datetime.fromisoformat(source_places[0].scheduled_at)
        now = now_seoul().isoformat()
        course_id = str(uuid4())
        course = DateCourse(
            id=course_id,
            profile_id=profile.id,
            chat_session_id=None,
            status="ACTIVE",
            source_type=source_type.value,
            source_course_id=source_course.id,
            title=source_course.title,
            date=request.date.isoformat(),
            start_time=request.start_time.strftime("%H:%M"),
            time_slot=source_course.time_slot,
            main_district=source_course.main_district,
            space_type=source_course.space_type,
            moods_json=source_course.moods_json,
            activities_json=source_course.activities_json,
            schedule_density=source_course.schedule_density,
            transportation=source_course.transportation,
            overall_comment=source_course.overall_comment,
            tags_json=source_course.tags_json,
            weather_json=None,
            current_order_no=source_places[0].order_no,
            completion_comment=None,
            started_at=None,
            completed_at=None,
            created_at=now,
            updated_at=now,
        )
        places = []
        for source in source_places:
            offset = datetime.fromisoformat(source.scheduled_at) - original_start
            places.append(
                DateCoursePlace(
                    id=str(uuid4()),
                    date_course_id=course_id,
                    content_id=source.content_id,
                    order_no=source.order_no,
                    scheduled_at=(new_start + offset).isoformat(),
                    estimated_stay_minutes=source.estimated_stay_minutes,
                    sweet_comment=source.sweet_comment,
                    hearted=0,
                    hearted_at=None,
                    completed_at=None,
                    title_snapshot=source.title_snapshot,
                    address_snapshot=source.address_snapshot,
                    address_detail_snapshot=source.address_detail_snapshot,
                    longitude_snapshot=source.longitude_snapshot,
                    latitude_snapshot=source.latitude_snapshot,
                    content_type_id_snapshot=source.content_type_id_snapshot,
                    district_snapshot=source.district_snapshot,
                    space_type_snapshot=source.space_type_snapshot,
                    image_url_snapshot=source.image_url_snapshot,
                    created_at=now,
                )
            )
        try:
            await self.repository.add_course(course, places)
            await self.repository.commit()
        except IntegrityError:
            await self.repository.rollback()
            raise BusinessException(
                status_code=409,
                code="DATE_COURSE_ACTIVE_ALREADY_EXISTS",
                message="이미 진행 중인 데이트 코스가 있습니다.",
            ) from None
        return await DateCourseService(self.repository).render_course(course)

    @staticmethod
    def _raise_invalid_start_time() -> None:
        raise BusinessException(
            status_code=422,
            code="COURSE_COPY_INVALID_START_TIME",
            message="현재 이후의 시작 날짜와 시간을 입력해 주세요.",
        )
