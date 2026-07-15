# ADR 0001: Frontend와 Backend를 모노레포로 관리

- 상태: 채택
- 날짜: 2026-07-15

## 배경

사이42의 Vue Frontend와 FastAPI Backend는 하나의 제품을 구성하며 API 계약과 개발 문서를 함께 관리해야 합니다.

## 결정

단일 Git 저장소의 `frontend/`와 `backend/` 디렉터리에서 각 애플리케이션을 독립적으로 설치·실행·배포합니다. 공통 문서와 자동화 설정은 저장소 루트에서 관리합니다.

## 결과

- 관련 변경을 하나의 Pull Request에서 검토할 수 있습니다.
- 각 애플리케이션은 별도의 패키지 관리자와 배포 설정을 유지합니다.
- CI는 Frontend와 Backend 검증을 독립 Job으로 실행합니다.
