# 환경변수

예시 파일에는 실제 Secret을 넣지 않습니다. 로컬 `.env` 파일은 Git에서 제외됩니다.

## Frontend

| 이름                     | 용도                        | 기본/예시 값            |
| ------------------------ | --------------------------- | ----------------------- |
| `VITE_API_BASE_URL`      | Backend 기본 URL            | `http://localhost:8000` |
| `VITE_KAKAO_MAP_APP_KEY` | 향후 Kakao Maps 브라우저 키 | 빈 값                   |

`VITE_` 접두사가 붙은 값은 브라우저 번들에 노출될 수 있으므로 비밀값을 저장하지 않습니다.

## Backend

| 이름              | 용도                        | 기본/예시 값                          |
| ----------------- | --------------------------- | ------------------------------------- |
| `APP_ENV`         | 실행 환경 구분              | `development`                         |
| `DATABASE_URL`    | 향후 비동기 SQLite 연결 URL | `sqlite+aiosqlite:///./data/sai42.db` |
| `OPENAI_API_KEY`  | 향후 OpenAI 연동            | 빈 값                                 |
| `WEATHER_API_KEY` | 향후 날씨 API 연동          | 빈 값                                 |

현재 초기 애플리케이션은 위 값을 읽거나 외부 API를 호출하지 않습니다.
