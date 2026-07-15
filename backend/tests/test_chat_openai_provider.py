"""OpenAI chat adapter tests without network access."""

import asyncio
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.chat.domain.entities import (
    AiChatTurn,
    AiConversationMemory,
    AiCourseRequest,
    PlaceCandidate,
)
from app.chat.domain.enums import ChatTurnIntent
from app.chat.infrastructure.openai_provider import OpenAiCourseProvider
from app.chat.presentation.dependencies import get_ai_course_provider
from app.config import Settings


class RecordingResponses:
    def __init__(self, output: AiChatTurn) -> None:
        self.output = output
        self.arguments: dict[str, object] = {}

    async def parse(self, **kwargs: object) -> SimpleNamespace:
        self.arguments = kwargs
        return SimpleNamespace(
            output_parsed=self.output,
            usage=SimpleNamespace(
                input_tokens=1200,
                input_tokens_details=SimpleNamespace(cached_tokens=512),
                output_tokens=200,
                output_tokens_details=SimpleNamespace(reasoning_tokens=80),
                total_tokens=1400,
            ),
            _request_id="request-test-1",
        )


class ChatOpenAiProviderTest(unittest.IsolatedAsyncioTestCase):
    def test_render_safe_latency_defaults_are_typed(self) -> None:
        settings = Settings()

        self.assertEqual(24, settings.openai_candidate_limit)
        self.assertEqual(0, settings.openai_max_retries)
        self.assertEqual("low", settings.openai_reasoning_effort)
        self.assertEqual("sai42-chat-v1", settings.openai_prompt_cache_key)

    async def test_dependency_reuses_one_app_owned_openai_provider(self) -> None:
        state = SimpleNamespace(
            ai_course_provider=None,
            ai_course_provider_lock=asyncio.Lock(),
        )
        request = SimpleNamespace(app=SimpleNamespace(state=state))
        settings = Settings(openai_api_key="test-key")
        shared_provider = SimpleNamespace()

        with patch(
            "app.chat.presentation.dependencies.OpenAiCourseProvider",
            return_value=shared_provider,
        ) as factory:
            first = await get_ai_course_provider(request, settings)  # type: ignore[arg-type]
            second = await get_ai_course_provider(request, settings)  # type: ignore[arg-type]

        self.assertIs(shared_provider, first)
        self.assertIs(first, second)
        factory.assert_called_once()
        self.assertEqual("low", factory.call_args.kwargs["reasoning_effort"])
        self.assertEqual("sai42-chat-v1", factory.call_args.kwargs["prompt_cache_key"])

    async def test_chat_turn_uses_structured_output_and_application_owned_memory(self) -> None:
        output = AiChatTurn(
            intent=ChatTurnIntent.CASUAL_CONVERSATION,
            assistant_message="반가워요! 오늘은 어떤 이야기를 나눌까요?",
            memory=AiConversationMemory(summary="사용자가 인사함"),
        )
        responses = RecordingResponses(output)
        client = SimpleNamespace(responses=responses)
        provider = OpenAiCourseProvider(
            api_key="test-key",
            model="test-model",
            timeout_seconds=1,
            max_retries=0,
            reasoning_effort="minimal",
            prompt_cache_key="test-chat-v2",
            client=client,  # type: ignore[arg-type]
        )
        candidate = PlaceCandidate(
            content_id="1",
            title="저장된 장소",
            category="ATTRACTION",
            address="대전",
            address_detail="",
            district="YUSEONG_GU",
            latitude=36.35,
            longitude=127.38,
            image_url=None,
            activities=["TOURISM"],
        )
        request = AiCourseRequest(
            conditions={"district": "YUSEONG_GU"},
            weather=None,
            candidates=[candidate],
            user_request="안녕",
            current_draft={"version": 1},
            memory=AiConversationMemory(summary="최초 요청을 기억함"),
        )

        with self.assertLogs("uvicorn.error", level="INFO") as logs:
            result = await provider.respond(request)

        self.assertEqual(output, result)
        self.assertIs(AiChatTurn, responses.arguments["text_format"])
        self.assertFalse(responses.arguments["store"])
        self.assertEqual({"effort": "minimal"}, responses.arguments["reasoning"])
        self.assertEqual(
            "chat_turn:test-chat-v2",
            responses.arguments["prompt_cache_key"],
        )
        self.assertNotIn("tools", responses.arguments)
        payload = json.loads(str(responses.arguments["input"]))
        self.assertEqual("최초 요청을 기억함", payload["memory"]["summary"])
        self.assertEqual("1", payload["candidates"][0]["content_id"])
        self.assertIn("cached_input_tokens=512", " ".join(logs.output))
        self.assertIn("reasoning_tokens=80", " ".join(logs.output))


if __name__ == "__main__":
    unittest.main()
