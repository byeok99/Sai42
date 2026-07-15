# 사이42 API 명세

> 원본: [`API-v3.0.pdf`](../sources/API-v3.0.pdf), v3.0 (63쪽)
>
> 변환 기준일: 2026-07-15
>
> API prefix: `/api/v1`
>
> 문서 성격: 원본을 구조화하고 2026-07-15 확정 결정을 반영한 구현 기준 명세

PDF 원본보다 이 문서의 확정 계약을 우선한다. 평점은 사용하지 않으며, 장소 식별자는 TourAPI `contentId`, 랭킹은 게시글 좋아요와 게시일을 기준으로 한다.

## 1. 전역 계약

| 항목 | 값 |
|---|---|
| Backend | FastAPI + SQLAlchemy + SQLite |
| Content-Type | `application/json` |
| 시간대 | `Asia/Seoul` |
| 날짜 | `YYYY-MM-DD` |
| 일시 | ISO 8601 + timezone |
| 서비스 ID | UUID v4 문자열 |
| 장소 ID | TourAPI `contentId` 문자열 |
| 요청·응답 필드 | `camelCase` |
| DB 컬럼 | `snake_case` |
| 사용자 검증 | `X-Profile-Id` + `X-User-Password` |

### 1.1 명세 수정 정책

- 비밀번호는 암호화하지 않고 숫자 4자리 평문으로 저장하며 직접 비교한다.
- 닉네임 및 비밀번호 수정 API는 제공하지 않는다.
- 사용자 성향 도메인과 저장 API는 없다. 코스 생성 때마다 전체 조건을 전달한다.
- 축제 도메인, API, DTO, 검증, 추천 로직은 사용하지 않는다.
- 현재 데이트 취소 API는 없다. `ACTIVE` 코스는 완료해야만 다음 코스를 만들 수 있다.

### 1.2 최종 사용자 흐름

```text
시작
  -> 닉네임 추천 / 신규 프로필 등록 / 기존 프로필 검증
  -> 매번 데이트 조건 입력
  -> 날씨 + 장소 후보 + AI 최초 코스
  -> 자연어 코스 조정
  -> 코스 확정
  -> 현재 데이트에서 장소별 하트
  -> 데이트 종료 + 한 줄 코멘트
  -> 과거 데이트 저장 + 랭킹보드 자동 공개
```

### 1.3 익명 프로필 정책

- 이메일, 실명, 전화번호는 수집하지 않는다.
- 닉네임과 숫자 4자리 비밀번호만 등록한다.
- 닉네임은 서비스 내에서 중복될 수 없다.
- Access Token, Refresh Token, Cookie Session을 발급하지 않는다.
- 보호 API는 매 요청마다 프로필 ID와 비밀번호를 검증한다.
- 비밀번호 분실 복구 기능은 없다.
- 평문 저장은 교육 목적이며 실제 운영 서비스에 부적합하다.

### 1.4 완료 코스와 게시글

- `DateCourse`는 실제 데이트 기록이다.
- `CommunityPost`는 완료 코스를 랭킹보드에 공개하는 게시물이다.
- 종료 시 코스 완료와 게시글 자동 생성을 하나의 트랜잭션으로 처리한다.
- 완료 코스의 장소, 시간, 추천 문구는 변경할 수 없다.
- 게시글은 한 줄 코멘트만 수정할 수 있다.
- 게시글을 논리 삭제해도 과거 데이트 기록은 유지한다.

## 2. 도메인 책임

| 도메인 | 책임 | 주요 모델 |
|---|---|---|
| Common | 공통 응답, 예외, 페이징, 옵션, 요청 추적 | `BaseDto`, `ErrorResponseDto` |
| Identity | 익명 프로필 등록, 입장, 요청별 검증 | `UserProfile` |
| Place | 공공데이터 장소와 지도 데이터 조회 | `Place` |
| Weather | 외부 날씨 조회와 추천용 요약 | `WeatherSnapshot` |
| Chat | AI 대화 세션, 최초 생성, 자연어 조정 | `ChatSession`, `ChatMessage` |
| CourseDraft | 확정 전 AI 코스 초안 | `CourseDraft`, `CourseDraftPlace` |
| DateCourse | 현재·완료 코스, 장소 하트, 종료 | `DateCourse`, `DateCoursePlace` |
| Community | 완료 코스 공개, 게시글, 게시글 좋아요 | `CommunityPost`, `CommunityLike` |
| Ranking | 공개 코스와 데이트 마스터 집계 | `RankingReadModel` |
| History | 본인의 완료 코스 조회 및 재진행 | `DateCourseReadModel` |

## 3. Enum

| Enum | 값 |
|---|---|
| `DateCourseStatus` | `ACTIVE`, `COMPLETED` |
| `CourseSourceType` | `AI_CHAT`, `RANKING_COPY`, `HISTORY_RESTART` |
| `ChatSessionStatus` | `ACTIVE`, `CONFIRMED`, `DISCARDED`, `EXPIRED` |
| `CommunityPostStatus` | `PUBLISHED`, `DELETED` |
| `TimeSlot` | `MORNING`, `AFTERNOON`, `FULL_DAY` |
| `District` | `DONG_GU`, `JUNG_GU`, `SEO_GU`, `YUSEONG_GU`, `DAEDEOK_GU`, `ANY` |
| `SpaceType` | `INDOOR`, `OUTDOOR`, `ANY` |
| `Mood` | `QUIET`, `EMOTIONAL`, `LIVELY`, `SPECIAL` |
| `ActivityType` | `TOURISM`, `CULTURE_EXHIBITION`, `FOOD`, `SHOPPING`, `WALK`, `LEPORTS` |
| `ScheduleDensity` | `RELAXED`, `NORMAL`, `TIGHT` |
| `Transportation` | `WALK`, `PUBLIC_TRANSIT`, `CAR`, `FLEXIBLE` |
| `PlaceCategory` | `ATTRACTION`, `CULTURAL_FACILITY`, `TRAVEL_COURSE`, `LEPORTS`, `ACCOMMODATION`, `SHOPPING`, `RESTAURANT` |
| `CourseEditAction` | `CHANGE_CAFE`, `ADD_NIGHT_VIEW`, `REDUCE_ROUTE`, `INCREASE_INDOOR`, `REGENERATE` |
| `RankingSort` | `POPULAR`, `LATEST` |

`CANCELED` 코스 상태와 축제·공연 활동은 사용하지 않는다.

## 4. 공통 응답

