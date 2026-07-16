<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDateStore } from '@/stores/dateStore'

const route = useRoute()
const router = useRouter()
const store = useDateStore()

const currentTab = computed(() => route.name as string)

async function navigate(tabName: string) {
  if (tabName === 'history') {
    await Promise.all([store.loadHistory(), store.loadRankings()])
  }
  if (tabName === 'ranking') {
    await store.loadRankings(1)
  }
  await router.push({ name: tabName })
}
</script>

<template>
  <nav class="nav">
    <button :class="{ active: currentTab === 'chat' }" @click="navigate('chat')">
      <b>💬</b><span>사이봇</span>
    </button>
    <button :class="{ active: currentTab === 'ranking' }" @click="navigate('ranking')">
      <b>🏆</b><span>랭킹</span>
    </button>
    <button :class="{ active: currentTab === 'current' }" @click="navigate('current')">
      <b>💗</b><span>현재 데이트</span>
    </button>
    <button :class="{ active: currentTab === 'history' }" @click="navigate('history')">
      <b>📮</b><span>추억</span>
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
  height: 74px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  padding: 8px 9px 10px;
  border-top: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.96);
}

button {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 3px;
  border-radius: 13px;
  background: transparent;
  color: #a99196;
}

button b {
  font-size: 18px;
}

button span {
  font-size: 9px;
  font-weight: 800;
}

button.active {
  background: #fff0f3;
  color: #e75d74;
}
</style>
