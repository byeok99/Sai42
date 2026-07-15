# Frontend Todo

## 현재 상태 요약 (2026-07-15)
- Swagger/OpenAPI 기준 API endpoint 구현률: 약 85%
- 요청/응답 DTO 정합성: 약 70%
- 전체 프런트 API 레이어 완성도: 약 78%

### 방금까지 확인된 내용
- Swagger에서 확인된 주요 endpoint들은 대부분 프런트 서비스/리포지토리 레이어로 구현되어 있음
- Identity / Place / Course / Community / Ranking / History 도메인별 repository/service 구조는 구성됨
- 최근 작업으로 DTO 필드 구조를 Swagger 방향에 더 가깝게 정리했고, 수정한 파일들 기준 에디터 진단 오류는 없음

### 아직 부족한 부분
- 실제 백엔드 응답 샘플이 없어서 DTO 필드명을 1:1로 완전히 맞추지는 못한 상태
- 인증 헤더 기반 공통 인증 유틸/스토어 연동이 아직 미완성
- API 에러 처리, 로딩/에러/빈 상태 패턴, 화면 컴포넌트 연결이 아직 남아 있음
- 실제 Vue 화면과 service → repository → API 흐름 연결은 다음 단계 작업

### 다음 우선순위
1. Swagger 응답 예시 기준으로 DTO 필드명과 타입을 더 엄밀하게 맞추기
2. 인증 헤더/공통 에러 처리/로딩 상태 패턴 연결하기
3. 실제 화면 컴포넌트와 API 레이어를 이어서 동작 확인하기
4. 해야할것 : 스웨거 응답 response에서 json 타입 키벨류 일치하는지 key mapper같은거 추가로 해야할거있는지 확인해야함.
5. 어디까지 스웨거 기준으로응답 json이 일치하는지 확실하게 확인해야함
6. 페이지별 ui와 service layer 연동해야함. 

- 그리고 추가로 챗봇 requset, response이거만 api 호출되면됨.

## 1. 프로젝트 기준 및 구조 정리
- [x] 프론트엔드 개발 기준(브랜치, 작업 순서, 커밋 규칙) 최종 확인
- [x] 현재 폴더 구조와 기존 컴포넌트/페이지 기준 정리
- [x] API 명세와 wireframe 기준으로 페이지/기능 우선순위 정의
- [x] UI layer / feature layer / repository layer / service layer 구조 기준 확정

## 2. API 명세 기반 데이터 계층 설계
- [x] API spec에서 endpoint, 요청/응답 DTO, 에러 포맷 정리
- [x] 공통 API client/axios 또는 fetch 기반 세팅
- [x] 타입 정의 파일 구성 (request/response/entity)
- [x] Repository layer 설계 및 기본 구현
- [x] Service layer 설계 및 비즈니스 로직 분리
- [x] endpoint → service → repository 흐름 검증
- [ ] 로딩, 에러, 빈 상태 처리 공통 패턴 정의

### 완료된 API 도메인 구현
- [x] Identity: 닉네임 추천, 프로필 생성, 프로필 검증, 내 프로필 조회
- [x] Place: 장소 목록/상세/주변 장소 조회
- [x] Chat: 채팅 세션 생성/조회/메시지 전송/확정/폐기
- [x] Course: 현재 코스 조회, 장소 완료, 장소 하트, 데이트 종료
- [x] Community: 게시글 목록/상세/생성/수정/삭제/좋아요/시작
- [x] Ranking: 데이트 마스터 목록 조회
- [x] History: 완료 코스 목록/상세/재진행

### 앞으로 구현할 API 관련 작업
- [ ] Swagger/OpenAPI 응답 스키마와 실제 DTO를 1:1로 맞추기
- [ ] 인증 헤더 기반 공통 인증 유틸/스토어 연동
- [ ] API 에러 처리 및 사용자 메시지 변환
- [ ] 로딩/에러/빈 상태를 공통 composable 또는 store로 정리
- [ ] 실제 화면 컴포넌트와 repository/service 연결
- [ ] Pinia store 또는 composable에서 API 호출 흐름 연결