### 4.1 성공 응답 `BaseDto<T>`

```json
{
  "success": true,
  "code": "COMMON_OK",
  "message": "요청이 성공적으로 처리되었습니다.",
  "data": {},
  "meta": null,
  "timestamp": "2026-07-14T14:30:00+09:00",
  "traceId": "9bb43f9d-a680-42ca-93bf-8a87a91aaef2"
}
```

| 필드 | 타입 | 필수 | 의미 |
|---|---|---:|---|
| `success` | boolean | Y | 항상 `true` |
| `code` | string | Y | 애플리케이션 응답 코드 |
| `message` | string | Y | 사용자 표시 가능 메시지 |
| `data` | `T \| null` | Y | 실제 응답 데이터 |
| `meta` | `PageMetaDto \| null` | Y | 페이징 등 부가 정보 |
| `timestamp` | datetime | Y | 서버 응답 시각 |
| `traceId` | UUID string | Y | 요청 추적 ID |

### 4.2 `PageMetaDto`

```json
{
  "page": 1,
  "size": 20,
  "totalElements": 57,
  "totalPages": 3,
  "hasNext": true,
  "hasPrevious": false
}
```

페이지 번호는 1부터 시작한다.

### 4.3 실패 응답 `ErrorResponseDto`

```json
{
  "success": false,
  "code": "AUTH_INVALID_CREDENTIALS",
  "message": "사용자 정보 또는 비밀번호가 올바르지 않습니다.",
  "errors": [
    {
      "field": null,
      "reason": "INVALID_CREDENTIALS",
      "rejectedValue": null
    }
  ],
  "timestamp": "2026-07-14T14:31:00+09:00",
  "traceId": "b4cd1da0-3c6c-4e80-a4ea-d74f0edc46e1"
}
```

`errors`는 상세 오류가 없을 때 빈 배열이다. 비밀번호는 `rejectedValue`, 로그, trace에 절대 포함하지 않는다. Pydantic 모델은 alias generator로 `snake_case` 필드를 `camelCase`로 직렬화하고 `populate_by_name`, `from_attributes`를 활성화한다.

## 5. 인증과 요청 규칙

### 5.1 헤더

```http
X-Profile-Id: 88a6f640-72fb-4e67-a05f-47b2809b76ff
X-User-Password: 0420
X-Request-Id: optional-uuid
Idempotency-Key: optional-uuid
```

| 헤더 | 필수 범위 | 의미 |
|---|---|---|
| `X-Profile-Id` | 보호 API | 프로필 UUID |
| `X-User-Password` | 보호 API | 숫자 4자리 비밀번호 |
| `X-Request-Id` | 선택 | 요청 추적 ID |
| `Idempotency-Key` | 일부 POST 권장 | 중복 실행 방지 |

검증 순서:

1. 두 인증 헤더의 존재를 확인한다.
2. 프로필 ID의 UUID 형식을 확인한다.
3. 프로필을 조회한다.
4. 비밀번호의 숫자 4자리 형식을 확인한다.
5. DB의 평문 `password`와 직접 비교한다.
6. 성공 시 `current_profile`을 주입한다.
7. 소유 리소스 접근이면 소유자 ID를 확인한다.

| 상황 | HTTP | 코드 |
|---|---:|---|
| 헤더 누락 | 401 | `AUTH_CREDENTIALS_REQUIRED` |
| profileId 형식 오류 | 401 | `AUTH_INVALID_PROFILE_ID_FORMAT` |
| 프로필 없음 또는 비밀번호 불일치 | 401 | `AUTH_INVALID_CREDENTIALS` |
| 반복 실패 제한 | 429 | `AUTH_TOO_MANY_ATTEMPTS` |
| 타 사용자 리소스 | 403 | `AUTH_FORBIDDEN` |

프로필 존재 여부와 비밀번호 오류는 구분해 노출하지 않는다.

### 5.2 선택 인증

장소, 날씨, 랭킹 조회는 헤더 없이 호출할 수 있다.

- 두 헤더 없음: 익명 조회
- 두 헤더 있음: 검증 후 `likedByMe`, `owner` 등 개인화 필드 포함
- 하나만 있음: 401
- 둘 다 있으나 불일치: 401

### 5.3 비밀번호와 브라우저 저장

- HTTPS를 사용한다.
- 비밀번호를 URL path나 query string에 넣지 않는다.
- access log에서 `X-User-Password`를 마스킹한다.
- `localStorage`에 저장하지 않는다.
- Pinia 메모리 또는 `sessionStorage`만 사용하며 탭 종료·퇴장 시 삭제한다.
- profileId와 IP 기준 rate limit을 적용한다.
- 401 응답 시 프론트는 저장된 profileId와 password를 제거한다.
- 로그아웃 API는 없다.

### 5.4 CORS와 멱등성

`allow_credentials=false`이며 `Content-Type`, `X-Profile-Id`, `X-User-Password`, `X-Request-Id`, `Idempotency-Key`를 허용한다.

다음 작업은 `Idempotency-Key` 사용을 권장한다.

- 코스 초안 확정
- 데이트 종료
- 랭킹 코스 진행
- 과거 코스 재진행
- 커뮤니티 재발행

동일한 profileId, URL, `Idempotency-Key` 요청은 최초 결과를 반환한다.

멱등성 레코드는 `idempotency_records`에 저장한다. 같은 key를 다른 요청 본문에 재사용하면
409 `COMMON_IDEMPOTENCY_KEY_REUSED`, 동일 요청이 아직 처리 중이면 409
`COMMON_IDEMPOTENCY_REQUEST_IN_PROGRESS`를 반환한다. 요청 인증과 기본 DTO 검증을 통과한 뒤
레코드를 선점하며, 완료한 최초 HTTP 상태와 공통 응답 body를 재요청에 사용한다. 5xx로 끝난
처리는 재시도할 수 있도록 완료 응답으로 보존하지 않는다.

### 5.5 문자열 제한

| 필드 | 제한 |
|---|---|
| 닉네임 | 2~14자 |
| 비밀번호 | 숫자 4자리 |
| AI 대화 메시지 | 1~1000자 |
| 코스 제목 | 1~60자 |
| 한 줄 코멘트 | 1~80자 |
| 전체 추천 멘트 | 최대 500자 |
| 장소별 추천 멘트 | 최대 300자 |

## 6. 공통 DTO

이 절의 JSON은 성공 응답의 `data`에 들어가는 도메인 구조다.

### 6.1 `PlaceSummaryDto`

