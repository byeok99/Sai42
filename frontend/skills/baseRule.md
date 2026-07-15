# Frontend 개발 기본 규칙

## 1. 기본 작업 원칙
- 모든 frontend 개발 작업은 `feature/frontend-develop` 브랜치를 기준으로 진행한다.
- 새 작업은 이 브랜치 기반으로 생성하여 진행한다.
- 작업 전 브랜치가 `feature/frontend-develop`인지 확인한다.
- API spec, wireframe, 디자인 시스템을 기준으로 구현한다.

## 2. 아키텍처 방향
- 프론트엔드는 UI layer, feature layer, repository layer, service layer의 흐름으로 구성한다.
- use case layer는 필수가 아니며, 필요 시에만 추가한다.
- 데이터 흐름은 다음 순서를 따른다.
  1. endpoint 정의
  2. service layer에서 API 호출 처리
  3. repository layer에서 데이터 접근 추상화
  4. feature layer에서 화면 로직 처리
  5. UI layer에서 화면 표시

## 3. 구현 방향
- 화면은 wireframe 기반으로 구성한다.
- 페이지 단위로 구조를 나누고, 재사용 가능한 컴포넌트는 공통 UI로 분리한다.
- UI feature는 화면별 기능 단위로 나누어 구현한다.
- 디자인 시스템은 모바일 우선, base components 중심으로 구성한다.

## 4. 개발 우선순위
- 1순위: API spec 기반 데이터 계층 설계
- 2순위: 디자인 시스템 및 base components 구축
- 3순위: wireframe 기반 페이지 및 feature 구현
- 4순위: 서비스 연결 및 흐름 연동
- 5순위: 배포 전 검증 및 QA
