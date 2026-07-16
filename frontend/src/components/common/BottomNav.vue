<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const currentTab = computed(() => route.name as string)

async function navigate(tabName: string) {
  if (currentTab.value === tabName) return
  await router.push({ name: tabName })
}
</script>

<template>
  <nav class="nav" aria-label="주요 메뉴">
    <button :class="{ active: currentTab === 'chat' }" @click="navigate('chat')">
      <span class="nav-icon">✦</span><span class="nav-label">42봇</span>
    </button>
    <button :class="{ active: currentTab === 'ranking' }" @click="navigate('ranking')">
      <span class="nav-icon">♛</span><span class="nav-label">랭킹</span>
    </button>
    <button :class="{ active: currentTab === 'current' }" @click="navigate('current')">
      <span class="nav-icon">♥</span><span class="nav-label">현재 데이트</span>
    </button>
    <button :class="{ active: currentTab === 'history' }" @click="navigate('history')">
      <span class="nav-icon">▣</span><span class="nav-label">추억</span>
    </button>
  </nav>
</template>

<style scoped>
.nav {
  position: absolute;
  z-index: 30;
  bottom: 0;
  left: 0;
  right: 0;
  height: 76px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  padding: 7px 10px 9px;
  border-top: 1px solid rgba(235, 223, 225, 0.86);
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 -10px 26px rgba(80, 54, 62, 0.08);
  backdrop-filter: blur(16px);
}

button {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 4px;
  border-radius: 16px;
  background: transparent;
  color: #a99196;
  transition:
    color 0.2s ease,
    background 0.2s ease,
    transform 0.2s ease;
}

.nav-icon {
  width: 30px;
  height: 28px;
  display: grid;
  place-items: center;
  border-radius: 11px;
  background: #f7f2f3;
  font-size: 14px;
  font-weight: 900;
  transition: all 0.2s ease;
}

.nav-label {
  font-size: 8px;
  font-weight: 800;
}

button.active {
  background: linear-gradient(180deg, #fff1f4, #fbf5ff);
  color: #e75d74;
}

button.active::before {
  position: absolute;
  top: -7px;
  width: 24px;
  height: 3px;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--pink), #9d83db);
  content: '';
}

button.active .nav-icon {
  background: linear-gradient(145deg, var(--pink), #a084dc);
  box-shadow: 0 7px 13px rgba(211, 91, 132, 0.22);
  color: #fff;
  transform: translateY(-1px);
}
</style>