```json
{
  "contentId": "130551",
  "name": "대전시립미술관",
  "category": "CULTURAL_FACILITY",
  "district": "SEO_GU",
  "address": "대전광역시 서구 둔산대로 155",
  "latitude": 36.366988348,
  "longitude": 127.385704504,
  "imageUrl": "https://...",
  "indoorOutdoor": "INDOOR"
}
```

장소의 API 식별자와 path parameter는 모두 TourAPI `contentId` 문자열을 사용한다. 별도 장소 UUID는 만들지 않는다.
DB에서 아직 분류되지 않은 `district`, `indoorOutdoor`와 존재하지 않는 `imageUrl`은 `null`로 반환하며 임의 값으로 보완하지 않는다.

### 6.2 `CourseConditionDto`

```json
{
  "date": "2026-07-14",
  "timeSlot": "AFTERNOON",
  "startTime": "14:00",
  "district": "YUSEONG_GU",
  "spaceType": "INDOOR",
  "moods": ["QUIET", "EMOTIONAL"],
  "activities": ["CULTURE_EXHIBITION", "FOOD"],
  "scheduleDensity": "RELAXED",
  "transportation": "PUBLIC_TRANSIT"
}
```

서버는 이 값을 프로필 성향으로 저장하지 않는다.

### 6.3 `WeatherSummaryDto`

```json
{
  "available": true,
  "district": "YUSEONG_GU",
  "date": "2026-07-14",
  "timeSlot": "AFTERNOON",
  "summary": "오후 4시부터 약한 비",
  "temperatureMin": 21.0,
  "temperatureMax": 27.0,
  "precipitationProbability": 60,
  "condition": "LIGHT_RAIN",
  "recommendation": {
    "preferredSpaceType": "INDOOR",
    "indoorRatio": 0.7,
    "message": "비 예보를 반영해 실내 장소 비중을 높였어요."
  },
  "provider": "외부 날씨 API",
  "observedAt": "2026-07-14T10:00:00+09:00"
}
```

날씨를 포함하는 모든 API는 이 중첩 `recommendation` 구조를 사용한다. 공급자 장애 시에도 같은 구조를 유지한다.

### 6.4 `CoursePlaceDto`

```json
{
  "coursePlaceId": "f2a9252d-14b1-4fe4-ae09-c8ebac4fd4c2",
  "order": 1,
  "scheduledAt": "2026-07-14T14:00:00+09:00",
  "estimatedStayMinutes": 90,
  "place": {},
  "sweetComment": "같은 작품을 바라보며 서로의 취향을 조금 더 알아가 보세요.",
  "heartedByMe": false,
  "heartCount": 14
}
```

### 6.5 `CourseMapDto`

```json
{
  "centerLatitude": 36.37,
  "centerLongitude": 127.38,
  "polyline": [
    {"latitude": 36.3798, "longitude": 127.3605},
    {"latitude": 36.3669, "longitude": 127.3857}
  ]
}
```

### 6.6 `DateCourseDto`

```json
{
  "courseId": "2adb4617-cf36-40ba-a6bd-2e9d45d2b3d8",
  "status": "ACTIVE",
  "sourceType": "AI_CHAT",
  "title": "비 오는 날 포근한 문화 데이트",
  "date": "2026-07-14",
  "timeSlot": "AFTERNOON",
  "overallComment": "오늘의 비 예보를 반영해 실내 장소 중심으로 구성했어요.",
  "estimatedTotalMinutes": 240,
  "conditions": {},
  "tags": ["#유성구", "#오후데이트", "#실내데이트"],
  "weather": {},
  "places": [{}, {}, {}],
  "map": {},
  "progress": {
    "currentOrderNo": 2,
    "completedPlaceCount": 1,
    "totalPlaceCount": 3,
    "progressPercent": 33,
    "allPlacesCompleted": false
  },
  "oneLineComment": null,
  "createdAt": "2026-07-14T13:30:00+09:00",
  "completedAt": null
}
```

`estimatedTotalMinutes`는 첫 장소의 `scheduledAt`부터 마지막 장소의 `scheduledAt + estimatedStayMinutes`까지의 분 단위 차이다. 코스는 항상 2~4개 장소를 포함한다. 평점·만족도 필드는 존재하지 않는다.

### 6.7 `DateCourseProgressDto`

```json
{
  "courseId": "2adb4617-cf36-40ba-a6bd-2e9d45d2b3d8",
  "completedPlace": {
    "coursePlaceId": "f2a9252d-14b1-4fe4-ae09-c8ebac4fd4c2",
    "order": 1,
    "completedAt": "2026-07-14T15:30:00+09:00"
  },
  "nextPlace": {},
  "currentOrderNo": 2,
  "completedPlaceCount": 1,
  "totalPlaceCount": 3,
  "progressPercent": 33,
  "allPlacesCompleted": false
}
```

- `progressPercent`는 `floor(completedPlaceCount * 100 / totalPlaceCount)`로 계산한다.
- 마지막 장소 완료 후 `nextPlace`는 null, `progressPercent`는 100, `allPlacesCompleted`는 true다.
- DB의 `current_order_no`는 마지막 순서를 유지하며, 마지막 완료 여부는 `allPlacesCompleted`로 판단한다.

## 7. 전체 엔드포인트

