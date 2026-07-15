# 배포 설정

## Frontend: Netlify

`frontend/netlify.toml`은 `npm run build` 결과인 `frontend/dist`를 게시하도록 구성합니다. SPA 경로 새로고침을 위해 모든 경로를 `index.html`로 전달합니다.

Netlify 사이트 설정에서 Base directory를 `frontend`로 지정하고 필요한 환경변수를 별도로 등록합니다.

## Backend: Render

`backend/render.yaml`은 `backend/requirements.txt`를 설치하고, Alembic 마이그레이션을 적용한
뒤 Uvicorn 단일 Worker로 FastAPI 애플리케이션을 실행합니다. SQLite에서 여러 프로세스가 같은
파일에 쓰는 상황을 피하기 위해 Worker는 하나만 사용합니다.

Blueprint는 `/api/v1/health`를 HTTP health check로 사용합니다. `PYTHON_VERSION` 환경변수는
Render 요구사항에 맞게 patch까지 포함한 Python 3.12 버전으로 고정합니다. Netlify 배포가
정해지면 `CORS_ALLOWED_ORIGINS`에 실제 사이트 origin을 입력합니다.

Render Blueprint를 생성할 때 Blueprint Path를 `backend/render.yaml`로 지정합니다. Blueprint를
사용하지 않고 Web Service를 직접 만들 경우 Root Directory를 `backend`로 지정하고 같은 빌드
명령, 시작 명령과 환경변수를 등록합니다.

배포 DB는 저장소의 `backend/data/sai42.db`이며 Render의 `rootDir: backend`를 기준으로
`sqlite+aiosqlite:///./data/sai42.db`에 연결합니다. 이 파일에는 한국관광공사 공공데이터와
과제용 테스트 데이터만 저장합니다. 실제 개인정보나 Secret은 넣지 않습니다.

## SQLite 파일 배포 정책

이 서비스는 별도의 Persistent Disk 없이 Git에 포함된 SQLite 파일을 배포 초기 상태로
사용합니다. 실행 중 생성되는 사용자, 코스, 커뮤니티 데이터는 같은 DB 파일에서 정상적으로
읽고 쓸 수 있지만 Render의 로컬 파일시스템은 임시 저장소이므로 다음 이벤트가 발생하면 Git에
커밋된 DB 상태로 돌아갑니다.

- 새 커밋 배포 또는 수동 재배포
- 서비스 재시작
- Free 인스턴스의 종료 및 재기동

따라서 이 구성은 데이터 초기화가 허용되는 교육·시연 서비스에만 사용합니다. 사용자 데이터의
영구 보존이 필요해지면 Persistent Disk 또는 외부 DB로 이전해야 합니다.

## 배포 전 확인

1. 로컬에서 `python -m alembic upgrade head`를 실행합니다.
2. `backend/data/sai42.db`의 공공데이터 건수와 무결성을 확인합니다.
3. DB에 실제 개인정보, 실제 비밀번호 또는 Secret이 없는지 확인합니다.
4. 코드와 배포용 DB 스냅샷을 같은 커밋에 포함합니다.

운영 Secret은 Render 환경변수에 등록하며 저장소나 SQLite 파일에 기록하지 않습니다.
