"""Deterministic quality checks for AI-generated course plans."""

from math import asin, cos, radians, sin, sqrt

from app.chat.application.dto import CourseDraftDto
from app.chat.domain.entities import AiCoursePlan, PlaceCandidate
from app.chat.domain.enums import CourseEditAction
from app.common.domain.enums import SpaceType
from app.course.application.dto import CourseConditionDto

CAFE_KEYWORDS = ("카페", "커피", "coffee", "디저트", "베이커리")
NIGHT_VIEW_KEYWORDS = ("야경", "전망", "공원", "대교", "엑스포", "산")


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


class CoursePlanQualityPolicy:
    """Validate business intent beyond the provider's output schema."""

    def violations(
        self,
        plan: AiCoursePlan,
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
        plan: AiCoursePlan,
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
        plan: AiCoursePlan,
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
