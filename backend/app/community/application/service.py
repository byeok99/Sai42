"""Community publishing, ranking list, likes, and course-start use cases."""

import json
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError

from app.auth.domain.entities import AuthenticatedProfile
from app.common.application.dto import PageMetaDto
from app.common.application.errors import BusinessException
from app.common.domain.time import now_seoul
from app.community.application.dto import (
    CommunityLikeDto,
    CommunityPostDetailDto,
    CommunityPostSummaryDto,
    DateMasterDto,
    DateMastersDto,
    PublishCommunityPostRequestDto,
    UpdateCommunityPostRequestDto,
)
from app.community.domain.query import CommunityPostCriteria
from app.community.infrastructure.models import CommunityLike
from app.community.infrastructure.repository import CommunityPostRow, CommunityRepository
from app.course.application.copy_service import CourseCopyService
from app.course.application.dto import (
    CopyCourseRequestDto,
    CopyResultDto,
    StartCommunityCourseDto,
)
from app.course.application.service import DateCourseService
from app.course.domain.enums import DateCourseSourceType
from app.course.infrastructure.repository import DateCourseRepository


class CommunityService:
    def __init__(self, repository: CommunityRepository) -> None:
        self.repository = repository

    async def list_posts(
        self,
        criteria: CommunityPostCriteria,
        *,
        profile: AuthenticatedProfile | None,
        page: int,
        size: int,
    ) -> tuple[list[CommunityPostSummaryDto], PageMetaDto]:
        rows, total = await self.repository.list_published(
            criteria,
            profile_id=profile.id if profile else None,
            offset=(page - 1) * size,
            limit=size,
        )
        heart_totals = await self.repository.place_heart_totals({row.course.id for row in rows})
        items = [
            CommunityPostSummaryDto(
                rank=(page - 1) * size + index,
                post_id=row.post.id,
                course_id=row.course.id,
                course_title=row.course.title,
                main_district=row.course.main_district,
                author_nickname=row.post.author_nickname_snapshot,
                one_line_comment=row.post.one_line_comment,
                course_like_count=row.like_count,
                place_heart_count=heart_totals.get(row.course.id, 0),
                liked_by_me=row.liked_by_me,
                tags=json.loads(row.course.tags_json),
                published_at=row.post.published_at,
            )
            for index, row in enumerate(rows, start=1)
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

    async def get_detail(
        self, post_id: str, *, profile: AuthenticatedProfile | None
    ) -> CommunityPostDetailDto:
        row = await self.repository.find_published(
            post_id, profile_id=profile.id if profile else None
        )
        if row is None:
            raise BusinessException(
                status_code=404,
                code="COMMUNITY_POST_NOT_FOUND",
                message="공개 게시글을 찾을 수 없습니다.",
            )
        return await self._detail(row, profile)

    async def republish(
        self,
        profile: AuthenticatedProfile,
        request: PublishCommunityPostRequestDto,
    ) -> CommunityPostDetailDto:
        self._validate_comment(request.one_line_comment)
        course = await self.repository.find_course(request.date_course_id)
        if course is None or course.status != "COMPLETED":
            raise BusinessException(
                status_code=422,
                code="COMMUNITY_COMPLETED_COURSE_REQUIRED",
                message="완료한 데이트 코스만 공개할 수 있습니다.",
            )
        if course.profile_id != profile.id:
            raise BusinessException(
                status_code=403,
                code="COMMUNITY_POST_FORBIDDEN",
                message="본인의 완료 코스만 공개할 수 있습니다.",
            )
        post = await self.repository.find_post_by_course(course.id)
        if post is None:
            raise BusinessException(
                status_code=404,
                code="COMMUNITY_POST_NOT_FOUND",
                message="복원할 게시글을 찾을 수 없습니다.",
            )
        if post.status == "PUBLISHED":
            raise BusinessException(
                status_code=409,
                code="COMMUNITY_POST_ALREADY_EXISTS",
                message="이미 공개 중인 게시글입니다.",
            )
        now = now_seoul().isoformat()
        post.status = "PUBLISHED"
        post.author_profile_id = profile.id
        post.author_nickname_snapshot = profile.nickname
        post.one_line_comment = request.one_line_comment
        post.published_at = now
        post.updated_at = now
        post.deleted_at = None
        await self.repository.commit()
        return await self.get_detail(post.id, profile=profile)

    async def update(
        self,
        profile: AuthenticatedProfile,
        post_id: str,
        request: UpdateCommunityPostRequestDto,
    ) -> CommunityPostDetailDto:
        self._validate_comment(request.one_line_comment)
        post = await self._owned_post(profile, post_id)
        if post.status != "PUBLISHED":
            self._raise_deleted()
        post.one_line_comment = request.one_line_comment
        post.updated_at = now_seoul().isoformat()
        await self.repository.commit()
        return await self.get_detail(post.id, profile=profile)

    async def delete(self, profile: AuthenticatedProfile, post_id: str) -> None:
        post = await self._owned_post(profile, post_id)
        if post.status == "DELETED":
            return
        now = now_seoul().isoformat()
        post.status = "DELETED"
        post.updated_at = now
        post.deleted_at = now
        await self.repository.commit()

    async def set_like(
        self, profile: AuthenticatedProfile, post_id: str, *, liked: bool
    ) -> CommunityLikeDto:
        post = await self.repository.find_post(post_id)
        if post is None:
            raise BusinessException(
                status_code=404,
                code="COMMUNITY_POST_NOT_FOUND",
                message="게시글을 찾을 수 없습니다.",
            )
        if post.status != "PUBLISHED":
            self._raise_deleted()
        existing = await self.repository.find_like(profile.id, post.id)
        try:
            if liked and existing is None:
                await self.repository.add_like(
                    CommunityLike(
                        id=str(uuid4()),
                        profile_id=profile.id,
                        community_post_id=post.id,
                        created_at=now_seoul().isoformat(),
                    )
                )
                await self.repository.commit()
            elif not liked and existing is not None:
                await self.repository.delete_like(existing)
                await self.repository.commit()
        except IntegrityError:
            await self.repository.rollback()
        return CommunityLikeDto(
            post_id=post.id,
            liked_by_me=liked,
            like_count=await self.repository.like_count(post.id),
        )

    async def start_course(
        self,
        profile: AuthenticatedProfile,
        post_id: str,
        request: CopyCourseRequestDto,
    ) -> StartCommunityCourseDto:
        course_repository = DateCourseRepository(self.repository.session)
        if await course_repository.find_active_course(profile.id):
            raise BusinessException(
                status_code=409,
                code="DATE_COURSE_ACTIVE_ALREADY_EXISTS",
                message="이미 진행 중인 데이트 코스가 있습니다.",
            )
        post = await self.repository.find_post(post_id)
        if post is None:
            raise BusinessException(
                status_code=404,
                code="COMMUNITY_POST_NOT_FOUND",
                message="게시글을 찾을 수 없습니다.",
            )
        if post.status != "PUBLISHED":
            self._raise_deleted()
        source_course = await self.repository.find_course(post.date_course_id)
        active_course = await CourseCopyService(course_repository).copy(
            profile=profile,
            source_course=source_course,
            request=request,
            source_type=DateCourseSourceType.RANKING_COPY,
        )
        return StartCommunityCourseDto(
            active_course=active_course,
            copy_result=CopyResultDto(source_post_id=post.id, warnings=[]),
        )

    async def get_masters(self, limit: int) -> DateMastersDto:
        rows = await self.repository.list_masters(limit)
        return DateMastersDto(
            masters=[
                DateMasterDto(
                    rank=index,
                    profile_id=UUID(profile_id),
                    nickname=nickname,
                    published_course_count=post_count,
                    received_like_count=like_count,
                )
                for index, (profile_id, nickname, post_count, like_count) in enumerate(
                    rows, start=1
                )
            ]
        )

    async def _detail(
        self, row: CommunityPostRow, profile: AuthenticatedProfile | None
    ) -> CommunityPostDetailDto:
        course = await DateCourseService(
            DateCourseRepository(self.repository.session)
        ).render_course(row.course)
        heart_totals = await self.repository.place_heart_totals({row.course.id})
        return CommunityPostDetailDto(
            post_id=row.post.id,
            owner=profile is not None and row.post.author_profile_id == profile.id,
            course_id=row.course.id,
            course_title=row.course.title,
            author_nickname=row.post.author_nickname_snapshot,
            one_line_comment=row.post.one_line_comment,
            date=course.date,
            time_slot=course.time_slot,
            overall_comment=course.overall_comment,
            conditions=course.conditions,
            tags=course.tags,
            places=course.places,
            map=course.map,
            course_like_count=row.like_count,
            place_heart_count=heart_totals.get(row.course.id, 0),
            liked_by_me=row.liked_by_me,
            published_at=row.post.published_at,
        )

    async def _owned_post(self, profile: AuthenticatedProfile, post_id: str):
        post = await self.repository.find_post(post_id)
        if post is None:
            raise BusinessException(
                status_code=404,
                code="COMMUNITY_POST_NOT_FOUND",
                message="게시글을 찾을 수 없습니다.",
            )
        if post.author_profile_id != profile.id:
            raise BusinessException(
                status_code=403,
                code="COMMUNITY_POST_FORBIDDEN",
                message="게시글을 수정할 권한이 없습니다.",
            )
        return post

    @staticmethod
    def _validate_comment(comment: str) -> None:
        if not comment:
            raise BusinessException(
                status_code=422,
                code="COMMUNITY_COMMENT_REQUIRED",
                message="한 줄 코멘트를 입력해 주세요.",
            )

    @staticmethod
    def _raise_deleted() -> None:
        raise BusinessException(
            status_code=409,
            code="COMMUNITY_POST_DELETED",
            message="삭제된 게시글입니다.",
        )
