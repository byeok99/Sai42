# 개발환경 설정

## 사전 요구사항

- Git
- Node.js 24 및 npm
- Python 3.12

## Frontend

```bash
cd frontend
npm install
npm run dev
```

검증 명령은 다음과 같습니다.

```bash
npm run lint
npm run format:check
npm run type-check
npm run build
```

## Backend

가상환경은 `backend/.venv`에 생성합니다.

```bash
cd backend
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python -m uvicorn app.main:app --reload
```

서버 실행 후 다음 URL에서 공통 API를 직접 확인할 수 있습니다.

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`
- Health API: `http://localhost:8000/api/v1/health`
- Meta Options API: `http://localhost:8000/api/v1/meta/options`

Swagger UI의 `Try it out`을 사용하면 모든 현재·향후 API를 공통 응답 및 오류 schema와 함께
테스트할 수 있습니다.

macOS/Linux:

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python -m uvicorn app.main:app --reload
```

검증 명령은 다음과 같습니다.

```bash
python -m ruff check .
python -m ruff format --check .
python -c "from app.main import app; print(app.title)"
```

## 환경변수

각 애플리케이션에서 `.env.example`을 `.env`로 복사한 뒤 로컬 값만 입력합니다. `.env`는 Git에 포함되지 않습니다.

AI 코스 생성과 채팅 수정을 테스트하려면 `backend/.env`의 `OPENAI_API_KEY`에 서버용 OpenAI API
키를 입력합니다. `OPENAI_MODEL`, timeout, 재시도, 후보 수는 `.env.example`의 기본값으로 동작하며
필요할 때만 조정합니다. 서버 재시작 후 Swagger의 `/chat/sessions` 흐름을 테스트할 수 있습니다.