| 영역 | Method | Path | 인증 | 설명 |
|---|---|---|---|---|
| Common | GET | `/health` | 공개 | 서버 상태 |
| Common | GET | `/meta/options` | 공개 | 선택 옵션 |
| Identity | GET | `/auth/nickname-suggestions` | 공개 | 닉네임 추천 |
| Identity | POST | `/auth/profiles` | 공개 | 익명 프로필 등록 |
| Identity | POST | `/auth/verify` | Body | 입장 검증 |
| Identity | GET | `/profiles/me` | 필수 | 내 프로필 |
| Place | GET | `/places` | 선택 | 장소 목록·마커 |
| Place | GET | `/places/{contentId}` | 선택 | 장소 상세 |
| Place | GET | `/places/{contentId}/nearby` | 선택 | 주변 장소 |
| Weather | GET | `/weather` | 선택 | 날짜·지역 날씨 |
| Chat | POST | `/chat/sessions` | 필수 | 세션과 최초 코스 생성 |
| Chat | GET | `/chat/sessions/{sessionId}` | 필수 | 세션·초안 조회 |
| Chat | POST | `/chat/sessions/{sessionId}/messages` | 필수 | 자연어·빠른 수정·재생성 |
| Chat | POST | `/chat/sessions/{sessionId}/confirm` | 필수 | 코스 확정 |
| Chat | DELETE | `/chat/sessions/{sessionId}` | 필수 | 확정 전 초안 폐기 |
| Current | GET | `/date-courses/current` | 필수 | 현재 데이트 |
| Current | PUT | `/date-courses/current/places/{coursePlaceId}/complete` | 필수 | 현재 장소 완료·다음 장소 전환 |
| Current | PUT | `/date-courses/current/places/{coursePlaceId}/heart` | 필수 | 장소 하트 등록 |
| Current | DELETE | `/date-courses/current/places/{coursePlaceId}/heart` | 필수 | 장소 하트 취소 |
| Current | POST | `/date-courses/current/complete` | 필수 | 데이트 종료·자동 공개 |
| Community | GET | `/community/posts` | 선택 | 랭킹보드 목록 |
| Community | GET | `/community/posts/{postId}` | 선택 | 게시글 상세 |
| Community | POST | `/community/posts` | 필수 | 완료 코스 재발행 |
| Community | PATCH | `/community/posts/{postId}` | 필수 | 한 줄 코멘트 수정 |
| Community | DELETE | `/community/posts/{postId}` | 필수 | 게시글 논리 삭제 |
| Community | PUT | `/community/posts/{postId}/like` | 필수 | 게시글 좋아요 |
| Community | DELETE | `/community/posts/{postId}/like` | 필수 | 게시글 좋아요 취소 |
| Community | POST | `/community/posts/{postId}/start` | 필수 | 공개 코스 진행 |
| Ranking | GET | `/rankings/masters` | 선택 | 데이트 마스터 |
| History | GET | `/profiles/me/date-courses` | 필수 | 완료 코스 목록 |
| History | GET | `/profiles/me/date-courses/{courseId}` | 필수 | 완료 코스 상세 |
| History | POST | `/profiles/me/date-courses/{courseId}/restart` | 필수 | 과거 코스 재진행 |

총 32개 엔드포인트다. 닉네임·비밀번호 수정, 사용자 성향 저장·조회, 축제 조회, 현재 데이트 취소 엔드포인트는 없다.

## 8. Common API

### 8.1 `GET /health`

- 인증: 불필요
- 200 `data`: `status`, `database`, `aiProvider`, `weatherProvider`, `version`
- 서버와 DB가 정상이면 외부 공급자 장애에도 HTTP 200을 유지하고 공급자 상태를 `DEGRADED`로 표시한다.

### 8.2 `GET /meta/options`

- 인증: 불필요
- 200 `data`: `timeSlots`, `districts`, `spaceTypes`, `moods`, `activityTypes`, `scheduleDensities`, `transportations`, `rankingSorts`
- 각 항목은 `{ "value": "ENUM", "label": "표시명" }` 구조다.

## 9. Identity API

### 9.1 `GET /auth/nickname-suggestions`

| Query | 타입 | 필수 | 기본값/검증 |
|---|---|---:|---|
| `count` | int | N | 5, 범위 1~10 |
| `seed` | string | N | null, 분위기 키워드 |

200 `data`:

```json
{"suggestions": ["복숭아와호두", "성심당옆두근이", "042설렘단"]}
```

### 9.2 `POST /auth/profiles`

```json
{"nickname": "복숭아와호두", "password": "0420"}
```

- `nickname`: trim 후 2~14자, 금칙어 제외, 정규화 값 UNIQUE
- `password`: `^\d{4}$`
- 201 `data`: `profileId`, `nickname`, `hasActiveDateCourse`, `completedDateCourseCount`, `createdAt`
- 오류: 409 `AUTH_NICKNAME_ALREADY_EXISTS`, 422 `COMMON_VALIDATION_ERROR`, 429 `AUTH_TOO_MANY_ATTEMPTS`

### 9.3 `POST /auth/verify`

```json
{"nickname": "복숭아와호두", "password": "0420"}
```

- 닉네임으로 조회한 뒤 평문 비밀번호를 비교한다.
- 토큰, 쿠키, 서버 세션을 만들지 않는다.
- 200 `data`: `profileId`, `nickname`, `hasActiveDateCourse`, `completedDateCourseCount`, `verifiedAt`
- 오류: 401 `AUTH_INVALID_CREDENTIALS`, 429 `AUTH_TOO_MANY_ATTEMPTS`

### 9.4 `GET /profiles/me`

- 인증: 필수
- 200 `data`: `profileId`, `nickname`, `hasActiveDateCourse`, `completedDateCourseCount`, `publishedCourseCount`, `createdAt`

## 10. Place API

### 10.1 `GET /places`

| Query | 타입 | 규칙 |
|---|---|---|
| `keyword` | string | 장소명·주소 검색 |
| `district` | `District` | `ANY` 제외 |
| `category` | `PlaceCategory[]` | 쉼표 구분 |
| `spaceType` | `SpaceType` | 실내·실외 |
| `latitude` | float | 반경 검색 시 세 좌표 필드 모두 필요 |
| `longitude` | float | 반경 검색 시 세 좌표 필드 모두 필요 |
| `radiusKm` | float | 0.1~30 |
| `hasImage` | boolean | 이미지 존재 여부 |
| `page` | int | 기본 1 |
| `size` | int | 기본 20, 최대 100 |

- 200 `data`: `PlaceSummaryDto[]`
- 200 `meta`: `PageMetaDto`
- 오류: `PLACE_INVALID_COORDINATES`, `PLACE_RADIUS_OUT_OF_RANGE`, `COMMON_VALIDATION_ERROR`

### 10.2 `GET /places/{contentId}`

- path `contentId`: TourAPI 콘텐츠 ID 문자열이며 `places.content_id`를 조회한다.
- 200 `data`: `contentId`, `contentTypeId`, `name`, `category`, `district`, 주소, 좌표, 이미지, 전화번호, `indoorOutdoor`, `source`
- `source`: `provider`, `license`, `originalModifiedAt`
- `contentTypeId`는 integer다.

### 10.3 `GET /places/{contentId}/nearby`

| Query | 타입 | 기본값/검증 |
|---|---|---|
| `radiusKm` | float | 3 |
| `category` | `PlaceCategory[]` | null |
| `limit` | int | 10, 최대 30 |

200 `data`:

```json
{
  "origin": {},
  "places": [{"place": {}, "distanceKm": 1.2}]
}
```

## 11. Weather API

### 11.1 `GET /weather`

