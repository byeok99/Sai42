# Frontend 작업 지침

- Vue 3 Composition API와 `<script setup>`을 사용한다.
- TypeScript를 사용한다.
- Vue Router와 Pinia를 사용한다.
- API 요청은 향후 `services` 계층에서 수행한다.
- 컴포넌트에서 Axios를 직접 호출하지 않는다.
- 모바일 우선 UI를 적용한다.
- Kakao 지도 SDK 로딩은 향후 단일 Loader로 관리한다.
- 실제 API Key를 하드코딩하지 않는다.
- 비밀번호를 `localStorage`에 저장하지 않는다.
- 작업 후 lint, type-check, build를 실행한다.
- 초기 설정 작업에서는 화면 기능을 구현하지 않는다.
