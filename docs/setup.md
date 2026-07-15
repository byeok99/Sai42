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
