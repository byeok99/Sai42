"""Deterministic quality checks for AI-generated course plans."""

import re
from math import asin, cos, radians, sin, sqrt

from app.chat.application.dto import CourseDraftDto
from app.chat.domain.entities import AiChatTurn, AiCourseContent, AiCoursePlan, PlaceCandidate
from app.chat.domain.enums import ChatTurnIntent, CourseEditAction
from app.common.domain.enums import SpaceType
from app.course.application.dto import CourseConditionDto

CAFE_KEYWORDS = ("카페", "커피", "coffee", "디저트", "베이커리")
NIGHT_VIEW_KEYWORDS = ("야경", "전망", "공원", "대교", "엑스포", "산")
INTERNAL_RESPONSE_PATTERNS = (
    re.compile(r"(?<![a-z])db(?![a-z])", re.IGNORECASE),
    re.compile(r"sqlite", re.IGNORECASE),
    re.compile(r"content\s*id", re.IGNORECASE),
    re.compile(r"candidates?", re.IGNORECASE),
    re.compile(r"(?<![a-z])any(?![a-z])", re.IGNORECASE),
    re.compile(r"후보"),
    re.compile(r"내부\s*(?:검증|프롬프트|시스템)"),
    re.compile(r"\b[A-Z][A-Z0-9_]{2,}\b"),
)


def haversine_km(
    first_latitude: float,
    first_longitude: float,
    second_latitude: float,
    second_longitude: float,
) -> float:
    """Return the great-circle distance between two WGS84 coordinates."""

    earth_radius_km = 6371.0088
    latitude_delta = radians(second_latitude - first_latitude)
    longitude_delta = radians(second_longitude - first_longitude)
    first_latitude_radians = radians(first_latitude)
    second_latitude_radians = radians(second_latitude)
    value = sin(latitude_delta / 2) ** 2 + (
        cos(first_latitude_radians) * cos(second_latitude_radians) * sin(longitude_delta / 2) ** 2
    )
    return 2 * earth_radius_km * asin(sqrt(value))


def route_distance_km(coordinates: list[tuple[float, float]]) -> float:
    return sum(
        haversine_km(*first, *second)
        for first, second in zip(coordinates, coordinates[1:], strict=False)
    )


def public_response_violations(texts: list[str]) -> list[str]:
    """Reject service internals and enum-like tokens from user-visible model text."""

    if any(_contains_internal_response_term(text) for text in texts):
        return [
            "사용자에게 데이터 저장 방식, 선택 목록, 식별자, 영문 enum 또는 내부 검증 용어를 "
            "노출하지 말고 자연스러운 서비스 문장으로 다시 작성하세요."
        ]
    return []


def sanitize_course_content(course: AiCourseContent) -> AiCourseContent:
    """Replace only unsafe user-visible wording without regenerating a valid course."""

    tags = [tag for tag in course.tags if not _contains_internal_response_term(tag)]
    return course.model_copy(
        update={
            "title": _safe_text(course.title, "함께 즐기는 데이트 코스"),
            "overall_comment": _safe_text(
                course.overall_comment,
                "요청한 분위기와 활동을 고려해 자연스럽게 이어지는 코스로 구성했어요.",
            ),
            "tags": tags or ["데이트"],
            "places": [
                place.model_copy(
                    update={
                        "sweet_comment": _safe_text(
                            place.sweet_comment,
                            "두 분의 시간을 편안하게 이어가기 좋은 장소예요.",
                        )
                    }
                )
                for place in course.places
            ],
        }
    )


def sanitize_course_plan(plan: AiCoursePlan) -> AiCoursePlan:
    cleaned_course = sanitize_course_content(plan)
    return plan.model_copy(
        update={
            "title": cleaned_course.title,
            "overall_comment": cleaned_course.overall_comment,
            "tags": cleaned_course.tags,
            "places": cleaned_course.places,
            "assistant_message": _safe_text(
                plan.assistant_message,
                "요청한 조건을 반영해 데이트 코스를 준비했어요.",
            ),
            "warnings": [
                warning
                for warning in plan.warnings
                if not _contains_internal_response_term(warning)
            ],
        }
    )


def sanitize_chat_turn(turn: AiChatTurn) -> AiChatTurn:
    fallback_by_intent = {
        ChatTurnIntent.COURSE_EDIT: "요청한 내용을 반영해 데이트 코스를 조정했어요.",
        ChatTurnIntent.COURSE_QUESTION: "현재 코스를 기준으로 궁금한 내용을 안내해 드릴게요.",
        ChatTurnIntent.CASUAL_CONVERSATION: (
            "편하게 말씀해 주세요. 데이트 이야기라면 무엇이든 함께 생각해 볼게요."
        ),
        ChatTurnIntent.CLARIFICATION_REQUIRED: (
            "원하는 변경 방향을 조금 더 구체적으로 알려주세요."
        ),
    }
    return turn.model_copy(
        update={
            "assistant_message": _safe_text(
                turn.assistant_message,
                fallback_by_intent[turn.intent],
            ),
            "proposed_course": (
                sanitize_course_content(turn.proposed_course)
                if turn.proposed_course is not None
                else None
            ),
            "warnings": [
                warning
                for warning in turn.warnings
                if not _contains_internal_response_term(warning)
            ],
        }
    )