| Query | 타입 | 필수 | 규칙 |
|---|---|---:|---|
| `date` | date | Y | 공급자 예보 범위 내 |
| `district` | `District` | Y | `ANY` 가능 |
| `timeSlot` | `TimeSlot` | Y | 오전·오후·하루 |

200 `data`:

```json
{
  "available": true,
  "district": "YUSEONG_GU",
  "date": "2026-07-14",
  "timeSlot": "AFTERNOON",
  "summary": "오후 4시부터 약한 비",
  "temperatureMin": 21.0,
  "temperatureMax": 27.0,
  "precipitationProbability": 60,
  "condition": "LIGHT_RAIN",
  "recommendation": {
    "preferredSpaceType": "INDOOR",
    "indoorRatio": 0.7,
    "message": "오후 비 예보를 반영해 실내 장소를 중심으로 추천할게요."
  },
  "provider": "외부 날씨 API",
  "observedAt": "2026-07-14T10:00:00+09:00"
}
```

외부 API 실패 시 HTTP 200과 `available=false`를 반환한다. `recommendation.preferredSpaceType`은 `ANY`, `indoorRatio`는 null이며 입력한 공간 조건만 반영한다는 메시지를 제공한다.

## 12. Chat / CourseDraft API

### 12.1 `POST /chat/sessions`

- 인증: 필수
- 목적: 전체 조건을 받아 세션, 날씨 스냅샷, 최초 코스 초안을 생성한다.

```json
{
  "date": "2026-07-14",
  "timeSlot": "AFTERNOON",
  "startTime": "14:00",
  "district": "YUSEONG_GU",
  "spaceType": "INDOOR",
  "moods": ["QUIET", "EMOTIONAL"],
  "activities": ["CULTURE_EXHIBITION", "FOOD"],
  "scheduleDensity": "RELAXED",
  "transportation": "PUBLIC_TRANSIT",
  "initialMessage": "마지막에는 조용한 저녁 식당을 넣어줘."
}
```

| 필드 | 필수 | 검증 |
|---|---:|---|
| `date` | Y | 과거 날짜 불가 |
| `timeSlot` | Y | Enum |
| `startTime` | Y | `HH:mm` |
| `district` | Y | Enum |
| `spaceType` | Y | Enum |
| `moods` | Y | 1~4개 |
| `activities` | Y | 1~5개 |
| `scheduleDensity` | Y | Enum |
| `transportation` | Y | Enum |
| `initialMessage` | N | 최대 1000자 |

처리 순서: 활성 코스 확인 → 조건 검증 → 날씨 조회 → 장소 후보 조회 → 후보 점수 계산 → 후보만 AI에 전달 → 제목·전체 멘트·장소별 멘트 생성 → 세션과 초안 저장.

- 201 `data`: `sessionId`, `status`, `assistantMessage`, `courseDraft`
- `courseDraft`: `draftId`, `version`, 제목, 날짜, 시간대, 전체 멘트, `estimatedTotalMinutes`, 조건, 태그, 날씨, 장소, 지도
- `courseDraft.places`는 최소 2개, 최대 4개다. 이 범위를 벗어난 AI 응답은 저장하지 않고 재시도하거나 `CHAT_AI_PROVIDER_ERROR`로 처리한다.
- 분위기처럼 DB에 정형 값이 없는 주관적 조건은 향후 AI가 실제 DB 장소의 제목·분류·주소 등만 근거로 판단한다. 이 판단을 위해 외부 장소나 임의 장소를 후보에 추가하지 않는다.
- 오류: 409 `DATE_COURSE_ACTIVE_ALREADY_EXISTS`, 422 `CHAT_NO_RECOMMENDABLE_PLACES`, 422 `CHAT_INVALID_DATE_CONDITION`, 502 `CHAT_AI_PROVIDER_ERROR`, 503 `CHAT_AI_TEMPORARILY_UNAVAILABLE`

### 12.2 `GET /chat/sessions/{sessionId}`

- 인증: 필수, 본인 세션만 허용
- 200 `data`: `sessionId`, `status`, `conditions`, `messages[]`, `courseDraft`
- 메시지: `messageId`, `role`, `content`, `createdAt`

### 12.3 `POST /chat/sessions/{sessionId}/messages`

```json
{
  "message": "두 번째 장소를 카페로 바꾸고 이동 거리를 줄여줘.",
  "quickAction": null,
  "expectedDraftVersion": 1
}
```

- `message`: 선택, 전달 시 1~1000자
- `quickAction`: 선택, `CourseEditAction`
- `message`와 `quickAction` 중 정확히 하나만 전달한다.
- `expectedDraftVersion`: 필수, 동시 수정 방지
- AI가 DB에 없는 장소를 생성할 수 없다.
- 장소 교체 시 Place Repository를 재조회한다.
- 성공한 변경은 초안 version을 1 증가시킨다.
- 수행 불가 시 기존 초안을 유지하고 HTTP 200, `changed=false`, `warnings[]`를 반환한다.
- 최초 입력 조건을 기본 컨텍스트로 유지하고 축제를 조회하지 않는다.
- 변경 후에도 코스 장소 수는 2~4개를 유지한다.
- 200 `data`: `userMessage`, `assistantMessage`, `changeSummary`, `courseDraft`
- 오류: `CHAT_SESSION_NOT_FOUND`, `CHAT_SESSION_FORBIDDEN`, `CHAT_SESSION_ALREADY_CONFIRMED`, `CHAT_DRAFT_VERSION_CONFLICT`, `CHAT_MESSAGE_TOO_LONG`, `CHAT_INVALID_EDIT_REQUEST`

빠른 수정 매핑:

| `quickAction` | 동작 |
|---|---|
| `CHANGE_CAFE` | 현재 조건 안에서 한 장소를 카페 후보로 교체한다. |
| `ADD_NIGHT_VIEW` | 야경 장소를 추가하거나 기존 장소와 교체한다. 최대 4개를 넘지 않는다. |
| `REDUCE_ROUTE` | 장소 수를 유지하면서 전체 이동 동선을 줄인다. |
| `INCREASE_INDOOR` | 실내 장소 비중을 높인다. |
| `REGENERATE` | 최초 조건을 유지하고 현재 초안과 다른 장소 조합을 생성한다. |

`quickAction` 요청도 사용자 메시지로 채팅 기록에 남기되, 표시 문구는 서버가 위 매핑에서 생성한다.

### 12.4 `POST /chat/sessions/{sessionId}/confirm`

- 인증: 필수
- `Idempotency-Key`: 권장

