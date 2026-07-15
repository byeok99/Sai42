"""Current DateCourse progression, heart, and completion use cases."""

import json
from datetime import datetime, timedelta
from math import floor
from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError

from app.auth.domain.entities import AuthenticatedProfile
from app.common.application.errors import BusinessException
from app.common.domain.enums import (
    ActivityType,
    District,
    Mood,
    ScheduleDensity,
    SpaceType,
    TimeSlot,
    Transportation,
)
from app.common.domain.time import now_seoul
from app.community.infrastructure.models import CommunityPost
from app.course.application.dto import (
    CompleteDateCourseDto,
    CompleteDateCourseRequestDto,
    CompletedPlaceDto,
    CoordinateDto,
    CourseConditionDto,
    CourseMapDto,
    CoursePlaceDto,
    CoursePlaceHeartDto,
    CoursePlaceSnapshotDto,
    CourseProgressSummaryDto,
    DateCourseDto,
    DateCourseProgressDto,
    PublishedCommunityPostDto,
)
from app.course.domain.enums import DateCourseSourceType, DateCourseStatus
from app.course.infrastructure.models import DateCourse, DateCoursePlace
from app.course.infrastructure.repository import DateCourseRepository
from app.place.domain.constants import PLACE_CATEGORY_BY_CONTENT_TYPE_ID
from app.place.domain.enums import PlaceCategory


def _datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


