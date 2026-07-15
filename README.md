# 사이42

대전 지역번호 042와 “우리 사이”를 결합한, 대전 지역 AI 기반 데이트 코스 메이커 프로젝트입니다.

현재 저장소에는 Vue 3와 FastAPI 기반 모노레포 개발환경과 한국관광공사 TourAPI 장소 데이터를
저장하기 위한 SQLite 모델·마이그레이션·적재 도구가 구성되어 있습니다. 실제 API, 외부 서비스
연동, 페이지 UI는 아직 구현하지 않았습니다.

## 기술 스택

- Frontend: Vue 3, Vite, TypeScript, Vue Router, Pinia, Axios
- Backend: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.x, SQLite
- Quality: ESLint, Prettier, Ruff, GitHub Actions
- Deployment configuration: Netlify, Render

## 디렉터리

- `frontend/`: Vue 애플리케이션
- `backend/`: FastAPI 애플리케이션
- `docs/`: 명세 원본과 개발 문서
- `data/raw/`: 추후 원본 데이터 보관 위치

## 시작하기

Node.js 24와 Python 3.12가 필요합니다. 상세한 설치 및 실행 방법은 [개발환경 설정](docs/guides/setup.md)을 확인하세요.

```bash
cd frontend
npm install
npm run dev
```

```bash
cd backend
python -m venv .venv
python -m pip install -r requirements-dev.txt
python -m uvicorn app.main:app --reload
```

환경변수는 각 애플리케이션의 `.env.example`을 복사해 사용하며, 실제 키나 비밀번호가 포함된 `.env`는 커밋하지 않습니다.

## 문서

- [문서 안내](docs/README.md)
- [아키텍처](docs/guides/architecture.md)
- [환경변수](docs/guides/environment-variables.md)
- [배포 설정](docs/guides/deployment.md)
