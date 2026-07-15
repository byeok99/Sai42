<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useDateStore } from '@/stores/dateStore'
import BottomNav from '@/components/common/BottomNav.vue'
import SurveyModal from '@/components/common/SurveyModal.vue'
import CommentModal from '@/components/common/CommentModal.vue'

const route = useRoute()
const store = useDateStore()

const showNav = computed(() => route.name !== 'entrance' && route.name !== undefined)
const isDev = import.meta.env.DEV
</script>

<template>
  <div class="shell">
    <div class="phone">
      <!-- Status Bar Area -->
      <div class="status-bar">
        <span>9:42</span>
        <span>● ●● 100%</span>
      </div>

      <!-- App Content Area -->
      <div class="app-container">
        <main :class="['page', { 'with-nav': showNav }]">
          <RouterView />
        </main>
      </div>

      <!-- Bottom Tab Navigation -->
      <BottomNav v-if="showNav" />

      <!-- Overlays and Sheets -->
      <SurveyModal />
      <CommentModal />

      <!-- Toast Alerts -->
      <div :class="['toast', { show: store.toastVisible }]">
        {{ store.toastMessage }}
      </div>
    </div>

    <!-- Desktop Sidebar Guide Panel -->
    <aside v-if="isDev" class="desktop-note">
      <strong>사이42 웹 프레임</strong>
      <p>
        입장 → 취향 조사 → 챗봇 코스 조정 → 지도 확인 → 코스 결정 → 데이트 진행 → 후기 등록 흐름을
        이용하실 수 있습니다.
      </p>
      <div class="demo">
        <b>데모 계정</b>
        닉네임: 복숭아와호두<br />
        비밀번호: 0420
      </div>
    </aside>
  </div>
</template>

<style scoped>
.toast {
  position: absolute;
  z-index: 150;
  left: 50%;
  bottom: 90px;
  transform: translate(-50%, 20px);
  opacity: 0;
  max-width: calc(100% - 34px);
  padding: 11px 14px;
  border-radius: 14px;
  background: rgba(57, 45, 48, 0.92);
  color: #fff;
  font-size: 9px;
  font-weight: 800;
  transition: all 0.22s;
  pointer-events: none;
  text-align: center;
}

.toast.show {
  transform: translate(-50%, 0);
  opacity: 1;
}

.demo {
  padding: 11px;
  border-radius: 14px;
  background: #fff2f5;
  font-size: 10px;
  line-height: 1.55;
  margin-top: 10px;
}

.demo b {
  display: block;
  color: #df5269;
}
</style>
