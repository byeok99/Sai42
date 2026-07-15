# Frontend Todo

## 1. 프로젝트 기준 및 구조 정리
- [ ] 프론트엔드 개발 기준(브랜치, 작업 순서, 커밋 규칙) 최종 확인
- [ ] 현재 폴더 구조와 기존 컴포넌트/페이지 기준 정리
- [ ] API 명세와 wireframe 기준으로 페이지/기능 우선순위 정의
- [ ] UI layer / feature layer / repository layer / service layer 구조 기준 확정

## 2. API 명세 기반 데이터 계층 설계
- [ ] API spec에서 endpoint, 요청/응답 DTO, 에러 포맷 정리
- [ ] 공통 API client/axios 또는 fetch 기반 세팅
- [ ] 타입 정의 파일 구성 (request/response/entity)
- [ ] Repository layer 설계 및 기본 구현
- [ ] Service layer 설계 및 비즈니스 로직 분리
- [ ] endpoint → service → repository 흐름 검증
- [ ] 로딩, 에러, 빈 상태 처리 공통 패턴 정의

## 3. 디자인 시스템 구축
- [ ] 와이어프레임 기반으로 공통 UI 패턴 정리
- [ ] 모바일 우선 레이아웃 기준 정의
- [ ] 공통 스타일 기준 정리 (spacing, typography, color, radius 등)
- [ ] Base components 구현
  - [ ] Button
  - [ ] Input / Textarea
  - [ ] Modal / Bottom sheet
  - [ ] Card / List item
  - [ ] Tabs / Segmented control
  - [ ] Badge / Chip
  - [ ] Header / Navigation bar
- [ ] Layout primitives 구현
  - [ ] Screen container
  - [ ] Safe area / padding 규칙
  - [ ] Responsive breakpoints

## 4. 화면 컴포넌트 및 페이지 구현
- [ ] wireframe 기반 주요 화면별 페이지 구조 분해
- [ ] 페이지 단위 디렉터리 구조 설계
- [ ] 각 화면에 필요한 feature-level component 구현
- [ ] 재사용 가능한 컴포넌트와 페이지 전용 컴포넌트 분리
- [ ] UI feature 단위로 기능 조합 및 상태 관리 구조 정리
- [ ] 모바일 UX에 맞는 인터랙션/전환/스크롤 동작 정리

### 페이지별 기능 정의
- [ ] 시작/인증 화면
  - [ ] 로그인/회원가입 진입 흐름
  - [ ] 데모 계정 로그인 또는 첫 등록 진입
- [ ] 커플 등록/온보딩 화면
  - [ ] 닉네임/비밀번호 입력
  - [ ] 커플 정보 등록 및 다음 단계 이동
- [ ] 성향 조사 화면
  - [ ] 버튼형 선택 UI 구현
  - [ ] 선택값 저장 및 다음 단계 연결
- [ ] 챗봇 대화 화면
  - [ ] 메시지 입력 UI
  - [ ] 빠른 버튼 기반 액션 처리
  - [ ] 날씨/축제 정보 표시
  - [ ] 코스 변경 요청 처리
- [ ] 지도/코스 화면
  - [ ] 가상 지도 마커 표시
  - [ ] 장소 탐색 및 선택 UI
  - [ ] 현재 위치/다음 장소 상태 표시
- [ ] 코스 확정/현재 데이트 화면
  - [ ] 추천 코스 확인 UI
  - [ ] 현재 데이트 등록 기능
  - [ ] 좋아요/다음 장소 진행 기능
- [ ] 데이트 종료/리뷰 화면
  - [ ] 한 줄 후기 입력
  - [ ] 평점 입력
  - [ ] 저장 후 완료 상태 처리
- [ ] 랭킹/공유 화면
  - [ ] 랭킹보드 표시
  - [ ] 다른 커플 코스 가져오기 기능
- [ ] 과거 데이트 기록 화면
  - [ ] 과거 코스 목록 조회
  - [ ] 상세 조회 및 재사용 흐름

## 5. 흐름 연결 및 상태 연동
- [ ] Router/페이지 흐름 연결
- [ ] service → repository → feature → UI 데이터 흐름 연결
- [ ] API 호출과 화면 상태 바인딩
- [ ] 사용자 액션(클릭, 입력, 제출)에 대한 이벤트 연결
- [ ] 예외 상황 처리 및 fallback UI 구성

## 6. 품질 및 배포 준비
- [ ] ESLint / TypeScript / 빌드 오류 점검
- [ ] 공통 에러 처리 및 로깅 포인트 정리
- [ ] 환경 변수 분리 (dev/staging/prod)
- [ ] 배포 설정 확인 및 빌드 검증
- [ ] 실제 배포 전 최종 QA 체크리스트 작성
