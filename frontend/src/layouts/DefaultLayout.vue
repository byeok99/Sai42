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

      <div v-if="store.loading && !store.chatLoading" class="request-overlay" aria-live="polite">
        <div class="request-loader"><span>42</span><i>✨</i><b>💞</b></div>
        <strong>42봇이 정성껏 준비하고 있어요</strong>
        <p>LLM 기반 추천은 조금 시간이 걸릴 수 있어요.<br />느긋하게 기다려 주세요 ☕</p>
      </div>

      <!-- Toast Alerts -->
      <div :class="['toast', { show: store.toastVisible }]">
        {{ store.toastMessage }}
      </div>
    </div>
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

.request-overlay {
  position: absolute;
  z-index: 140;
  inset: 0;
  display: grid;
  place-content: center;
  justify-items: center;
  gap: 9px;
  padding: 28px;
  background: rgba(255, 250, 245, 0.91);
  text-align: center;
}
.request-overlay strong {
  font-size: 15px;
}
.request-overlay p {
  margin: 0;
  color: var(--muted);
  font-size: 11px;
  line-height: 1.6;
}
.request-loader {
  position: relative;
  width: 78px;
  height: 78px;
  display: grid;
  place-items: center;
  border-radius: 30px;
  background: linear-gradient(135deg, #ffe2e8, #e7ddff);
  color: #e75d74;
  font-size: 25px;
  font-weight: 900;
  animation: loader-float 1.4s ease-in-out infinite;
}
.request-loader i,
.request-loader b {
  position: absolute;
  font-style: normal;
  font-size: 17px;
}
.request-loader i {
  right: -9px;
  top: -8px;
}
.request-loader b {
  left: -10px;
  bottom: -8px;
}
@keyframes loader-float {
  50% {
    transform: translateY(-7px) rotate(3deg);
  }
}
</style>
