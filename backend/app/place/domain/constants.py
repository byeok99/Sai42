"""Place domain mappings shared by imports and future DTO conversion."""

RECOMMENDABLE_CONTENT_TYPE_IDS = frozenset({12, 14, 25, 28, 32, 38, 39})
EXCLUDED_CONTENT_TYPE_IDS = frozenset({15})

PLACE_CATEGORY_BY_CONTENT_TYPE_ID = {
    12: "ATTRACTION",
    14: "CULTURAL_FACILITY",
    25: "TRAVEL_COURSE",
    28: "LEPORTS",
    32: "ACCOMMODATION",
    38: "SHOPPING",
    39: "RESTAURANT",
}

ACTIVITIES_BY_CONTENT_TYPE_ID = {
    12: ("TOURISM",),
    14: ("CULTURE_EXHIBITION",),
    25: ("TOURISM", "WALK"),
    28: ("LEPORTS",),
    32: (),
    38: ("SHOPPING",),
    39: ("FOOD",),
}

DISTRICT_BY_ADDRESS_PREFIX = {
    "대전광역시 동구": "DONG_GU",
    "대전광역시 중구": "JUNG_GU",
    "대전광역시 서구": "SEO_GU",
    "대전광역시 유성구": "YUSEONG_GU",
    "대전광역시 대덕구": "DAEDEOK_GU",
}

SOURCE_PROVIDER = "한국관광공사"
SOURCE_LICENSE = "공공누리 제3유형"
SOURCE_URL = "https://www.data.go.kr/data/15101578/openapi.do"