```json
{"draftId": "c2b7...", "expectedVersion": 2}
```

처리 순서: 소유권·세션 상태 확인 → draft ID·version 확인 → 활성 코스 재확인 → `DateCourse` 생성 → 장소 스냅샷 저장 → 세션 `CONFIRMED` → 커밋.

- 201 `data`: `DateCourseDto`
- 초안 장소 수가 2~4개가 아니면 확정을 거부한다.
- 오류: 409 `CHAT_DRAFT_VERSION_CONFLICT`, 409 `DATE_COURSE_ACTIVE_ALREADY_EXISTS`, 404 `CHAT_SESSION_NOT_FOUND`, 409 `CHAT_SESSION_ALREADY_CONFIRMED`
- 현재 코스 교체 옵션은 없다.

### 12.5 `DELETE /chat/sessions/{sessionId}`

- 인증: 필수
- 확정 전 AI 초안만 `DISCARDED` 처리한다. 현재 데이트 삭제가 아니다.
- 200, `code=CHAT_SESSION_DISCARDED`, `data=null`

## 13. Current DateCourse API

### 13.1 `GET /date-courses/current`

- 인증: 필수
- 200 `data`: `DateCourseDto`
- 현재 코스가 없으면 200, `code=DATE_COURSE_CURRENT_EMPTY`, `data=null`

### 13.2 `PUT /date-courses/current/places/{coursePlaceId}/complete`

- 인증: 필수
- Request body: 없음
- 본인의 현재 `ACTIVE` 코스 장소만 완료할 수 있다.
- 아직 완료되지 않은 장소는 `order == date_courses.current_order_no`일 때만 완료할 수 있다.
- 서버 시각을 해당 장소의 `completed_at`에 기록한다.
- 다음 장소가 있으면 `current_order_no`를 다음 `order_no`로 갱신한다.
- 마지막 장소면 코스는 계속 `ACTIVE`로 유지하고 `nextPlace=null`, `allPlacesCompleted=true`를 반환한다. 사용자는 이후 별도의 데이트 종료 API로 한 줄 코멘트를 저장한다.
- 이미 완료된 같은 장소를 다시 요청하면 최초 `completedAt`과 현재 진행 상태를 HTTP 200으로 반환하며 두 번 전진하지 않는다. 이 멱등 검사를 순서 충돌 검사보다 먼저 수행한다.
- 아직 완료되지 않은 이전·이후 순서 장소를 요청하면 409 `DATE_COURSE_PLACE_SEQUENCE_CONFLICT`다.
- 200 `data`: `DateCourseProgressDto`
- 오류: `DATE_COURSE_CURRENT_NOT_FOUND`, `DATE_COURSE_NOT_ACTIVE`, `DATE_COURSE_PLACE_NOT_FOUND`, `DATE_COURSE_PLACE_NOT_OWNED`, `DATE_COURSE_PLACE_SEQUENCE_CONFLICT`

### 13.3 `PUT /date-courses/current/places/{coursePlaceId}/heart`

- 본인의 현재 `ACTIVE` 코스 장소에만 사용한다.
- 멱등 처리한다.
- 200 `data`: `coursePlaceId`, `heartedByMe=true`, `heartCount`, `updatedAt`
- 오류: `DATE_COURSE_CURRENT_NOT_FOUND`, `DATE_COURSE_NOT_ACTIVE`, `DATE_COURSE_PLACE_NOT_FOUND`, `DATE_COURSE_PLACE_NOT_OWNED`

### 13.4 `DELETE /date-courses/current/places/{coursePlaceId}/heart`

- 200 `data`: `coursePlaceId`, `heartedByMe=false`, `heartCount`, `updatedAt`

### 13.5 `POST /date-courses/current/complete`

- 인증: 필수
- `Idempotency-Key`: 권장

```json
{"oneLineComment": "비 오는 날에도 이동이 편했어요."}
```

- `oneLineComment`: 필수, trim 후 1~80자
- 평점·만족도는 입력하거나 저장하지 않는다.
- 모든 장소의 `completed_at`이 존재해야 종료할 수 있다. 미완료 장소가 있으면 409 `DATE_COURSE_PLACES_INCOMPLETE`다.

처리 순서: 활성 코스·소유권 확인 → `COMPLETED` → 한 줄 코멘트 저장 → 장소별 하트 확정 → 게시글 자동 생성 → `completedAt` 기록 → 커밋.

- 200 `data`: `completedCourse`, `communityPost`
- 오류: 404 `DATE_COURSE_CURRENT_NOT_FOUND`, 409 `DATE_COURSE_ALREADY_COMPLETED`, 409 `DATE_COURSE_PLACES_INCOMPLETE`, 422 `COMMUNITY_COMMENT_REQUIRED`, 500 `DATE_COURSE_COMPLETION_TRANSACTION_FAILED`
- 현재 데이트 취소 API는 없다.

## 14. Community / Ranking API

### 14.1 `GET /community/posts`

| Query | 타입 | 기본값/설명 |
|---|---|---|
| `sort` | `RankingSort` | `POPULAR` |
| `district` | `District[]` | 다중 선택 |
| `timeSlot` | `TimeSlot[]` | 다중 선택 |
| `spaceType` | `SpaceType[]` | 다중 선택 |
| `mood` | `Mood[]` | 다중 선택 |
| `activity` | `ActivityType[]` | 다중 선택 |
| `density` | `ScheduleDensity[]` | 다중 선택 |
| `page` | int | 기본 1 |
| `size` | int | 기본 20, 최대 50 |

- `POPULAR`: 게시글 좋아요 수 내림차순, 동률이면 `publishedAt` 내림차순, 다시 동률이면 `postId` 오름차순
- `LATEST`: `publishedAt` 내림차순, 동률이면 게시글 ID 오름차순
- 장소별 누적 하트는 표시 정보이며 게시글 정렬 점수에는 사용하지 않는다.
- 200 item: `rank`, `postId`, `courseId`, `courseTitle`, `mainDistrict`, `authorNickname`, `oneLineComment`, `courseLikeCount`, `placeHeartCount`, `likedByMe`, `tags`, `publishedAt`

### 14.2 `GET /community/posts/{postId}`

- 200 `data`: `postId`, `owner`, 코스 제목, 작성자, 코멘트, 날짜, 시간대, 전체 멘트, 조건, 태그, 장소, 지도, 코스 좋아요 수, 장소별 누적 하트, `likedByMe`, 게시일

### 14.3 `POST /community/posts`

