# API / Service 계약 검증 결과

- 검증일: 2026-07-15
- 기준 문서: `docs/specifications/api.md` (API v3.0)
- 실행 기준: FastAPI `app.openapi()`가 생성한 현재 Swagger schema
- 프론트 기준: `frontend/src/services/api/endpoints.ts`, repository, service, API DTO
- 집중 수정 범위: Chat / CourseDraft 5개 operation과 Chat 확정 응답인 `DateCourseDto`

## 1. 결론 요약

HTTP method와 path의 조합을 operation 1개로 계산했다. 생성과 확정은 성공 상태가 200이 아니라
201이므로 성공 계약 검증에 200과 201을 모두 포함했다.

| 검증 항목                             |    결과 | 판정                                                                   |
| ------------------------------------- | ------: | ---------------------------------------------------------------------- |
| 백엔드 Swagger operation              | 32 / 32 | 모두 router에 등록됨                                                   |
| 프론트 endpoint path template         | 32 / 32 | 모든 Swagger path를 표현함                                             |
| 프론트 repository/service 호출 함수   | 29 / 32 | `health`, `meta/options`, `weather` 3개 없음                           |
| Chat endpoint path/repository/service |   5 / 5 | 모두 연결됨                                                            |
| Chat 요청·응답 DTO와 성공 code        |   5 / 5 | 이번 작업에서 일치시킴                                                 |
| Chat mapper 런타임 계약 검사          |   5 / 5 | envelope, data key, primitive, enum, 중첩 DTO 검사                     |
| 프론트 전체 TypeScript 검사           |    실패 | Chat 오류는 0개, 다른 5개 repository 영역의 기존 `implicit any`가 남음 |

즉, 백엔드는 Swagger에 노출한 32개 operation을 모두 구현했다. 프론트는 모든 path 상수를
가지고 있지만 실제 repository/service 호출은 29개이며, 그중 Chat 5개는 현재 계약과 일치한다.
나머지 도메인은 함수가 존재하더라도 여러 요청·응답 DTO가 Swagger와 다르므로 아래의
“호출 함수 존재”를 “계약 구현 완료”로 해석하면 안 된다.

## 2. Chat endpoint 1:1 대응 결과

모든 성공 응답의 공통 envelope key는 다음과 같다.

```text
success, code, message, data, meta, timestamp, traceId
```

| Method / path                              | 성공 | Request DTO                    | 성공 `data` key / 값                                                                         | Repository → Service                | 결과 |
| ------------------------------------------ | ---: | ------------------------------ | -------------------------------------------------------------------------------------------- | ----------------------------------- | ---- |
| `POST /chat/sessions`                      |  201 | `CreateChatSessionRequestDto`  | `sessionId`, `status`, `assistantMessage`, `courseDraft`; code=`CHAT_SESSION_CREATED`        | `createSession` → `createSession`   | 일치 |
| `GET /chat/sessions/{sessionId}`           |  200 | 없음                           | `sessionId`, `status`, `conditions`, `messages`, `courseDraft`; code=`COMMON_OK`             | `getSession` → `getSession`         | 일치 |
| `POST /chat/sessions/{sessionId}/messages` |  200 | `SendChatMessageRequestDto`    | `userMessage`, `assistantMessage`, `changeSummary`, `courseDraft`; code=`CHAT_DRAFT_UPDATED` | `sendMessage` → `sendMessage`       | 일치 |
| `POST /chat/sessions/{sessionId}/confirm`  |  201 | `ConfirmChatSessionRequestDto` | `DateCourseDto`; code=`CHAT_SESSION_CONFIRMED`                                               | `confirmSession` → `confirmSession` | 일치 |
| `DELETE /chat/sessions/{sessionId}`        |  200 | 없음                           | `null`; code=`CHAT_SESSION_DISCARDED`                                                        | `discardSession` → `discardSession` | 일치 |

### 2.1 수정한 프론트 계약

