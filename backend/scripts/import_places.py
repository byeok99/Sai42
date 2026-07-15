"""Validate TourAPI JSON files and upsert them into the SQLite places table."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import create_engine, inspect, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.place.domain.constants import (
    ACTIVITIES_BY_CONTENT_TYPE_ID,
    DISTRICT_BY_ADDRESS_PREFIX,
    EXCLUDED_CONTENT_TYPE_IDS,
    RECOMMENDABLE_CONTENT_TYPE_IDS,
)
from app.place.infrastructure.models import Place

SEOUL = timezone(timedelta(hours=9), name="Asia/Seoul")
EXPECTED_ITEM_FIELDS = {
    "addr1",
    "addr2",
    "areacode",
    "cat1",
    "cat2",
    "cat3",
    "contentid",
    "contenttypeid",
    "cpyrhtDivCd",
    "createdtime",
    "firstimage",
    "firstimage2",
    "lclsSystm1",
    "lclsSystm2",
    "lclsSystm3",
    "lDongRegnCd",
    "lDongSignguCd",
    "mapx",
    "mapy",
    "mlevel",
    "modifiedtime",
    "sigungucode",
    "tel",
    "title",
    "zipcode",
}
UPSERT_BATCH_SIZE = 20


class ImportValidationError(ValueError):
    """Raised when a source document does not match the declared TourAPI schema."""


@dataclass(frozen=True)
class ImportResult:
    """Counts reported after a successful import transaction."""

    source_items: int
    loaded: int
    inserted: int
    updated: int
    skipped: int
    recommendable: int


def _load_document(path: Path) -> dict[str, object]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ImportValidationError(f"{path.name}: JSON을 읽을 수 없습니다: {exc}") from exc
    if not isinstance(document, dict):
        raise ImportValidationError(f"{path.name}: 최상위 값은 객체여야 합니다.")
    return document


def _required_int(value: object, *, field: str, filename: str) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError) as exc:
        raise ImportValidationError(f"{filename}: {field} 값이 정수가 아닙니다: {value!r}") from exc


def _required_float(value: object, *, field: str, filename: str) -> float:
    try:
        result = float(str(value))
    except (TypeError, ValueError) as exc:
        raise ImportValidationError(f"{filename}: {field} 값이 실수가 아닙니다: {value!r}") from exc
    if field == "mapx" and not -180 <= result <= 180:
        raise ImportValidationError(f"{filename}: 경도 범위를 벗어났습니다: {result}")
    if field == "mapy" and not -90 <= result <= 90:
        raise ImportValidationError(f"{filename}: 위도 범위를 벗어났습니다: {result}")
    return result


def _source_timestamp(value: object, *, field: str, filename: str) -> str | None:
    text = str(value or "")
    if not text:
        return None
    try:
        parsed = datetime.strptime(text, "%Y%m%d%H%M%S").replace(tzinfo=SEOUL)
    except ValueError as exc:
        raise ImportValidationError(
            f"{filename}: {field} 값이 YYYYMMDDHHmmss 형식이 아닙니다: {text!r}"
        ) from exc
    return parsed.isoformat(timespec="seconds")


def _district(address: str) -> str | None:
    return next(
        (
            district
            for prefix, district in DISTRICT_BY_ADDRESS_PREFIX.items()
            if address.startswith(prefix)
        ),
        None,
    )


def _json_array(values: Iterable[str]) -> str:
    return json.dumps(list(values), ensure_ascii=False, separators=(",", ":"))


def _validate_items(
    document: dict[str, object],
    *,
    path: Path,
    content_type_id: int,
) -> list[dict[str, object]]:
    items = document.get("items")
    if not isinstance(items, list):
        raise ImportValidationError(f"{path.name}: items는 배열이어야 합니다.")
    declared_total = _required_int(document.get("total"), field="total", filename=path.name)
    if declared_total != len(items):
        raise ImportValidationError(
            f"{path.name}: total={declared_total}과 실제 items={len(items)}가 다릅니다."
        )

    validated: list[dict[str, object]] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ImportValidationError(f"{path.name}: items[{index}]는 객체여야 합니다.")
        missing = EXPECTED_ITEM_FIELDS - item.keys()
        if missing:
            missing_text = ", ".join(sorted(missing))
            raise ImportValidationError(f"{path.name}: items[{index}] 필드 누락: {missing_text}")
        item_type_id = _required_int(
            item["contenttypeid"],
            field=f"items[{index}].contenttypeid",
            filename=path.name,
        )
        if item_type_id != content_type_id:
            raise ImportValidationError(
                f"{path.name}: items[{index}] 유형 {item_type_id}이 문서 유형 "
                f"{content_type_id}과 다릅니다."
            )
        validated.append(item)
    return validated


def _to_place_row(
    item: dict[str, object],
    *,
    content_type_id: int,
    filename: str,
    imported_at: str,
) -> dict[str, object]:
    address = str(item["addr1"])
    district = _district(address)
    content_id = str(item["contentid"])
    title = str(item["title"])
    if not content_id or not title:
        raise ImportValidationError(f"{filename}: contentid와 title은 비어 있을 수 없습니다.")

    map_level_text = str(item["mlevel"])
    map_level = (
        _required_int(map_level_text, field="mlevel", filename=filename) if map_level_text else None
    )
    return {
        "content_id": content_id,
        "content_type_id": content_type_id,
        "title": title,
        "address": address,
        "address_detail": str(item["addr2"]),
        "zipcode": str(item["zipcode"]),
        "telephone": str(item["tel"]),
        "longitude": _required_float(item["mapx"], field="mapx", filename=filename),
        "latitude": _required_float(item["mapy"], field="mapy", filename=filename),
        "map_level": map_level,
        "area_code": str(item["areacode"]),
        "sigungu_code": str(item["sigungucode"]),
        "legal_region_code": str(item["lDongRegnCd"]),
        "legal_sigungu_code": str(item["lDongSignguCd"]),
        "category1": str(item["cat1"]),
        "category2": str(item["cat2"]),
        "category3": str(item["cat3"]),
        "class_code1": str(item["lclsSystm1"]),
        "class_code2": str(item["lclsSystm2"]),
        "class_code3": str(item["lclsSystm3"]),
        "image_url": str(item["firstimage"]),
        "thumbnail_url": str(item["firstimage2"]),
        "copyright_code": str(item["cpyrhtDivCd"]),
        "source_created_at": _source_timestamp(
            item["createdtime"], field="createdtime", filename=filename
        ),
        "source_modified_at": _source_timestamp(
            item["modifiedtime"], field="modifiedtime", filename=filename
        ),
        "district": district,
        "space_type": None,
        "moods_json": "[]",
        "activities_json": _json_array(ACTIVITIES_BY_CONTENT_TYPE_ID[content_type_id]),
        "keywords_json": "[]",
        "description": None,
        "estimated_stay_minutes": None,
        "estimated_cost": None,
        "rain_suitability": None,
        "conversation_score": None,
        "photo_score": None,
        "is_recommendable": int(district is not None),
        "created_at": imported_at,
        "updated_at": imported_at,
    }


def load_source_rows(source_dir: Path) -> tuple[list[dict[str, object]], int, int]:
    """Load and validate every JSON file, returning rows and source/skip counts."""
    paths = sorted(source_dir.glob("*.json"))
    if not paths:
        raise ImportValidationError(f"JSON 파일이 없습니다: {source_dir}")

    imported_at = datetime.now(SEOUL).isoformat(timespec="seconds")
    rows: list[dict[str, object]] = []
    source_items = 0
    skipped = 0
    seen_content_ids: set[str] = set()

    for path in paths:
        document = _load_document(path)
        content_type_id = _required_int(
            document.get("contentTypeId"), field="contentTypeId", filename=path.name
        )
        allowed_ids = RECOMMENDABLE_CONTENT_TYPE_IDS | EXCLUDED_CONTENT_TYPE_IDS
        if content_type_id not in allowed_ids:
            raise ImportValidationError(
                f"{path.name}: 지원하지 않는 contentTypeId입니다: {content_type_id}"
            )
        items = _validate_items(document, path=path, content_type_id=content_type_id)
        source_items += len(items)
        if content_type_id in EXCLUDED_CONTENT_TYPE_IDS:
            skipped += len(items)
            continue

        for item in items:
            row = _to_place_row(
                item,
                content_type_id=content_type_id,
                filename=path.name,
                imported_at=imported_at,
            )
            content_id = str(row["content_id"])
            if content_id in seen_content_ids:
                raise ImportValidationError(f"중복 contentid가 있습니다: {content_id}")
            seen_content_ids.add(content_id)
            rows.append(row)

    return rows, source_items, skipped


def _sync_database_url(database_url: str) -> str:
    if database_url.startswith("sqlite+aiosqlite:"):
        return database_url.replace("sqlite+aiosqlite:", "sqlite:", 1)
    if database_url.startswith("sqlite:"):
        return database_url
    raise ImportValidationError("장소 적재는 SQLite DATABASE_URL만 지원합니다.")


def _chunks(rows: list[dict[str, object]]) -> Iterable[list[dict[str, object]]]:
    for start in range(0, len(rows), UPSERT_BATCH_SIZE):
        yield rows[start : start + UPSERT_BATCH_SIZE]


def import_places(source_dir: Path, database_url: str) -> ImportResult:
    """Validate source files and atomically upsert the resulting place rows."""
    rows, source_items, skipped = load_source_rows(source_dir)
    engine = create_engine(_sync_database_url(database_url))
    try:
        with engine.begin() as connection:
            if not inspect(connection).has_table(Place.__tablename__):
                raise ImportValidationError(
                    "places 테이블이 없습니다. 먼저 `python -m alembic upgrade head`를 실행하세요."
                )
            existing_ids = set(connection.scalars(select(Place.content_id)))
            for batch in _chunks(rows):
                statement = sqlite_insert(Place).values(batch)
                update_columns = {
                    column.name: getattr(statement.excluded, column.name)
                    for column in Place.__table__.columns
                    if column.name not in {"content_id", "created_at"}
                }
                connection.execute(
                    statement.on_conflict_do_update(
                        index_elements=[Place.content_id],
                        set_=update_columns,
                    )
                )
    finally:
        engine.dispose()

    loaded_ids = {str(row["content_id"]) for row in rows}
    updated = len(loaded_ids & existing_ids)
    inserted = len(loaded_ids - existing_ids)
    recommendable = sum(int(row["is_recommendable"]) for row in rows)
    return ImportResult(
        source_items=source_items,
        loaded=len(rows),
        inserted=inserted,
        updated=updated,
        skipped=skipped,
        recommendable=recommendable,
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True, help="TourAPI JSON 디렉터리")
    parser.add_argument(
        "--database-url",
        default=os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/sai42.db"),
        help="대상 SQLite URL (기본: DATABASE_URL 또는 backend/data/sai42.db)",
    )
    return parser.parse_args()


def main() -> None:
    """Run the place import and print a machine-readable summary."""
    args = parse_args()
    try:
        result = import_places(args.source_dir.resolve(), args.database_url)
    except ImportValidationError as exc:
        raise SystemExit(f"장소 적재 실패: {exc}") from exc
    print(json.dumps(asdict(result), ensure_ascii=False))


if __name__ == "__main__":
    main()
