"""Tests for TourAPI place validation and idempotent SQLite upserts."""

import json
import tempfile
import unittest
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.database import Base
from app.place.infrastructure.models import Place
from scripts.import_places import import_places


def _item(content_id: str, content_type_id: int, address: str) -> dict[str, str]:
    return {
        "addr1": address,
        "addr2": "",
        "areacode": "",
        "cat1": "",
        "cat2": "",
        "cat3": "",
        "contentid": content_id,
        "contenttypeid": str(content_type_id),
        "createdtime": "20260102030405",
        "firstimage": "",
        "firstimage2": "",
        "cpyrhtDivCd": "Type1",
        "mapx": "127.1",
        "mapy": "36.3",
        "mlevel": "6",
        "modifiedtime": "20260703092341",
        "sigungucode": "",
        "tel": "",
        "title": f"장소 {content_id}",
        "zipcode": "12345",
        "lDongRegnCd": "30",
        "lDongSignguCd": "200",
        "lclsSystm1": "VE",
        "lclsSystm2": "VE02",
        "lclsSystm3": "VE020100",
    }


def _write_document(path: Path, content_type_id: int, items: list[dict[str, str]]) -> None:
    document = {
        "region": "대전_충청권",
        "contentType": "테스트",
        "contentTypeId": content_type_id,
        "total": len(items),
        "items": items,
    }
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")


class ImportPlacesTest(unittest.TestCase):
    def test_imports_allowed_types_skips_festivals_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source_dir = root / "source"
            source_dir.mkdir()
            _write_document(
                source_dir / "관광지.json",
                12,
                [_item("100", 12, "대전광역시 유성구 대학로 1")],
            )
            _write_document(
                source_dir / "축제.json",
                15,
                [_item("200", 15, "대전광역시 중구 중앙로 1")],
            )

            database_path = root / "test.db"
            database_url = f"sqlite:///{database_path.as_posix()}"
            engine = create_engine(database_url)
            Base.metadata.create_all(engine)
            engine.dispose()

            first_result = import_places(source_dir, database_url)
            second_result = import_places(source_dir, database_url)

            self.assertEqual(first_result.source_items, 2)
            self.assertEqual(first_result.loaded, 1)
            self.assertEqual(first_result.inserted, 1)
            self.assertEqual(first_result.skipped, 1)
            self.assertEqual(first_result.recommendable, 1)
            self.assertEqual(second_result.updated, 1)

            engine = create_engine(database_url)
            with Session(engine) as session:
                places = list(session.scalars(select(Place)))
                self.assertEqual(len(places), 1)
                self.assertEqual(places[0].content_id, "100")
                self.assertEqual(places[0].district, "YUSEONG_GU")
                self.assertEqual(places[0].activities_json, '["TOURISM"]')
                self.assertEqual(places[0].source_modified_at, "2026-07-03T09:23:41+09:00")
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
