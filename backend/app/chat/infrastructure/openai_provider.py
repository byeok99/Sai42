"""OpenAI Responses API adapter for constrained course planning."""

import json

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
    RateLimitError,
)

from app.chat.domain.entities import (
    AiCoursePlan,
    AiCourseProviderError,
    AiCourseProviderUnavailable,
    AiCourseRequest,
)

SYSTEM_INSTRUCTIONS = """
당신은 대전 데이트 코스를 만드는 사이봇이다.
반드시 입력의 candidates 배열에 있는 contentId만 선택한다. 후보 밖의 장소, 가상의 장소,
외부 지식으로 찾은 장소는 절대 사용하지 않는다. 서로 다른 장소를 2~4개 선택하고 사용자의
조건과 요청을 최대한 반영한다. 장소의 제목, 카테고리, 주소, 좌표, 활동 정보만 근거로
분위기와 실내외 유형을 판단한다. 이동 동선은 좌표가 가까운 순서를 우선하고 방문 순서에 맞는
자연스러운 한국어 제목, 전체 설명, 장소별 한 줄 멘트를 작성한다. 태그는 #으로 시작한다.
현재 초안이 있으면 사용자의 수정 요청을 반영한 전체 코스를 다시 반환한다. 요청을 완전히
반영할 수 없으면 기존 장소 구성을 최대한 유지하고 warnings에 이유를 한국어로 기록한다.
""".strip()


class OpenAiCourseProvider:
    """Generate schema-validated plans without enabling external model tools."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        timeout_seconds: float,
        max_retries: int,
        client: AsyncOpenAI | None = None,
    ) -> None:
        self.model = model
        self.client = client or AsyncOpenAI(
            api_key=api_key,
            timeout=timeout_seconds,
            max_retries=max_retries,
        )

    async def generate(self, request: AiCourseRequest) -> AiCoursePlan:
        payload = {
            "conditions": request.conditions,
            "weather": request.weather,
            "userRequest": request.user_request,
            "currentDraft": request.current_draft,
            "candidates": [
                candidate.model_dump(mode="json", by_alias=True) for candidate in request.candidates
            ],
        }
        try:
            response = await self.client.responses.parse(
                model=self.model,
                instructions=SYSTEM_INSTRUCTIONS,
                input=json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
                text_format=AiCoursePlan,
                store=False,
            )
        except (APITimeoutError, APIConnectionError, RateLimitError) as exc:
            raise AiCourseProviderUnavailable("OpenAI provider unavailable") from exc
        except APIStatusError as exc:
            if exc.status_code == 429 or exc.status_code >= 500:
                raise AiCourseProviderUnavailable("OpenAI provider unavailable") from exc
            raise AiCourseProviderError("OpenAI provider rejected request") from exc
        except Exception as exc:
            raise AiCourseProviderError("OpenAI provider response invalid") from exc

        if response.output_parsed is None:
            raise AiCourseProviderError("OpenAI provider returned no structured output")
        return response.output_parsed
