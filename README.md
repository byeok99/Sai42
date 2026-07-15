# 사이42 (Sai42)

대전 지역번호 **042**와 “우리 사이”를 결합한 AI 기반 데이트 코스 서비스입니다. 두 사람이 날짜,
시간, 지역, 취향을 입력하면 대전 공공 관광 데이터를 후보로 삼아 코스를 제안하고, 대화로 코스를
수정한 뒤 실제 데이트 진행·추억 공유까지 하나의 흐름으로 연결합니다.

```text
입장 → 성향 조사 → AI 코스 생성/수정 → 코스 확정 → 현재 데이트 진행 → 종료/공개 → 랭킹·추억
```

## 핵심 기능

- 익명 커플 프로필 등록 및 비밀번호 검증
- 날짜·시각·지역·공간·분위기·활동·일정 밀도·이동수단 기반 AI 코스 생성
- 자연어 요청 및 빠른 수정(카페 변경, 야경 추가, 동선 축소, 실내 강화)
- 지도 위 코스 경로와 장소별 방문 완료·하트 관리
- 데이트 종료 시 추억 저장 및 커뮤니티 게시글 자동 공개
- 공개 코스 랭킹, 좋아요, 내 게시글 수정/논리 삭제, 타인 코스 재시작
- 완료한 내 데이트 코스 조회 및 재진행

## 기술 스택

| 영역 | 기술 | 활용 목적 |
| --- | --- | --- |
| Frontend | Vue 3, TypeScript, Vite | 컴포넌트 기반 SPA와 빠른 개발 서버/번들링 |
| Frontend 상태/라우팅 | Pinia, Vue Router | 인증·설문·챗 세션·현재 코스 상태와 화면 전환 관리 |
| Frontend 지도 | Leaflet, OpenStreetMap | 추천/진행 중 코스의 장소 마커와 폴리라인 경로 표시 |
| Frontend 품질 | vue-tsc, ESLint, Oxlint, Prettier | 타입 안정성, 정적 분석, 일관된 포맷 유지 |
| Backend | Python 3.12, FastAPI | 비동기 HTTP API, OpenAPI/Swagger 문서 자동화 |
| Backend 검증 | Pydantic v2 | 요청·응답 DTO, enum, 입력 규칙 검증 |
| Backend 영속성 | SQLAlchemy 2.x Async, Alembic, SQLite | 비동기 DB 접근, 마이그레이션, 공공데이터/서비스 데이터 저장 |
| AI | OpenAI Responses API + Pydantic structured output | DB 후보 안에서만 코스를 선택하도록 구조화된 AI 응답 생성 |
| 날씨 | Open-Meteo Forecast API | 날짜·시간대의 날씨와 실내/실외 추천 비율 계산 |
| 데이터 | 한국관광공사 TourAPI 적재 데이터 | 대전 장소 후보, 좌표, 분류, 주소 등 추천 근거 제공 |
| 배포 | Render(Backend), Netlify 설정(Frontend) | API 런타임과 정적 웹 배포 구성 |

## 전체 아키텍처

![Sai42 architecture](<docs/assets/Sai42 architecture.svg>)

위 흐름은 프런트 이벤트가 API endpoint와 HTTPS JSON 네트워크를 거쳐 백엔드 계층으로 전달되고,
백엔드가 OpenAI·Open-Meteo·SQLite를 조합해 응답을 만드는 과정을 나타냅니다. 하단 흐름은 인증
헤더부터 챗 세션/초안 버전, 확정된 데이트 코스 스냅샷, 커뮤니티·추억까지 이어지는 서비스 상태의
변화를 보여줍니다.

백엔드는 도메인별로 `presentation / application / domain / infrastructure` 계층을 분리합니다.
Router는 HTTP 입출력과 dependency 조립만 맡고, 유스케이스와 트랜잭션 제어는 application service,
DB 및 외부 API 접근은 infrastructure repository/provider에 둡니다.

```text
backend/app/<domain>/
├── presentation/    # FastAPI router, dependency, HTTP response
├── application/     # use case, DTO, transaction boundary
├── domain/          # enum, entity, business rule
└── infrastructure/  # SQLAlchemy model/repository, OpenAI/Open-Meteo adapter
```

