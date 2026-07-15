# 환경변수

예시 파일에는 실제 Secret을 넣지 않습니다. 로컬 `.env` 파일은 Git에서 제외됩니다.

## Frontend

| 이름                     | 용도                        | 기본/예시 값            |
| ------------------------ | --------------------------- | ----------------------- |
| `VITE_API_BASE_URL`      | Backend 기본 URL            | `http://localhost:8000` |
| `VITE_KAKAO_MAP_APP_KEY` | 향후 Kakao Maps 브라우저 키 | 빈 값                   |

`VITE_` 접두사가 붙은 값은 브라우저 번들에 노출될 수 있으므로 비밀값을 저장하지 않습니다.

## Backend

| 이름                       | 용도                              | 기본/예시 값                          |
| -------------------------- | --------------------------------- | ------------------------------------- |
| `APP_ENV`                  | 실행 환경 구분                    | `development`                         |
| `DATABASE_URL`             | 비동기 SQLite 연결 URL            | `sqlite+aiosqlite:///./data/sai42.db` |
| `CORS_ALLOWED_ORIGINS`     | 허용 Browser origin, 쉼표 구분    | `http://localhost:5173`               |
| `SQLITE_BUSY_TIMEOUT_MS`   | SQLite lock 대기 시간(ms)         | `5000`                                |
| `AUTH_RATE_LIMIT_MAX_ATTEMPTS` | 인증 실패·등록 시도 허용 횟수 | `10`                                  |
| `AUTH_RATE_LIMIT_WINDOW_SECONDS` | 인증 시도 제한 구간(초)     | `60`                                  |
| `OPENAI_API_KEY`           | 향후 OpenAI 연동                  | 빈 값                                 |
| `WEATHER_API_BASE_URL`     | Open-Meteo Forecast 요청 URL      | `https://api.open-meteo.com/v1/forecast` |
| `WEATHER_API_TIMEOUT_SECONDS` | 날씨 요청 제한 시간(초)       | `5`                                   |

백엔드는 `DATABASE_URL`을 읽어 비동기 DB 엔진을 구성합니다. 배포 환경의
`CORS_ALLOWED_ORIGINS`에는 실제 Netlify origin을 등록하며 `*`를 사용하지 않습니다. 외부 날씨
현재 사용하는 Open-Meteo 무료 API는 API 키가 필요하지 않습니다. 비상업 무료 사용은 일일 호출
한도가 있고 출처 표시가 필요하므로, 상용 배포 전에는 Open-Meteo 이용 조건과 유료 플랜을 다시
검토합니다. 공급자 장애가 발생하면 날씨 API는 HTTP 200과 `available=false`를 반환합니다. AI
공급자 연동은 아직 구현하지 않았습니다.