class DateCourseService:
    def __init__(self, repository: DateCourseRepository) -> None:
        self.repository = repository

    async def get_current(self, profile: AuthenticatedProfile) -> DateCourseDto | None:
        course = await self.repository.find_active_course(profile.id)
        if course is None:
            return None
        return await self._course_dto(course)

    async def render_course(self, course: DateCourse) -> DateCourseDto:
        """Build the shared immutable course read model for adjacent domains."""
        return await self._course_dto(course)

    async def complete_place(
        self, profile: AuthenticatedProfile, course_place_id: str
    ) -> DateCourseProgressDto:
        course = await self._required_active_course(profile.id)
        target = await self._required_owned_place(course, course_place_id)
        places = await self.repository.list_course_places(course.id)
        if target.completed_at is None:
            if target.order_no != course.current_order_no:
                raise BusinessException(
                    status_code=409,
                    code="DATE_COURSE_PLACE_SEQUENCE_CONFLICT",
                    message="현재 순서의 장소만 완료할 수 있습니다.",
                )
            now = now_seoul().isoformat()
            target.completed_at = now
            course.started_at = course.started_at or now
            course.updated_at = now
            following = next((place for place in places if place.order_no > target.order_no), None)
            if following is not None:
                course.current_order_no = following.order_no
            await self.repository.commit()
        return await self._progress_dto(course, target, places)

    async def set_heart(
        self,
        profile: AuthenticatedProfile,
        course_place_id: str,
        *,
        hearted: bool,
    ) -> CoursePlaceHeartDto:
        course = await self._required_active_course(profile.id)
        target = await self._required_owned_place(course, course_place_id)
        now = now_seoul()
        if bool(target.hearted) != hearted:
            target.hearted = int(hearted)
            target.hearted_at = now.isoformat() if hearted else None
            course.updated_at = now.isoformat()
            await self.repository.flush()
            await self.repository.commit()
        counts = await self.repository.heart_counts(
            {target.content_id} if target.content_id else set()
        )
        return CoursePlaceHeartDto(
            course_place_id=target.id,
            hearted_by_me=hearted,
            heart_count=counts.get(target.content_id or "", 0),
            updated_at=now,
        )

    async def complete_course(
        self,
        profile: AuthenticatedProfile,
        request: CompleteDateCourseRequestDto,
    ) -> CompleteDateCourseDto:
        if not request.one_line_comment:
            raise BusinessException(
                status_code=422,
                code="COMMUNITY_COMMENT_REQUIRED",
                message="데이트 종료 한 줄 코멘트를 입력해 주세요.",
            )
        course = await self._required_active_course(profile.id)
        places = await self.repository.list_course_places(course.id)
        if not places or any(place.completed_at is None for place in places):
            raise BusinessException(
                status_code=409,
                code="DATE_COURSE_PLACES_INCOMPLETE",
                message="모든 장소를 완료한 후 데이트를 종료해 주세요.",
            )
        now = now_seoul()
        course.status = DateCourseStatus.COMPLETED.value
        course.completion_comment = request.one_line_comment
        course.completed_at = now.isoformat()
        course.updated_at = now.isoformat()
        post = CommunityPost(
            id=str(uuid4()),
            date_course_id=course.id,
            author_profile_id=profile.id,
            author_nickname_snapshot=profile.nickname,
            one_line_comment=request.one_line_comment,
            status="PUBLISHED",
            published_at=now.isoformat(),
            updated_at=now.isoformat(),
            deleted_at=None,
        )
        try:
            await self.repository.add_community_post(post)
            await self.repository.commit()
        except SQLAlchemyError:
            await self.repository.rollback()
            raise BusinessException(
                status_code=500,
                code="DATE_COURSE_COMPLETION_TRANSACTION_FAILED",
                message="데이트 종료 처리에 실패했습니다.",
            ) from None
        return CompleteDateCourseDto(
            completed_course=await self._course_dto(course, places=places),
            community_post=PublishedCommunityPostDto(
                post_id=post.id,
                course_id=course.id,
                status=post.status,
                one_line_comment=post.one_line_comment,
                published_at=now,
            ),
        )

    async def _required_active_course(self, profile_id: str) -> DateCourse:
        course = await self.repository.find_active_course(profile_id)
        if course is None:
            raise BusinessException(
                status_code=404,
                code="DATE_COURSE_CURRENT_NOT_FOUND",
                message="현재 진행 중인 데이트 코스가 없습니다.",
            )
        return course

    async def _required_owned_place(
        self, course: DateCourse, course_place_id: str
    ) -> DateCoursePlace:
        place = await self.repository.find_course_place(course_place_id)
        if place is None:
            raise BusinessException(
                status_code=404,
                code="DATE_COURSE_PLACE_NOT_FOUND",
                message="코스 장소를 찾을 수 없습니다.",
            )
        if place.date_course_id != course.id:
            raise BusinessException(
                status_code=403,
                code="DATE_COURSE_PLACE_NOT_OWNED",
                message="현재 코스의 장소가 아닙니다.",
            )
        return place

    async def _course_dto(
        self,
        course: DateCourse,
        *,
        places: list[DateCoursePlace] | None = None,
    ) -> DateCourseDto:
        places = places or await self.repository.list_course_places(course.id)
        heart_counts = await self.repository.heart_counts(
            {place.content_id for place in places if place.content_id}
        )
        place_dtos = [self._place_dto(place, heart_counts) for place in places]
        completed_count = sum(place.completed_at is not None for place in places)
        coordinates = [
            CoordinateDto(latitude=place.latitude_snapshot, longitude=place.longitude_snapshot)
            for place in places
            if place.latitude_snapshot is not None and place.longitude_snapshot is not None
        ]
        first_start = _datetime(places[0].scheduled_at)
        last_end = _datetime(places[-1].scheduled_at) + timedelta(
            minutes=places[-1].estimated_stay_minutes
        )
        conditions = CourseConditionDto(
            date=course.date,
            time_slot=TimeSlot(course.time_slot),
            start_time=course.start_time,
            district=District(course.main_district),
            space_type=SpaceType(course.space_type),
            moods=[Mood(value) for value in json.loads(course.moods_json)],
            activities=[ActivityType(value) for value in json.loads(course.activities_json)],
            schedule_density=ScheduleDensity(course.schedule_density),
            transportation=Transportation(course.transportation) if course.transportation else None,
        )
        return DateCourseDto(
            course_id=course.id,
            status=DateCourseStatus(course.status),
            source_type=DateCourseSourceType(course.source_type),
            title=course.title,
            date=course.date,
            time_slot=TimeSlot(course.time_slot),
            overall_comment=course.overall_comment,
            estimated_total_minutes=floor((last_end - first_start).total_seconds() / 60),
            conditions=conditions,
            tags=json.loads(course.tags_json),
            weather=json.loads(course.weather_json) if course.weather_json else None,
            places=place_dtos,
            map=CourseMapDto(
                center_latitude=(
                    sum(point.latitude for point in coordinates) / len(coordinates)
                    if coordinates
                    else None
                ),
                center_longitude=(
                    sum(point.longitude for point in coordinates) / len(coordinates)
                    if coordinates
                    else None
                ),
                polyline=coordinates,
            ),
            progress=self._progress_summary(course, places, completed_count),
            one_line_comment=course.completion_comment,
            created_at=_datetime(course.created_at),
            completed_at=_datetime(course.completed_at) if course.completed_at else None,
        )

    async def _progress_dto(
        self,
        course: DateCourse,
        completed_place: DateCoursePlace,
        places: list[DateCoursePlace],
    ) -> DateCourseProgressDto:
        heart_counts = await self.repository.heart_counts(
            {place.content_id for place in places if place.content_id}
        )
        completed_count = sum(place.completed_at is not None for place in places)
        next_place = next((place for place in places if place.completed_at is None), None)
        return DateCourseProgressDto(
            course_id=course.id,
            completed_place=CompletedPlaceDto(
                course_place_id=completed_place.id,
                order=completed_place.order_no,
                completed_at=_datetime(completed_place.completed_at),
            ),
            next_place=self._place_dto(next_place, heart_counts) if next_place else None,
            current_order_no=course.current_order_no,
            completed_place_count=completed_count,
            total_place_count=len(places),
            progress_percent=floor(completed_count * 100 / len(places)),
            all_places_completed=completed_count == len(places),
        )

    @staticmethod
    def _progress_summary(
        course: DateCourse,
        places: list[DateCoursePlace],
        completed_count: int,
    ) -> CourseProgressSummaryDto:
        total = len(places)
        return CourseProgressSummaryDto(
            current_order_no=course.current_order_no,
            completed_place_count=completed_count,
            total_place_count=total,
            progress_percent=floor(completed_count * 100 / total),
            all_places_completed=completed_count == total,
        )

    @staticmethod
    def _place_dto(
        place: DateCoursePlace,
        heart_counts: dict[str, int],
    ) -> CoursePlaceDto:
        return CoursePlaceDto(
            course_place_id=place.id,
            order=place.order_no,
            scheduled_at=_datetime(place.scheduled_at),
            estimated_stay_minutes=place.estimated_stay_minutes,
            place=CoursePlaceSnapshotDto(
                content_id=place.content_id,
                name=place.title_snapshot,
                category=PlaceCategory(
                    PLACE_CATEGORY_BY_CONTENT_TYPE_ID[place.content_type_id_snapshot]
                ),
                district=(District(place.district_snapshot) if place.district_snapshot else None),
                address=place.address_snapshot,
                address_detail=place.address_detail_snapshot,
                latitude=place.latitude_snapshot,
                longitude=place.longitude_snapshot,
                image_url=place.image_url_snapshot,
                indoor_outdoor=SpaceType(place.space_type_snapshot),
            ),
            sweet_comment=place.sweet_comment,
            hearted_by_me=bool(place.hearted),
            heart_count=heart_counts.get(place.content_id or "", 0),
        )
