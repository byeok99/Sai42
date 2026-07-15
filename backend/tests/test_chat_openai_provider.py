"""OpenAI chat adapter tests without network access."""

import json
import unittest
from types import SimpleNamespace

from app.chat.domain.entities import (
    AiChatTurn,
    AiConversationMemory,
    AiCourseRequest,
    PlaceCandidate,
)
from app.chat.domain.enums import ChatTurnIntent
from app.chat.infrastructure.openai_provider import OpenAiCourseProvider


class RecordingResponses:
    def __init__(self, output: AiChatTurn) -> None:
        self.output = output
        self.arguments: dict[str, object] = {}

    async def parse(self, **kwargs: object) -> SimpleNamespace:
        self.arguments = kwargs
        return SimpleNamespace(output_parsed=self.output)


class ChatOpenAiProviderTest(unittest.IsolatedAsyncioTestCase):
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

        result = await provider.respond(request)

        self.assertEqual(output, result)
        self.assertIs(AiChatTurn, responses.arguments["text_format"])
        self.assertFalse(responses.arguments["store"])
        self.assertNotIn("tools", responses.arguments)
        payload = json.loads(str(responses.arguments["input"]))
        self.assertEqual("최초 요청을 기억함", payload["memory"]["summary"])
        self.assertEqual("1", payload["candidates"][0]["content_id"])


if __name__ == "__main__":
    unittest.main()
