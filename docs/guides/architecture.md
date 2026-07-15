# 아키텍처

## 개요

사이42는 하나의 Git 저장소에서 Vue 3 Frontend와 FastAPI Backend를 관리하는 모노레포입니다.

```text
Browser
  -> frontend/ (Vue 3 + Vite)
  -> backend/  (FastAPI)
  -> SQLite    (향후 Backend에서 비동기 접근)
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

현재 `common`에는 공통 응답·예외·요청 추적과 Health·Meta Options API가 있고, `place`에는
공공데이터 분류 규칙과 `places` 영속성 모델이 있습니다. Place API를 포함한 실제 비즈니스
API는 아직 구현하지 않습니다.

## 데이터와 외부 서비스

별도로 전달받은 원본 데이터와 일반 SQLite 파일은 Git에서 제외합니다. Render 배포용
`backend/data/sai42.db`만 예외적으로 추적하며, 한국관광공사 TourAPI 장소 데이터는
`backend/scripts/import_places.py`로 검증 후 적재합니다. Render에서는 이 DB를 임시 로컬
파일로 사용하므로 런타임 변경은 재배포나 재시작 시 커밋된 상태로 초기화됩니다. OpenAI, 날씨,
Kakao Maps 연동은 환경변수 이름만 예약하며 실제 호출은 구현하지 않습니다.
