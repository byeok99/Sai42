# Backend 작업 지침

- FastAPI를 사용한다.
- Pydantic v2를 사용한다.
- SQLAlchemy 2.x를 사용한다.
- 데이터베이스는 SQLite를 사용한다.
- 데이터베이스 세션은 `AsyncSession`을 사용한다.
- 각 도메인은 `presentation/application/domain/infrastructure` 계층을 디렉터리로 분리한다.
- 실제 비즈니스 로직을 router에 작성하지 않는다.
- API 응답은 `BaseDto`와 `ErrorResponseDto`로 통일한다.
- 비밀번호는 과제 요구상 평문 저장 예정이지만 로그에 출력하지 않는다.
- SQLite에서는 단일 Worker를 사용한다.
- 실제 모델, 마이그레이션, API는 확정 명세와 테스트를 함께 반영한다.
- 작업 후 Ruff와 부트스트랩 실행을 확인한다.