def _contains_internal_response_term(text: str) -> bool:
    return any(pattern.search(text) for pattern in INTERNAL_RESPONSE_PATTERNS)


def _safe_text(text: str, fallback: str) -> str:
    return fallback if _contains_internal_response_term(text) else text


class CoursePlanQualityPolicy:
    """Validate business intent beyond the provider's output schema."""

    def violations(
        self,
        plan: AiCourseContent,
        *,
        conditions: CourseConditionDto,
        candidates: list[PlaceCandidate],
        current_draft: CourseDraftDto | None,
        action: CourseEditAction | None,
    ) -> list[str]:
        candidate_by_id = {candidate.content_id: candidate for candidate in candidates}
        selected_ids = [place.content_id for place in plan.places]
        violations: list[str] = []

        if len(selected_ids) != len(set(selected_ids)):
            violations.append("서로 다른 장소만 선택해야 합니다.")
        if any(content_id not in candidate_by_id for content_id in selected_ids):
            violations.append("candidates에 없는 contentId를 선택하지 마세요.")
            return violations

        selected = [candidate_by_id[content_id] for content_id in selected_ids]
        violations.extend(self._condition_violations(plan, selected, candidates, conditions))
        if current_draft is not None and action is not None:
            violations.extend(
                self._action_violations(plan, selected, candidates, current_draft, action)
            )
        return violations

    @staticmethod
    def _condition_violations(
        plan: AiCourseContent,
        selected: list[PlaceCandidate],
        candidates: list[PlaceCandidate],
        conditions: CourseConditionDto,
    ) -> list[str]:
        violations: list[str] = []
        requested = {activity.value for activity in conditions.activities}
        available = requested & {
            activity for candidate in candidates for activity in candidate.activities
        }
        covered = available & {
            activity for candidate in selected for activity in candidate.activities
        }
        required_coverage = min(len(available), len(plan.places))
        if len(covered) < required_coverage:
            missing = ", ".join(sorted(available - covered))
            violations.append(f"선택 가능한 요청 활동을 더 반영하세요: {missing}")

        if conditions.space_type != SpaceType.ANY:
            matching_space_count = sum(
                place.space_type == conditions.space_type for place in plan.places
            )
            if matching_space_count * 2 < len(plan.places):
                violations.append(
                    f"요청한 공간 유형 {conditions.space_type.value}을 과반수 이상 반영하세요."
                )
        return violations

    def _action_violations(
        self,
        plan: AiCourseContent,
        selected: list[PlaceCandidate],
        candidates: list[PlaceCandidate],
        current: CourseDraftDto,
        action: CourseEditAction,
    ) -> list[str]:
        current_ids = {place.place.content_id for place in current.places}
        selected_ids = {candidate.content_id for candidate in selected}
        violations: list[str] = []

        if action == CourseEditAction.REGENERATE and selected_ids == current_ids:
            violations.append("REGENERATE 요청에서는 기존과 다른 장소 조합을 선택하세요.")
        elif action == CourseEditAction.CHANGE_CAFE:
            if self._has_keyword(candidates, CAFE_KEYWORDS) and not self._has_keyword(
                selected, CAFE_KEYWORDS
            ):
                violations.append("카페로 판단할 수 있는 후보를 코스에 포함하세요.")
        elif action == CourseEditAction.ADD_NIGHT_VIEW:
            if self._has_keyword(candidates, NIGHT_VIEW_KEYWORDS) and not self._has_keyword(
                selected, NIGHT_VIEW_KEYWORDS
            ):
                violations.append("야경이나 전망 장소로 판단할 수 있는 후보를 포함하세요.")
        elif action == CourseEditAction.INCREASE_INDOOR:
            previous_indoor = sum(
                place.place.indoor_outdoor == SpaceType.INDOOR for place in current.places
            )
            proposed_indoor = sum(place.space_type == SpaceType.INDOOR for place in plan.places)
            if previous_indoor < len(current.places) and proposed_indoor <= previous_indoor:
                violations.append("기존 초안보다 실내 장소 비중을 높이세요.")
        elif action == CourseEditAction.REDUCE_ROUTE:
            if len(plan.places) != len(current.places):
                violations.append("이동 동선 축소 시 기존 장소 수를 유지하세요.")
            elif self._selected_route_distance(selected) >= self._draft_route_distance(current):
                violations.append("기존 초안보다 실제 좌표 이동 거리가 짧은 조합을 선택하세요.")
        return violations

    @staticmethod
    def _has_keyword(candidates: list[PlaceCandidate], keywords: tuple[str, ...]) -> bool:
        return any(
            keyword in candidate.title.casefold()
            for candidate in candidates
            for keyword in keywords
        )

    @staticmethod
    def _selected_route_distance(candidates: list[PlaceCandidate]) -> float:
        return route_distance_km(
            [(candidate.latitude, candidate.longitude) for candidate in candidates]
        )

    @staticmethod
    def _draft_route_distance(draft: CourseDraftDto) -> float:
        return route_distance_km(
            [
                (place.place.latitude, place.place.longitude)
                for place in draft.places
                if place.place.latitude is not None and place.place.longitude is not None
            ]
        )
