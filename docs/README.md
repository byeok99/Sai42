# 사이42 문서 안내

이 디렉터리는 구현 기준 명세, 개발 가이드, 의사결정, 원본 자료를 역할별로 분리한다.

## 읽는 순서

1. [`specifications/README.md`](./specifications/README.md)에서 제품 불변 조건과 명세 간 책임을 확인한다.
2. [`specifications/functional.md`](./specifications/functional.md)에서 구현해야 할 사용자 기능을 확인한다.
3. [`specifications/api.md`](./specifications/api.md)에서 DTO, 엔드포인트, 오류 계약을 확인한다.
4. [`specifications/database.md`](./specifications/database.md)에서 저장 구조, 제약, 트랜잭션을 확인한다.
5. 실행·배포 작업은 [`guides/README.md`](./guides/README.md)를 참조한다.

## 디렉터리 구조

```text
docs/
├── README.md
├── specifications/        # 현재 구현 기준인 제품 계약
│   ├── README.md
│   ├── functional.md      # 기능 ID 60개
│   ├── api.md             # API 엔드포인트 32개
│   └── database.md        # DB 테이블 8개

├── guides/                # 개발·운영 절차
│   ├── README.md
│   ├── architecture.md
│   ├── setup.md
│   ├── environment-variables.md
│   └── deployment.md
├── decisions/             # 아키텍처 결정 기록
│   └── 0001-monorepo-architecture.md
└── sources/               # 전달받은 원본 PDF, 참고 전용
    ├── README.md
    ├── API-v3.0.pdf
    ├── DB-v4.0.pdf
    └── functional-spec.pdf
```

## 문서 우선순위

구현할 때는 `specifications/`의 Markdown을 기준으로 한다. `sources/`의 PDF는 원본 추적용이며, 확정 과정에서 제거된 평점·장소 UUID·복합 랭킹 산식 같은 과거 내용이 남아 있으므로 구현 계약으로 직접 사용하지 않는다.

명세끼리 다르게 보이는 경우 임의로 추정하지 말고 다음 책임 경계를 적용한다.

- 사용자 행동과 필수 여부: `functional.md`
- HTTP 요청·응답·오류: `api.md`
- 영속 데이터·제약·트랜잭션: `database.md`
- 개발환경과 운영 절차: `guides/`
- 결정 배경: `decisions/`