| 기존 불일치                                             | 수정 결과                                                                                          |
| ------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| 최초 생성 요청에 선택 필드 `initialMessage`가 없음      | `initialMessage?: string \| null` 추가                                                             |
| 모든 응답을 하나의 잘못된 `ChatSessionDto`로 처리       | 생성, 조회, 메시지, 확정, 폐기 DTO를 endpoint별로 분리                                             |
| 조회 응답을 `id`, `draft`, `draftVersion`으로 선언      | API DTO는 `sessionId`, `courseDraft` 그대로 선언하고 service mapper에서 프론트 모델로 변환         |
| 메시지 role을 소문자 `user`, `assistant`로 선언         | Swagger enum인 `USER`, `ASSISTANT`로 수정                                                          |
| 메시지 요청이 `{content}`                               | `{message, expectedDraftVersion}` 또는 `{quickAction, expectedDraftVersion}`의 배타 union으로 수정 |
| 확정 요청 body가 없음                                   | `{draftId, expectedVersion}` 전달                                                                  |
| 확정 응답을 `ChatSessionDto`로 선언                     | 실제 `DateCourseDto`로 수정                                                                        |
| 폐기 응답을 `unknown`으로 선언                          | `null`로 수정                                                                                      |
| 초안과 확정 코스의 중첩 구조가 `unknown` 또는 축약 구조 | 조건, 날씨, 장소 snapshot, 지도, 진행률까지 구체 DTO 선언                                          |
| 성공 envelope의 `success`가 일반 `boolean`              | Swagger의 상수 값과 같은 literal `true`로 수정                                                     |

### 2.2 Mapper 동작

`frontend/src/services/mappers/chatMapper.ts`는 fetch 결과를 바로 신뢰하지 않고 다음을 검사한다.

- endpoint별 정확한 성공 `code`
- 공통 envelope의 정확한 key 집합과 `meta=null`
- endpoint별 `data`의 정확한 key 집합
- string, number, integer, boolean, null, array 타입
- Chat, 공통 조건, 장소, 날씨, 코스 상태 enum 값
- 코스 장소 2~4개 제약
- 날짜, 시간, datetime의 기본 문자열 형식
- 생성·조회·수정·확정·폐기 응답의 모든 중첩 DTO

검증 후 service 모델에는 다음 변환을 적용한다.

| API DTO                                           | Service 모델                   |
| ------------------------------------------------- | ------------------------------ |
| `sessionId`                                       | `id`                           |
| `courseDraft`                                     | `draft`                        |
| `courseDraft.version`                             | `draftVersion`                 |
| `changeSummary.changed`, `changeSummary.warnings` | `changed`, `warnings`로 평탄화 |
| `conditions.startTime`의 `HH:mm:ss` 가능 값       | `HH:mm`으로 정규화             |

API DTO 자체는 Swagger key를 그대로 유지하므로 네트워크 계약과 프론트 내부 모델을 혼동하지
않는다. 알 수 없는 key, 누락 key, 잘못된 enum 또는 타입이 오면 mapper가 `TypeError`를 발생시켜
API drift를 조기에 드러낸다.

## 3. 백엔드 Chat service와 repository 대응

### 3.1 `ChatRepository`

| Repository 함수             | 호출하는 service 흐름                          | 판정               |
| --------------------------- | ---------------------------------------------- | ------------------ |
| `find_session`              | 조회, 메시지 수정, 확정, 폐기의 소유 세션 확인 | 사용 중            |
| `list_recommendable_places` | 최초 생성, 메시지 수정 시 후보 재조회          | 사용 중            |
| `find_places`               | 확정 직전 초안의 모든 `contentId` 재검증       | 사용 중            |
| `add_session`               | 최초 생성                                      | 사용 중            |
| `commit`                    | 생성, 메시지 수정, 확정, 폐기                  | 사용 중            |
| `rollback`                  | 확정 중 `IntegrityError` 처리                  | 사용 중            |
| 기존 `flush`                | 어떤 service에서도 호출하지 않음               | 이번 작업에서 제거 |

Chat service가 함께 사용하는 `DateCourseRepository` 연결은 다음과 같다.

