"""History list contracts for completed date courses."""

from datetime import date, datetime

from app.common.application.dto import ApiDto
from app.common.domain.enums import District


class HistoryCourseSummaryDto(ApiDto):
    course_id: str
    date: date
    course_title: str
    main_district: District
    one_line_comment: str
    hearted_place_count: int
    total_place_count: int
    completed_at: datetime
