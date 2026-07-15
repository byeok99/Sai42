# 배포 기본 설정

이 문서는 배포 설정 파일의 의도만 설명합니다. 이번 초기 세팅에서는 실제 배포를 수행하지 않습니다.

## Frontend: Netlify

`frontend/netlify.toml`은 `npm run build` 결과인 `frontend/dist`를 게시하도록 구성합니다. SPA 경로 새로고침을 위해 모든 경로를 `index.html`로 전달합니다.

Netlify 사이트 설정에서 Base directory를 `frontend`로 지정하고 필요한 환경변수를 별도로 등록합니다.

## Backend: Render

`backend/render.yaml`은 `backend/requirements.txt`를 설치하고 Uvicorn 단일 Worker로 FastAPI 애플리케이션을 실행하도록 구성합니다. SQLite 사용 시 여러 Worker가 동일 파일을 공유하지 않도록 단일 Worker를 유지합니다.

운영 Secret은 Render 환경변수에 등록하며 저장소에 기록하지 않습니다. SQLite 파일은 기본적으로 영구 저장소가 아니므로 실제 배포 설계 단계에서 Render Disk 또는 별도 데이터베이스 사용 여부를 결정해야 합니다.