주요 도메인은 `auth`, `chat`, `course`, `community`, `history`, `place`, `ranking`, `weather`,
`common`입니다.

## Frontend 데이터 흐름

프런트는 화면 컴포넌트가 직접 HTTP 요청을 하지 않습니다. 모든 외부 요청은 Service/Repository를
거쳐 `ApiClient`가 수행하며, API 응답은 Pinia 상태에 반영된 뒤 화면이 갱신됩니다.

```text
View 이벤트
  → Pinia Store action
    → domain Service
      → Repository
        → ApiClient(fetch)
          → FastAPI
          ← BaseDto<T> / ErrorResponseDto
        ← DTO 검증·매핑
      ← 화면용 상태 업데이트
  ← Vue 반응성으로 지도·카드·목록 렌더링
```

### 주요 화면 흐름

1. **입장**: 닉네임·4자리 비밀번호를 `POST /auth/profiles` 또는 `POST /auth/verify`로 전송한다.
   응답의 `profileId`와 입력 비밀번호는 메모리에만 보관해 인증 헤더를 만든다.
2. **성향 조사**: 날짜, 시작 시각, 지역, 실내/실외, 활동, 분위기, 일정 밀도, 이동수단을 수집해
   `POST /chat/sessions` 요청으로 변환한다.
3. **사이봇**: 응답의 `sessionId`, `draftId`, `draftVersion`, 메시지, 장소/좌표를 상태에 저장한다.
   메시지 수정은 항상 최신 `expectedDraftVersion`을 함께 전송한다.
4. **현재 데이트**: 확정된 `DateCourseDto`를 표시하고, 장소 완료·하트·종료 API 응답으로 진행률을
   다시 동기화한다.
5. **랭킹/추억**: 탭 진입과 pull-to-refresh 시 목록을 다시 요청한다. 게시글 수정·삭제 후에는 서버의
   최신 목록을 다시 받아 다른 화면의 오래된 표시를 방지한다.

## Backend 데이터 흐름

### 1. 프로필 인증

```text
POST /auth/profiles 또는 /auth/verify
  → nickname 정규화·4자리 비밀번호 검증·rate limit 검사
  → user_profiles 조회/저장
  → profileId 반환

후속 인증 요청
  → X-Profile-Id + X-User-Password
  → AuthService.authenticate_headers()
  → AuthenticatedProfile dependency 주입
```

토큰이나 브라우저 쿠키 세션을 발급하지 않는 익명 프로필 모델입니다. 과제 요구에 따라 비밀번호는
숫자 4자리 평문으로 저장하지만, 로그·오류 응답·trace에는 노출하지 않습니다.

### 2. AI 코스 생성 및 챗 세션

```text
POST /chat/sessions
  → 헤더 인증, 활성 코스 존재 여부 확인
  → 요청 날짜/시각이 현재 이후인지 검증
  → Open-Meteo 날씨 요약 조회
  → SQLite places에서 조건에 맞는 추천 가능 장소 후보 조회·점수화
  → 후보 목록 + 조건 + 날씨만 OpenAI Responses API로 전달
  → 구조화된 AI 응답의 contentId를 SQLite 후보 집합과 재검증
  → chat_sessions에 조건·날씨·메시지·draft·version 저장
  → sessionId, assistantMessage, courseDraft 반환
```

AI 모델이 임의 장소를 만들어내지 않도록, 모델에는 SQLite에 존재하는 후보만 전달하고 응답의
`contentId`도 다시 대조합니다. 후보 밖 장소, 중복 장소, 2~4개 범위를 벗어난 결과는 저장하지
않습니다.

```text
POST /chat/sessions/{sessionId}/messages
  → 세션 소유자·ACTIVE 상태·expectedDraftVersion 확인
  → 자연어 또는 quickAction으로 초안 재생성
  → 메시지와 변경된 draft를 저장, version 증가

POST /chat/sessions/{sessionId}/confirm
  → draftId/version 재검증
  → date_courses + date_course_places 스냅샷 생성
  → chat_sessions.status = CONFIRMED
```

### 3. 데이트 진행, 종료, 커뮤니티

