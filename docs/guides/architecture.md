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

`backend/app`는 도메인별 router/service/repository 구조를 사용합니다. 현재는 FastAPI 진입점,
공통 비동기 DB 세션, 공통 응답·예외·요청 추적, Health·Meta Options API, 공공데이터용
`places` 모델과 멱등성 레코드 마이그레이션을 제공합니다. Place API를 포함한 실제 비즈니스
API는 아직 구현하지 않습니다.

## 데이터와 외부 서비스

별도로 전달받은 원본 데이터와 일반 SQLite 파일은 Git에서 제외합니다. Render 배포용
`backend/data/sai42.db`만 예외적으로 추적하며, 한국관광공사 TourAPI 장소 데이터는
`backend/scripts/import_places.py`로 검증 후 적재합니다. Render에서는 이 DB를 임시 로컬
파일로 사용하므로 런타임 변경은 재배포나 재시작 시 커밋된 상태로 초기화됩니다. OpenAI, 날씨,
Kakao Maps 연동은 환경변수 이름만 예약하며 실제 호출은 구현하지 않습니다.