- `find_active_course`: 생성 전과 확정 전 중복 활성 코스 확인
- `add_course`: 확정 시 `DateCourse`와 2~4개 장소 snapshot 저장
- `list_course_places`, `heart_counts`: 확정 결과 `DateCourseDto` 렌더링 과정에서 간접 호출

### 3.2 백엔드 계약 보정

| 항목                            | 기존                         | 수정                               |
| ------------------------------- | ---------------------------- | ---------------------------------- |
| `conditions.startTime` 응답     | Pydantic 기본값인 `HH:mm:ss` | 명세의 `HH:mm` serializer 적용     |
| `courseDraft.weather` Swagger   | 임의 object                  | `WeatherSummaryDto \| null` `$ref` |
| `DateCourseDto.weather` Swagger | 임의 object                  | `WeatherSummaryDto \| null` `$ref` |
| 초안/확정 코스 장소 수 schema   | 단순 array                   | OpenAPI `minItems=2`, `maxItems=4` |
| AI 코스 제목 길이               | 최대 80자                    | 공통 명세대로 최대 60자            |

## 4. 전체 Swagger operation의 프론트 구현 상태

| 영역               | Swagger operation | endpoint path | repository/service 함수 | DTO 계약 상태          |
| ------------------ | ----------------: | ------------: | ----------------------: | ---------------------- |
| Common             |                 2 |             2 |                       0 | 미구현                 |
| Identity           |                 4 |             4 |                       4 | 응답 DTO 불일치        |
| Place              |                 3 |             3 |                       3 | query/응답 DTO 불일치  |
| Chat               |                 5 |             5 |                       5 | 일치, mapper 적용      |
| Current DateCourse |                 5 |             5 |                       5 | 요청·응답 DTO 불일치   |
| Community          |                 8 |             8 |                       8 | 일부만 일치            |
| Ranking            |                 1 |             1 |                       1 | 응답 DTO 불일치        |
| History            |                 3 |             3 |                       3 | 요청·응답 DTO 불일치   |
| Weather            |                 1 |             1 |                       0 | 미구현                 |
| 합계               |                32 |            32 |                      29 | Chat 외 후속 정비 필요 |

### 4.1 구현되지 않은 프론트 호출

다음 3개는 endpoint 상수만 있고 repository/service/DTO 호출 흐름이 없다.

1. `GET /health`
2. `GET /meta/options`
3. `GET /weather`

### 4.2 호출 함수는 있지만 Swagger와 다른 영역

#### Identity

- 닉네임 추천의 실제 `data`는 `{suggestions: string[]}`이지만 프론트는
  `{nickname: string}[]`로 선언했다.
- 프로필 생성 응답은 `ProfileCreatedDto`, 검증 응답은 `ProfileVerifiedDto`, 내 프로필은
  `MyProfileDto`인데 세 endpoint 모두 `ProfileMeDto` 하나로 처리한다.
- 실제 식별자 key는 `profileId`지만 프론트 `ProfileMeDto`는 `id`다.

#### Place

- 장소명 key는 `name`인데 프론트는 `title`이다.
- 실제 null 가능 필드를 optional 필드로 선언했고 `indoorOutdoor`, `addressDetail`, `telephone`,
  `source` 구조를 정확히 표현하지 않는다.
- 주변 장소 응답은 `NearbyPlacesDto {origin, places[{place, distanceKm}]}`인데 프론트는
  `PlaceSummaryDto[]`로 처리한다.

#### Current DateCourse

- 현재 코스 조회는 `DateCourseDto`다.
- 장소 완료는 `DateCourseProgressDto`, 하트/취소는 `CoursePlaceHeartDto`, 데이트 종료는
  `CompleteDateCourseDto`인데 모두 `CurrentCourseDto`로 처리한다.
- 데이트 종료 request key는 `oneLineComment`인데 프론트는 `completionComment`를 보낸다.

#### Community