## 3. 디자인 시스템 구축
- [x] 와이어프레임 기반으로 공통 UI 패턴 정리
- [x] 모바일 우선 레이아웃 기준 정의
- [x] 공통 스타일 기준 정리 (spacing, typography, color, radius 등)
- [x] Base components 구현
  - [x] Button
  - [x] Input / Textarea
  - [x] Modal / Bottom sheet
  - [x] Card / List item
  - [x] Tabs / Segmented control
  - [x] Badge / Chip
  - [x] Header / Navigation bar
- [x] Layout primitives 구현
  - [x] Screen container
  - [x] Safe area / padding 규칙
  - [x] Responsive breakpoints

## 4. 화면 컴포넌트 및 페이지 구현
- [x] wireframe 기반 주요 화면별 페이지 구조 분해
- [x] 페이지 단위 디렉터리 구조 설계
- [x] 각 화면에 필요한 feature-level component 구현
- [x] 재사용 가능한 컴포넌트와 페이지 전용 컴포넌트 분리
- [x] UI feature 단위로 기능 조합 및 상태 관리 구조 정리
- [x] 모바일 UX에 맞는 인터랙션/전환/스크롤 동작 정리

### 페이지별 기능 정의
- [x] 시작/인증 화면
  - [x] 로그인/회원가입 진입 흐름
  - [x] 데모 계정 로그인 또는 첫 등록 진입
- [x] 커플 등록/온보딩 화면
  - [x] 닉네임/비밀번호 입력
  - [x] 커플 정보 등록 및 다음 단계 이동
- [x] 성향 조사 화면
  - [x] 버튼형 선택 UI 구현
  - [x] 선택값 저장 및 다음 단계 연결
- [x] 챗봇 대화 화면
  - [x] 메시지 입력 UI
  - [x] 빠른 버튼 기반 액션 처리
  - [x] 날씨/축제 정보 표시
  - [x] 코스 변경 요청 처리
- [x] 지도/코스 화면
  - [x] 가상 지도 마커 표시
  - [x] 장소 탐색 및 선택 UI
  - [x] 현재 위치/다음 장소 상태 표시
- [x] 코스 확정/현재 데이트 화면
  - [x] 추천 코스 확인 UI
  - [x] 현재 데이트 등록 기능
  - [x] 좋아요/다음 장소 진행 기능
- [x] 데이트 종료/리뷰 화면
  - [x] 한 줄 후기 입력
  - [x] 평점 입력
  - [x] 저장 후 완료 상태 처리
- [x] 랭킹/공유 화면
  - [x] 랭킹보드 표시
  - [x] 다른 커플 코스 가져오기 기능
- [x] 과거 데이트 기록 화면
  - [x] 과거 코스 목록 조회
  - [x] 상세 조회 및 재사용 흐름

## 5. 흐름 연결 및 상태 연동
- [x] Router/페이지 흐름 연결
- [x] service → repository → feature → UI 데이터 흐름 연결 (Mock 상태 저장소 기반 연결 완료)
- [x] API 호출과 화면 상태 바인딩 (Mock API 액션 연동 완료)
- [x] 사용자 액션(클릭, 입력, 제출)에 대한 이벤트 연결
- [x] 예외 상황 처리 및 fallback UI 구성

## 6. 품질 및 배포 준비
- [x] ESLint / TypeScript / 빌드 오류 점검
- [ ] 공통 에러 처리 및 로깅 포인트 정리
- [x] 환경 변수 분리 (dev/staging/prod - import.meta.env.DEV 가드 적용 완료)
- [ ] 배포 설정 확인 및 빌드 검증
- [ ] 실제 배포 전 최종 QA 체크리스트 작성
