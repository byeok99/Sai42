"""Contract tests for common envelopes, tracing, errors, and OpenAPI."""

import unittest
from typing import Annotated
from uuid import UUID, uuid4

import httpx
from fastapi import Body
from pydantic import BaseModel, Field

from app.config import Settings
from app.database import dispose_database_engine
from app.main import create_app


class PasswordBody(BaseModel):
    """Test-only input used to verify sensitive-value redaction."""

    password: Annotated[str, Field(pattern=r"^\d{4}$")]


class CommonApiTest(unittest.IsolatedAsyncioTestCase):
    async def asyncTearDown(self) -> None:
        await dispose_database_engine()

    async def _client(self, app):
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        return httpx.AsyncClient(transport=transport, base_url="http://testserver")

    async def test_health_and_options_follow_the_common_contract(self) -> None:
        app = create_app(Settings())
        request_id = str(uuid4())

        async with await self._client(app) as client:
            health_response = await client.get(
                "/api/v1/health",
                headers={"X-Request-Id": request_id},
            )
            options_response = await client.get("/api/v1/meta/options")
            invalid_request_id_response = await client.get(
                "/api/v1/meta/options",
                headers={"X-Request-Id": "not-a-uuid"},
            )

        self.assertEqual(health_response.status_code, 200)
        health = health_response.json()
        self.assertTrue(health["success"])
        self.assertEqual(health["code"], "COMMON_OK")
        self.assertEqual(health["traceId"], request_id)
        self.assertEqual(health_response.headers["X-Request-Id"], request_id)
        self.assertEqual(health["data"]["database"], "UP")
        self.assertEqual(health["data"]["aiProvider"], "NOT_CONFIGURED")
        self.assertEqual(health["data"]["weatherProvider"], "NOT_CONFIGURED")
        self.assertEqual(health["timestamp"][-6:], "+09:00")

        self.assertEqual(options_response.status_code, 200)
        options = options_response.json()["data"]
        self.assertEqual(options["timeSlots"][0], {"value": "MORNING", "label": "오전"})
        self.assertIn({"value": "ANY", "label": "상관없음"}, options["districts"])
        self.assertEqual(len(options["activityTypes"]), 6)
        UUID(options_response.json()["traceId"])
        self.assertEqual(invalid_request_id_response.status_code, 422)
        self.assertEqual(
            invalid_request_id_response.json()["code"],
            "COMMON_VALIDATION_ERROR",
        )

    async def test_swagger_and_openapi_publish_common_and_error_schemas(self) -> None:
        app = create_app(Settings())

        async with await self._client(app) as client:
            docs_response = await client.get("/docs")
            redoc_response = await client.get("/redoc")
            schema_response = await client.get("/openapi.json")

        self.assertEqual(docs_response.status_code, 200)
        self.assertEqual(redoc_response.status_code, 200)
        schema = schema_response.json()
        self.assertEqual(
            set(schema["paths"]),
            {
                "/api/v1/health",
                "/api/v1/meta/options",
                "/api/v1/auth/nickname-suggestions",
                "/api/v1/auth/profiles",
                "/api/v1/auth/verify",
                "/api/v1/profiles/me",
                "/api/v1/places",
                "/api/v1/places/{contentId}",
                "/api/v1/places/{contentId}/nearby",
                "/api/v1/date-courses/current",
                "/api/v1/date-courses/current/places/{coursePlaceId}/complete",
                "/api/v1/date-courses/current/places/{coursePlaceId}/heart",
                "/api/v1/date-courses/current/complete",
            },
        )
        schemas = schema["components"]["schemas"]
        self.assertIn("ErrorResponseDto", schemas)
        self.assertIn("BaseDto_HealthDto_", schemas)
        self.assertEqual(
            set(schemas["ErrorResponseDto"]["required"]),
            {"success", "code", "message", "errors", "timestamp", "traceId"},
        )
        self.assertEqual(
            set(schemas["BaseDto_HealthDto_"]["required"]),
            {"success", "code", "message", "data", "meta", "timestamp", "traceId"},
        )
        self.assertEqual(
            set(schema["paths"]["/api/v1/health"]["get"]["responses"]),
            {"200", "400", "422", "500"},
        )
        request_id_parameter = schema["paths"]["/api/v1/health"]["get"]["parameters"][0]
        self.assertEqual(request_id_parameter["name"], "X-Request-Id")
        self.assertEqual(request_id_parameter["in"], "header")

    async def test_validation_and_unexpected_errors_are_sanitized(self) -> None:
        app = create_app(Settings())

        @app.post("/_test/password")
        async def validate_password(payload: Annotated[PasswordBody, Body()]):
            return payload

        @app.get("/_test/error")
        async def raise_error():
            raise RuntimeError("sensitive internal detail")

        async with await self._client(app) as client:
            validation_response = await client.post(
                "/_test/password",
                json={"password": "not-a-pin"},
            )
            json_response = await client.post(
                "/_test/password",
                content="{invalid",
                headers={"Content-Type": "application/json"},
            )
            error_response = await client.get(
                "/_test/error",
                headers={"Origin": "http://localhost:5173"},
            )
            not_found_response = await client.get("/_test/missing")

        self.assertEqual(validation_response.status_code, 422)
        validation = validation_response.json()
        self.assertEqual(validation["code"], "COMMON_VALIDATION_ERROR")
        self.assertEqual(validation["errors"][0]["field"], "password")
        self.assertIsNone(validation["errors"][0]["rejectedValue"])
        self.assertNotIn("not-a-pin", validation_response.text)

        self.assertEqual(json_response.status_code, 400)
        self.assertEqual(json_response.json()["code"], "COMMON_BAD_REQUEST")
        self.assertEqual(error_response.status_code, 500)
        self.assertEqual(error_response.json()["code"], "COMMON_INTERNAL_SERVER_ERROR")
        self.assertNotIn("sensitive internal detail", error_response.text)
        self.assertEqual(
            error_response.headers["access-control-allow-origin"],
            "http://localhost:5173",
        )
        self.assertEqual(not_found_response.status_code, 404)
        self.assertEqual(not_found_response.json()["code"], "COMMON_NOT_FOUND")

    async def test_cors_preflight_allows_declared_headers_only_for_configured_origin(self) -> None:
        app = create_app(Settings(cors_allowed_origins="https://sai42.netlify.app"))

        async with await self._client(app) as client:
            response = await client.options(
                "/api/v1/health",
                headers={
                    "Origin": "https://sai42.netlify.app",
                    "Access-Control-Request-Method": "GET",
                    "Access-Control-Request-Headers": "X-Profile-Id,X-User-Password",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["access-control-allow-origin"],
            "https://sai42.netlify.app",
        )
        self.assertEqual(response.headers.get("access-control-allow-credentials"), None)


if __name__ == "__main__":
    unittest.main()