- 인증: 필수
- `Idempotency-Key`: 권장
- 삭제된 게시글의 완료 코스를 다시 공개할 때 사용하며 일반 종료 UI에서는 호출하지 않는다.

```json
{
  "dateCourseId": "...",
  "oneLineComment": "이동이 편했어요."
}
```

- 본인의 `COMPLETED` 코스만 가능하다.
- `date_course_id`로 기존 게시글을 삭제 상태까지 포함해 조회한다.
- 기존 게시글이 `PUBLISHED`면 409 `COMMUNITY_POST_ALREADY_EXISTS`다.
- 기존 게시글이 `DELETED`면 새 행을 만들지 않고 같은 `postId`의 행을 복원한다.
- 복원 시 `status=PUBLISHED`, `published_at=복원 요청 처리 시각`, `updated_at=동일 시각`, `deleted_at=NULL`로 갱신한다.
- `one_line_comment`는 요청의 trim된 1~80자 값으로 교체한다.
- 기존 `community_likes` 행은 그대로 유지한다. 복원 직후 좋아요 수와 `likedByMe`도 삭제 전 상태를 이어받는다.
- 작성자 ID와 닉네임 스냅샷은 복원하는 현재 프로필 기준으로 갱신한다.
- 200: 복원된 커뮤니티 상세 DTO
- 삭제된 기존 게시글 행이 없으면 404 `COMMUNITY_POST_NOT_FOUND`다.
- 오류: `COMMUNITY_POST_NOT_FOUND`, `COMMUNITY_POST_ALREADY_EXISTS`, `COMMUNITY_COMPLETED_COURSE_REQUIRED`, `COMMUNITY_POST_FORBIDDEN`
- 동일 `Idempotency-Key` 재요청은 최초 200 결과를 반환한다. 다른 키로 이미 복원된 게시글을 다시 요청하면 409다.

### 14.4 `PATCH /community/posts/{postId}`

```json
{"oneLineComment": "이동이 정말 편했고 비 오는 날에도 좋았어요."}
```

- 인증: 필수, 소유자만
- 완료 코스의 장소, 일정, 추천 멘트, 조건은 바꾸지 않는다.
- 200: 수정된 커뮤니티 상세 DTO

### 14.5 `DELETE /community/posts/{postId}`

- 인증: 필수, 소유자만
- 게시글을 `DELETED`로 바꾸고 랭킹에서 제외한다.
- 과거 데이트와 기존 좋아요 기록은 유지한다.
- 200, `data=null`

### 14.6 게시글 좋아요

- `PUT /community/posts/{postId}/like`: 프로필당 게시글 1회, 멱등 등록
- `DELETE /community/posts/{postId}/like`: 좋아요 취소
- 200 `data`: `postId`, `likedByMe`, `likeCount`

### 14.7 `POST /community/posts/{postId}/start`

```json
{"date": "2026-07-20", "startTime": "14:00"}
```

처리 순서: 활성 코스 확인 → 공개 게시글·원본 스냅샷 조회 → 새 날짜·시간으로 일정 재계산 → `sourceType=RANKING_COPY`인 새 활성 코스 생성.

복사 시 장소·추천 문구·조건 스냅샷만 복사한다. 새 코스의 `hearted=0`, `hearted_at=NULL`, 장소 `completed_at=NULL`, `current_order_no=첫 번째 order_no`, 코스 `started_at=NULL`로 초기화한다.

- 201 `data`: `activeCourse`, `copyResult.sourcePostId`, `copyResult.warnings`
- 오류: 409 `DATE_COURSE_ACTIVE_ALREADY_EXISTS`, 404 `COMMUNITY_POST_NOT_FOUND`, 409 `COMMUNITY_POST_DELETED`, 422 `COURSE_COPY_INVALID_START_TIME`
- 현재 데이트 교체 옵션은 없다.

### 14.8 `GET /rankings/masters`

| Query | 타입 | 기본값/검증 |
|---|---|---|
| `limit` | int | 10, 최대 50 |

- 공개 상태인 작성자별 게시글이 받은 `community_likes` 합계를 기준으로 내림차순 정렬한다.
- 동률이면 공개 게시글 수 내림차순, 닉네임 오름차순으로 정렬한다.
- 200 `data`: `masters[]`
- 각 항목: `rank`, `profileId`, `nickname`, `publishedCourseCount`, `receivedLikeCount`

## 15. History API

### 15.1 `GET /profiles/me/date-courses`

| Query | 타입 | 필수 |
|---|---|---:|
| `year` | int | N |
| `month` | int | N |
| `district` | `District` | N |
| `page` | int | N |
| `size` | int | N |

본인의 `COMPLETED` 코스만 반환한다. 200 item: `courseId`, `date`, `courseTitle`, `mainDistrict`, `oneLineComment`, `heartedPlaceCount`, `totalPlaceCount`, `completedAt`.

### 15.2 `GET /profiles/me/date-courses/{courseId}`

- 인증: 필수, 본인 코스만
- 200 `data`: 코스 ID·상태·제목·날짜·코멘트·조건·태그·장소·지도·완료일
- 평점·만족도 필드는 반환하지 않는다.

### 15.3 `POST /profiles/me/date-courses/{courseId}/restart`

```json
{"date": "2026-07-21", "startTime": "14:00"}
```

처리 순서: 활성 코스 확인 → 본인 완료 코스 조회 → 장소·추천 문구·조건 스냅샷 복사 → 일정 재계산 → `sourceType=HISTORY_RESTART` → 새 활성 코스 저장.

복사 시 `hearted=0`, `hearted_at=NULL`, 장소 `completed_at=NULL`, `current_order_no=첫 번째 order_no`, 코스 `started_at=NULL`로 초기화한다.

- 201 `data`: `DateCourseDto`
- 오류: `DATE_COURSE_ACTIVE_ALREADY_EXISTS`, `HISTORY_COURSE_NOT_FOUND`, `HISTORY_COURSE_FORBIDDEN`, `COURSE_COPY_INVALID_START_TIME`
- 현재 데이트 교체 옵션은 없다.

## 16. HTTP 상태와 오류 코드

| HTTP | 기준 |
|---:|---|
| 200 | 조회·수정·삭제 성공, 멱등 재요청 |
| 201 | 새 리소스 생성 |
| 400 | JSON 파싱 실패, query 조합 오류 |
| 401 | 인증 헤더 누락 또는 비밀번호 불일치 |
| 403 | 타 사용자 리소스 접근 |
| 404 | 리소스 없음 |
| 409 | 중복·상태·버전 충돌 |
| 422 | 필드 검증 또는 업무 규칙 위반 |
| 429 | 요청 제한 |
| 500 | 내부 서버 오류 |
| 502 | 외부 API 비정상 응답 |
| 503 | 외부 API 일시 장애 |