```text
현재 코스 조회
  GET /date-courses/current

장소 진행
  PUT /date-courses/current/places/{coursePlaceId}/complete
  → 현재 순서의 장소만 완료 처리 → 다음 순서 갱신

데이트 종료
  POST /date-courses/current/complete
  → 모든 장소 완료 여부 확인
  → date_courses를 COMPLETED로 변경
  → community_posts 게시글 자동 생성
  → 하나의 트랜잭션으로 commit
```

완료 코스는 장소명·주소·좌표·추천 멘트의 스냅샷을 유지합니다. 따라서 원본 공공데이터가 바뀌어도
과거 데이트와 공개 코스는 당시의 내용을 재현할 수 있습니다.

### 4. 랭킹·복사·추억

```text
완료 코스 → community_posts(PUBLISHED) → community_likes 집계 → 랭킹 목록

공개 코스 시작
  POST /community/posts/{postId}/start
  → 원본 코스 스냅샷 복사
  → 새 ACTIVE date_course 생성 (sourceType=RANKING_COPY)

추억 재진행
  POST /profiles/me/date-courses/{courseId}/restart
  → 새 ACTIVE date_course 생성 (sourceType=HISTORY_RESTART)
```

한 프로필에는 동시에 하나의 `ACTIVE` 코스만 존재하도록 SQLite partial unique index로 보장합니다.
공개 게시글은 작성자만 코멘트를 수정하거나 논리 삭제할 수 있고, 삭제 후에도 완료 코스와 좋아요
기록은 유지합니다.

## 세션·동시성·안전성

| 항목 | 설계 |
| --- | --- |
| 인증 세션 | 서버 쿠키 세션 대신 `X-Profile-Id`, `X-User-Password` 헤더로 매 요청 인증 |
| 챗 세션 | `chat_sessions`에 조건, 날씨, 메시지, 초안, 버전, 상태, 만료 시각을 저장 |
| 화면 상태 | 프런트는 `sessionId`, `draftId`, `draftVersion`을 메모리 Pinia 상태로 관리 |
| 동시 수정 방지 | 메시지/확정 요청의 `expectedDraftVersion`으로 낙관적 잠금 적용 |
| 쓰기 멱등성 | 코스 확정, 현재 데이트 종료, 공개 코스 시작은 `Idempotency-Key`를 지원 |
| 요청 추적 | `X-Request-Id`와 응답 `traceId`로 서버 로그의 요청을 추적 |
| AI 안전장치 | DB 후보 제한, 구조화 출력, contentId 재검증, 장소 수 제한 |
| 비밀 관리 | OpenAI 키는 백엔드 환경변수만 사용하며 `.env`는 커밋하지 않음 |

## 데이터 모델

| 테이블 | 역할 |
| --- | --- |
| `user_profiles` | 익명 커플 프로필과 인증 정보 |
| `places` | TourAPI 기반 대전 장소·좌표·분류·추천 속성 |
| `chat_sessions` | AI 대화 조건, 메시지, 코스 초안, 버전 |
| `date_courses` | AI/복사/재진행으로 생성된 현재·완료 코스 |
| `date_course_places` | 장소별 일정, 하트, 완료 시간, 장소 스냅샷 |
| `community_posts` | 완료 코스의 공개 게시글 |
| `community_likes` | 프로필별 게시글 좋아요 |
| `idempotency_records` | 재시도 가능한 쓰기 요청의 최초 응답 보관 |

## 실행 방법

Node.js 24와 Python 3.12가 필요합니다. 자세한 설정은 [개발환경 설정](docs/guides/setup.md)을
참고하세요.

```bash
cd frontend
npm install
npm run dev
```

```bash
cd backend
python -m venv .venv
python -m pip install -r requirements-dev.txt
python -m uvicorn app.main:app --reload
```

환경변수는 각 애플리케이션의 `.env.example`을 복사해 사용합니다. 실제 키나 비밀번호가 포함된
`.env`는 커밋하지 않습니다.

## 문서

- [API 명세](docs/specifications/api.md)
- [데이터베이스 명세](docs/specifications/database.md)
- [아키텍처 상세](docs/guides/architecture.md)
- [환경변수](docs/guides/environment-variables.md)
- [배포 설정](docs/guides/deployment.md)
