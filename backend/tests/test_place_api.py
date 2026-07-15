"""Place API contract tests against the tracked public SQLite dataset."""

import unittest

import httpx

from app.config import Settings
from app.database import dispose_database_engine
from app.main import create_app


class PlaceApiTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.app = create_app(Settings())

    async def asyncTearDown(self) -> None:
        await dispose_database_engine()

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            transport=httpx.ASGITransport(app=self.app, raise_app_exceptions=False),
            base_url="http://testserver",
        )

    async def test_list_uses_stored_places_and_supports_contract_filters(self) -> None:
        async with self._client() as client:
            response = await client.get("/api/v1/places", params={"size": 5})

        self.assertEqual(200, response.status_code, response.text)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(5, len(body["data"]))
        self.assertEqual(1, body["meta"]["page"])
        self.assertEqual(5, body["meta"]["size"])
        self.assertGreater(body["meta"]["totalElements"], 0)
        first = body["data"][0]
        self.assertEqual(
            {
                "contentId",
                "name",
                "category",
                "district",
                "address",
                "latitude",
                "longitude",
                "imageUrl",
                "indoorOutdoor",
            },
            set(first),
        )

        async with self._client() as client:
            filter_params = {
                "keyword": first["name"],
                "category": first["category"],
                "hasImage": first["imageUrl"] is not None,
            }
            if first["district"] is not None:
                filter_params["district"] = first["district"]
            if first["indoorOutdoor"] is not None:
                filter_params["spaceType"] = first["indoorOutdoor"]
            filtered = await client.get(
                "/api/v1/places",
                params=filter_params,
            )

        self.assertEqual(200, filtered.status_code, filtered.text)
        content_ids = {place["contentId"] for place in filtered.json()["data"]}
        self.assertIn(first["contentId"], content_ids)

    async def test_detail_and_nearby_follow_tourapi_content_id_contract(self) -> None:
        async with self._client() as client:
            listed = await client.get("/api/v1/places", params={"size": 1})
            origin = listed.json()["data"][0]
            detail_response = await client.get(f"/api/v1/places/{origin['contentId']}")
            radius_response = await client.get(
                "/api/v1/places",
                params={
                    "latitude": origin["latitude"],
                    "longitude": origin["longitude"],
                    "radiusKm": 0.1,
                },
            )
            nearby_response = await client.get(
                f"/api/v1/places/{origin['contentId']}/nearby",
                params={"radiusKm": 30, "limit": 3},
            )

        self.assertEqual(200, detail_response.status_code, detail_response.text)
        detail = detail_response.json()["data"]
        self.assertEqual(origin["contentId"], detail["contentId"])
        self.assertIsInstance(detail["contentTypeId"], int)
        self.assertEqual("한국관광공사", detail["source"]["provider"])
        self.assertEqual("공공누리 제3유형", detail["source"]["license"])

        self.assertEqual(200, radius_response.status_code, radius_response.text)
        self.assertIn(
            origin["contentId"],
            {place["contentId"] for place in radius_response.json()["data"]},
        )

        self.assertEqual(200, nearby_response.status_code, nearby_response.text)
        nearby = nearby_response.json()["data"]
        self.assertEqual(origin["contentId"], nearby["origin"]["contentId"])
        self.assertLessEqual(len(nearby["places"]), 3)
        distances = [item["distanceKm"] for item in nearby["places"]]
        self.assertEqual(sorted(distances), distances)
        self.assertTrue(all(distance <= 30 for distance in distances))
        self.assertNotIn(
            origin["contentId"],
            {item["place"]["contentId"] for item in nearby["places"]},
        )

    async def test_radius_category_and_optional_auth_errors_use_common_envelope(self) -> None:
        async with self._client() as client:
            partial_coordinates = await client.get("/api/v1/places", params={"latitude": 36.35})
            invalid_radius = await client.get(
                "/api/v1/places",
                params={"latitude": 36.35, "longitude": 127.38, "radiusKm": 31},
            )
            invalid_category = await client.get(
                "/api/v1/places", params={"category": "NOT_A_CATEGORY"}
            )
            any_district = await client.get("/api/v1/places", params={"district": "ANY"})
            partial_auth = await client.get(
                "/api/v1/places", headers={"X-Profile-Id": "missing-password"}
            )
            missing = await client.get("/api/v1/places/not-a-content-id")

        self.assertEqual("PLACE_INVALID_COORDINATES", partial_coordinates.json()["code"])
        self.assertEqual("PLACE_RADIUS_OUT_OF_RANGE", invalid_radius.json()["code"])
        self.assertEqual("COMMON_VALIDATION_ERROR", invalid_category.json()["code"])
        self.assertEqual("COMMON_VALIDATION_ERROR", any_district.json()["code"])
        self.assertEqual(401, partial_auth.status_code)
        self.assertEqual("AUTH_CREDENTIALS_REQUIRED", partial_auth.json()["code"])
        self.assertEqual(404, missing.status_code)
        self.assertEqual("PLACE_NOT_FOUND", missing.json()["code"])


if __name__ == "__main__":
    unittest.main()