| 영역 | 오류 코드 |
|---|---|
| Common | `COMMON_BAD_REQUEST`, `COMMON_VALIDATION_ERROR`, `COMMON_NOT_FOUND`, `COMMON_INTERNAL_SERVER_ERROR`, `COMMON_RATE_LIMIT_EXCEEDED`, `COMMON_EXTERNAL_SERVICE_ERROR`, `COMMON_EXTERNAL_SERVICE_UNAVAILABLE`, `COMMON_IDEMPOTENCY_KEY_REUSED`, `COMMON_IDEMPOTENCY_REQUEST_IN_PROGRESS` |
| Auth | `AUTH_NICKNAME_ALREADY_EXISTS`, `AUTH_CREDENTIALS_REQUIRED`, `AUTH_INVALID_PROFILE_ID_FORMAT`, `AUTH_INVALID_CREDENTIALS`, `AUTH_FORBIDDEN`, `AUTH_TOO_MANY_ATTEMPTS` |
| Place | `PLACE_NOT_FOUND`, `PLACE_INVALID_COORDINATES`, `PLACE_RADIUS_OUT_OF_RANGE` |
| Weather | `WEATHER_DATE_OUT_OF_RANGE`, `WEATHER_PROVIDER_ERROR` |
| Chat | `CHAT_SESSION_NOT_FOUND`, `CHAT_SESSION_FORBIDDEN`, `CHAT_SESSION_ALREADY_CONFIRMED`, `CHAT_MESSAGE_TOO_LONG`, `CHAT_INVALID_EDIT_REQUEST`, `CHAT_NO_RECOMMENDABLE_PLACES`, `CHAT_INVALID_DATE_CONDITION`, `CHAT_DRAFT_VERSION_CONFLICT`, `CHAT_AI_PROVIDER_ERROR`, `CHAT_AI_TEMPORARILY_UNAVAILABLE` |
| DateCourse | `DATE_COURSE_CURRENT_NOT_FOUND`, `DATE_COURSE_ACTIVE_ALREADY_EXISTS`, `DATE_COURSE_NOT_ACTIVE`, `DATE_COURSE_ALREADY_COMPLETED`, `DATE_COURSE_PLACE_NOT_FOUND`, `DATE_COURSE_PLACE_NOT_OWNED`, `DATE_COURSE_PLACE_SEQUENCE_CONFLICT`, `DATE_COURSE_PLACES_INCOMPLETE`, `DATE_COURSE_COMPLETION_TRANSACTION_FAILED` |
| Community | `COMMUNITY_POST_NOT_FOUND`, `COMMUNITY_POST_FORBIDDEN`, `COMMUNITY_POST_ALREADY_EXISTS`, `COMMUNITY_COMPLETED_COURSE_REQUIRED`, `COMMUNITY_COMMENT_REQUIRED`, `COMMUNITY_POST_DELETED` |
| History | `HISTORY_COURSE_NOT_FOUND`, `HISTORY_COURSE_FORBIDDEN` |

예외 처리 대상은 `RequestValidationError`, `StarletteHTTPException`, `SQLAlchemyError`, 외부 API timeout, `BusinessException`, 처리되지 않은 `Exception`이다. FastAPI 기본 422도 공통 `ErrorResponseDto`로 변환한다.

## 17. 페이지별 호출 매핑

| 페이지 | 호출 순서 |
|---|---|
| 시작 | 닉네임 추천 → 등록 또는 검증 → 내 프로필 |
| 코스 만들기 | 옵션 → 선택적 날씨 → 세션 생성 → 메시지 조정 → 확정 |
| 현재 데이트 | 현재 코스 → 현재 장소 완료·다음 장소 전환 → 장소 하트 등록·취소 → 종료 |
| 랭킹보드 | 목록 → 행 상세 → 좋아요 → 공개 코스 시작 → 마스터 랭킹 |
| 과거 데이트 | 목록 → 행 상세 → 재진행 |

입장 페이지를 제외한 사용자 페이지는 인증 헤더를 전달한다.

## 18. 구현 완료 기준

- 모든 성공·실패 응답이 공통 envelope를 따른다.
- 보호 API는 매 요청마다 profileId와 평문 비밀번호를 검증한다.
- 비밀번호가 로그, 오류 응답, trace에 노출되지 않는다.
- 닉네임·비밀번호 수정 API와 성향 저장 API가 없다.
- 코스 생성마다 전체 조건을 전달한다.
- 최초 생성·수정·확정 코스는 DB 장소 2~4개로 제한하고 전체 예상 소요시간을 제공한다.
- 빠른 수정은 `CourseEditAction`과 고정 매핑을 사용한다.
- 축제 조회·추천 로직과 현재 데이트 취소 API가 없다.
- 프로필당 `ACTIVE` 코스는 최대 하나다.
- 활성 코스가 있으면 생성·랭킹 복사·과거 재진행을 409로 막는다.
- 장소 하트는 현재 활성 코스에서만 변경한다.
- 장소 완료는 순서대로만 허용하고 같은 장소 완료 재요청은 두 번 전진하지 않는다.
- 마지막 장소 완료 후에도 한 줄 코멘트로 종료할 때까지 코스는 `ACTIVE`다.
- 종료와 커뮤니티 자동 공개를 한 트랜잭션으로 처리한다.
- 종료 평가에는 장소별 하트와 한 줄 코멘트만 사용하고 평점은 사용하지 않는다.
- 확정·완료 코스의 장소, 시간, 추천 문구는 불변이다.
- 커뮤니티 수정은 한 줄 코멘트만 허용한다.
- 삭제 게시글 재발행은 기존 행과 좋아요를 유지한 상태에서 `PUBLISHED`로 복원한다.
- 인기 랭킹과 데이트 마스터는 게시글 좋아요 수를 기준으로 한다.
- AI는 DB에 없는 장소를 등록하지 못한다.
- 날씨 장애가 코스 생성 전체 실패로 이어지지 않는다.
- 완료 코스 스냅샷은 원본 장소가 바뀌어도 유지된다.
- 랭킹 복사·과거 재진행 시 진행 상태와 장소 하트는 초기화한다.
- `/docs`, `/redoc`에서 모든 요청·응답·오류 schema를 확인할 수 있다.
