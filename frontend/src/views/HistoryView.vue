<script setup lang="ts">
import { computed } from 'vue'
import { useDateStore } from '@/stores/dateStore'
import BaseCard from '@/components/common/BaseCard.vue'

const store = useDateStore()

const averageRating = computed(() => {
  if (store.history.length === 0) return '0.0'
  const sum = store.history.reduce((acc, curr) => acc + curr.rating, 0)
  return (sum / store.history.length).toFixed(1)
})

const totalPlacesVisited = computed(() => {
  return store.history.reduce((acc, curr) => acc + curr.places.length, 0)
})

function showInfo() {
  store.triggerToast('월별·테마별 필터가 들어갈 자리예요')
}
</script>

<template>
  <div class="history-view">
    <header class="top-bar">
      <div>
        <p class="section-label">OUR MEMORY</p>
        <h2>옛날 데이트 코스</h2>
      </div>
      <button class="info-btn" @click="showInfo">⌁</button>
    </header>

    <div class="scroll-area">
      <!-- Stats Summary Card -->
      <BaseCard class="summary-card">
        <div>
          <strong>{{ store.history.length }}</strong>
          <span>함께한 데이트</span>
        </div>
        <div>
          <strong>{{ totalPlacesVisited }}</strong>
          <span>방문한 장소</span>
        </div>
        <div>
          <strong>{{ averageRating }}</strong>
          <span>평균 설렘</span>
        </div>
      </BaseCard>

      <!-- Month Header -->
      <div class="month-header">
        <strong>2026년 7월</strong>
        <span>우리의 기록</span>
      </div>

      <!-- History List -->
      <div class="hlist">
        <BaseCard v-for="(item, idx) in store.history" :key="idx" class="history-card">
          <div class="hhead">
            <div class="date-badge">{{ item.date }}</div>
            <div>
              <span class="label">7월 · {{ '★'.repeat(item.rating) }}</span>
              <h3>{{ item.title }}</h3>
              <p>{{ item.places.length }}개 장소 · 대전</p>
            </div>
          </div>
          <div class="hcomment">“{{ item.comment }}”</div>
          <div class="places">
            <span v-for="place in item.places" :key="place">{{ place }}</span>
          </div>
        </BaseCard>
      </div>
    </div>
  </div>
</template>

<style scoped>
.history-view {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.top-bar {
  height: 72px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px 10px;
  background: var(--cream);
  border-bottom: 1px solid var(--line);
}

.section-label {
  margin: 0;
  color: #e75d74;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.top-bar h2 {
  margin: 3px 0 0;
  font-size: 21px;
  font-weight: 800;
}

.info-btn {
  width: 36px;
  height: 36px;
  border-radius: 13px;
  background: #fff;
  box-shadow: var(--shadow);
  font-weight: 900;
  border: 0;
  cursor: pointer;
  color: var(--ink);
  display: grid;
  place-items: center;
}

.summary-card {
  padding: 14px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  background: linear-gradient(135deg, #ffe7eb, #eee8ff);
  margin-top: 15px;
}

.summary-card div {
  text-align: center;
}

.summary-card div + div {
  border-left: 1px solid rgba(85, 61, 68, 0.12);
}

.summary-card strong {
  display: block;
  font-size: 18px;
  font-weight: 800;
}

.summary-card span {
  font-size: 8px;
  color: var(--muted);
}

.month-header {
  display: flex;
  justify-content: space-between;
  padding: 17px 3px 9px;
  font-size: 12px;
}

.month-header span {
  color: var(--muted);
  font-size: 9px;
}

.hlist {
  display: grid;
  gap: 10px;
}

.history-card {
  padding: 13px;
}

.hhead {
  display: flex;
  gap: 10px;
}

.date-badge {
  width: 43px;
  height: 43px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  background: #ffe4e9;
  color: #dc526a;
  font-weight: 900;
}

.label {
  display: block;
  color: #e75d74;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.history-card h3 {
  margin: 2px 0 4px;
  font-size: 12px;
  font-weight: 800;
}

.history-card p {
  margin: 0;
  color: var(--muted);
  font-size: 8px;
}

.hcomment {
  margin-top: 10px;
  padding: 9px;
  border-radius: 11px;
  background: #f8f3f1;
  font-size: 9px;
  line-height: 1.5;
}

.places {
  display: flex;
  gap: 5px;
  overflow-x: auto;
  margin-top: 9px;
  scrollbar-width: none;
}

.places::-webkit-scrollbar {
  display: none;
}

.places span {
  flex: none;
  padding: 6px 8px;
  border-radius: 9px;
  background: #f3efed;
  font-size: 8px;
  font-weight: 700;
}
</style>
