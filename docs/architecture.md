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

`backend/app`는 향후 도메인별 router/service/repository 구조를 추가할 수 있도록 빈 Python 패키지만 준비합니다. 현재는 FastAPI 애플리케이션 객체를 제공하는 최소 진입점만 존재합니다. 모델, API, 마이그레이션은 구현하지 않습니다.

## 데이터와 외부 서비스

SQLite 파일과 원본 데이터는 Git에서 제외합니다. OpenAI, 날씨, Kakao Maps 연동은 환경변수 이름만 예약하며 실제 호출은 구현하지 않습니다.
