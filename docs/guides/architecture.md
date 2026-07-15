# 아키텍처

## 개요

사이42는 하나의 Git 저장소에서 Vue 3 Frontend와 FastAPI Backend를 관리하는 모노레포입니다.

```text
Browser
  -> frontend/ (Vue 3 + Vite)
  -> backend/  (FastAPI)
  -> SQLite    (Backend에서 비동기 접근)
```

## Frontend

`frontend/src`는 컴포넌트, composable, router, service, store, type, utility, view를 역할별로 나눌 수 있도록 빈 디렉터리만 준비합니다. API 호출과 실제 상태 로직, 페이지 UI는 구현하지 않습니다.

## Backend

`backend/app`는 도메인 우선 구조를 유지하고, 각 도메인 안을 다음 네 레이어로 동일하게
분리합니다.

```text
app/<domain>/
├── presentation/    # FastAPI router, dependency, middleware, HTTP 응답 변환
├── application/     # 유스케이스 service와 입출력 DTO
├── domain/          # 외부 프레임워크와 독립적인 규칙, enum, 상수
└── infrastructure/  # SQLAlchemy model/repository와 외부 서비스 adapter
```

`auth`, `chat`, `common`, `community`, `course`, `history`, `place`, `ranking`, `weather`에 같은
레이어 패키지를 적용합니다. HTTP 요청은 `presentation`에서 받고 유스케이스는 `application`에
위임합니다. 영속성 구현은 `infrastructure`에 두며 실제 비즈니스 규칙은 router에 작성하지
않습니다. 최상위 `main.py`, `config.py`, `database.py`, `models.py`는 애플리케이션 조립과 공통
런타임 설정을 담당하므로 도메인 밖에 유지합니다.

현재 `common`에는 공통 응답·예외·요청 추적과 Health·Meta Options API가 있고, `auth`에는
익명 프로필 등록·검증·헤더 인증과 프로세스 단위 요청 제한이 있습니다. 닉네임 추천은
`places`에 저장된 추천 가능 공공 장소 이름을 사용합니다. `place`는 공공데이터 분류 규칙과
`places` 영속성 모델, 목록·상세·주변 장소 API를 제공합니다. 반경 검색은 SQLite에서 좌표
경계 상자를 먼저 조회한 후 애플리케이션 레이어에서 Haversine 거리로 재검증하며, 장소 응답은
추적 DB의 추천 가능 공공데이터만 사용합니다. `course`는 현재 데이트 코스의 조회, 순차 장소
완료, 장소 하트, 종료를 담당하며 종료와 `community_posts` 자동 공개를 하나의 트랜잭션으로
처리합니다. `Idempotency-Key`가 있는 종료 요청은 최초 공통 응답을 저장해 재사용합니다. Chat AI,
CourseDraft API는 아직 구현하지 않습니다. `weather`는 Open-Meteo 시간별 예보를 공급자 독립 DTO로
정규화하며 장애 시 사용 가능한 폴백 응답을 제공합니다. `community`, `ranking`, `history`는 완료
코스 스냅샷을 조회하고 좋아요를 집계하거나 새 활성 코스로 복사합니다.

## 데이터와 외부 서비스

별도로 전달받은 원본 데이터와 일반 SQLite 파일은 Git에서 제외합니다. Render 배포용
`backend/data/sai42.db`만 예외적으로 추적하며, 한국관광공사 TourAPI 장소 데이터는
`backend/scripts/import_places.py`로 검증 후 적재합니다. Render에서는 이 DB를 임시 로컬
파일로 사용하므로 런타임 변경은 재배포나 재시작 시 커밋된 상태로 초기화됩니다. Open-Meteo
무료 API는 별도 키 없이 서버에서 호출합니다. OpenAI와 Kakao Maps 연동은 환경변수 이름만
예약하며 실제 호출은 구현하지 않습니다.