- 게시글 생성 request key는 `dateCourseId`인데 프론트는 `courseId`를 보낸다.
- 목록의 `mainDistrict`, `tags`, 상세의 `owner`, `date`, `conditions`, `map` 및 중첩 장소 구조가
  누락되거나 다른 이름이다.
- 삭제 성공 `data`는 `null`인데 `unknown`으로 선언했다.
- 게시글 시작은 `{date, startTime}` body가 필수이고 `StartCommunityCourseDto`를 반환하지만,
  프론트는 body 없이 요청하고 응답을 `unknown`으로 처리한다.
- 좋아요/취소의 `CommunityLikeDto` key는 현재 프론트 DTO와 일치한다.

#### Ranking

- 실제 응답은 `{masters: DateMasterDto[]}`이며 원소 key는 `rank`, `profileId`, `nickname`,
  `publishedCourseCount`, `receivedLikeCount`다.
- 프론트는 이를 `CommunityPostSummaryDto[]`로 처리한다.

#### History

- 목록은 `HistoryCourseSummaryDto[]`, 상세은 `DateCourseDto`인데 모두 `CurrentCourseDto`로 처리한다.
- 재진행은 `{date, startTime}` body가 필수이나 프론트는 body 없이 요청한다.

## 5. 아직 남은 Chat 관련 구현 한계

다음 항목은 DTO mapper로 해결할 수 없는 동작 또는 화면 통합 범위다.

- `chatService`를 호출하는 Vue 화면/Pinia 흐름이 아직 없다. API 계층은 호출 가능하지만 실제
  사용자 UI 흐름은 구현되지 않았다.
- `chat_sessions.expires_at`은 저장하지만 만료 시 `EXPIRED`로 전환하거나 접근을 차단하는 Chat
  service 로직은 없다.
- `REDUCE_ROUTE`는 서버의 결정적 거리 최적화가 아니라 AI 요청 문구에 의존한다. 다른 빠른 수정도
  후보 점수 가중치와 AI 응답에 의존하므로 행동을 절대 보장하는 알고리즘은 아니다.
- 프론트에는 별도 테스트 runner가 없어 mapper의 독립 unit test는 추가하지 못했다. 대신
  TypeScript compiler, ESLint, Oxlint와 백엔드 실제 JSON 계약 테스트로 검증했다.

## 6. 실행한 검증

| 명령                                                                                                 | 결과                                                                |
| ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `backend/.venv/Scripts/python.exe -m unittest tests.test_chat_api`                                   | 4 tests, OK                                                         |
| `backend/.venv/Scripts/python.exe -m unittest discover -s tests`                                     | 36 tests, OK                                                        |
| `backend/.venv/Scripts/ruff.exe check app/chat app/course/application/dto.py tests/test_chat_api.py` | 통과                                                                |
| FastAPI `app.openapi()` schema 확인                                                                  | Chat 5개 operation, weather `$ref`, 장소 `minItems/maxItems` 확인   |
| DTO 직렬화 확인                                                                                      | `conditions.startTime == "14:00"` 확인                              |
| 변경 프론트 파일 ESLint                                                                              | 통과                                                                |
| 변경 프론트 파일 Oxlint                                                                              | 통과                                                                |
| 변경 프론트 파일 Prettier check                                                                      | 통과                                                                |
| `npm.cmd run build-only`                                                                             | Vite production build 통과                                          |
| `npm.cmd run type-check`                                                                             | 실패: Chat 오류는 없고 다른 repository의 기존 `implicit any`만 남음 |

현재 전체 타입 검사를 막는 파일은 다음과 같다.

- `frontend/src/services/repositories/communityRepository.ts`
- `frontend/src/services/repositories/courseRepository.ts`
- `frontend/src/services/repositories/historyRepository.ts`
- `frontend/src/services/repositories/identityRepository.ts`
- `frontend/src/services/repositories/placeRepository.ts`

이 파일들은 단순 annotation뿐 아니라 위에 기록한 실제 DTO 계약도 함께 고쳐야 하므로 Chat 작업에
섞어 임의로 정상 처리된 것처럼 만들지 않았다.
