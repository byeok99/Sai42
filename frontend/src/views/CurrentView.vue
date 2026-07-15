<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useDateStore } from '@/stores/dateStore'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import LeafletMap from '@/components/map/LeafletMap.vue'

const store = useDateStore()
const router = useRouter()

const progressPct = computed(() => {
  if (!store.activeCourse) return 0
  const total = store.activeCourse.places.length
  return Math.round(((store.activeProgress + 1) / total) * 100)
})

function handleLikePlace(idx: number) {
  store.togglePlaceLike(idx)
}

function handleNext() {
  store.nextPlace()
}

function endDating() {
  store.showCommentModal = true
}

function navigateToChat() {
  router.push({ name: 'chat' })
}
</script>

<template>
  <div class="current-view">
    <header class="top-bar">
      <div>
        <p class="section-label">TODAY</p>
        <h2>현재 데이트</h2>
      </div>
      <span v-if="store.activeCourse" class="live-badge">● 진행 중</span>
    </header>

    <div class="scroll-area">
      <!-- Empty State -->
      <div v-if="!store.activeCourse" class="empty-state">
        <div class="empty-emoji">🗺️</div>
        <h3>아직 오늘의 코스가 없어요</h3>
        <p>사이봇과 대화해서 두 분만의 코스를 만들어 보세요.</p>
        <BaseButton variant="primary" @click="navigateToChat"> 코스 만들기 </BaseButton>
      </div>

      <!-- Active Course Body -->
      <div v-else class="active-body">
        <div class="today-card">
          <span class="label">2026. 07. 15 · 대전</span>
          <h3>{{ store.activeCourse.title }}</h3>
          <p class="desc">오늘의 날씨와 두 분의 취향을 반영했어요.</p>
          <div class="progress-meta">
            <span
              >{{ store.activeProgress + 1 }} / {{ store.activeCourse.places.length }} 장소</span
            >
            <span>{{ progressPct }}%</span>
          </div>
          <div class="progress-bar">
            <span :style="{ width: `${progressPct}%` }"></span>
          </div>
        </div>

        <!-- Minimap Wrapper -->
        <BaseCard class="minimap">
          <LeafletMap
            v-if="store.activeCourse"
            :coords="store.activeCourse.coords"
            :places="store.activeCourse.places"
          />
        </BaseCard>

        <!-- Places List -->
        <div class="place-list">
          <div
            v-for="(place, idx) in store.activeCourse.places"
            :key="place"
            :class="[
              'place-card',
              { done: idx < store.activeProgress },
              { current: idx === store.activeProgress },
            ]"
          >
            <div class="step-badge">
              {{ idx < store.activeProgress ? '✓' : idx + 1 }}
            </div>
            <div class="place-info">
              <h4>{{ place }}</h4>
              <p>
                {{
                  idx === store.activeProgress
                    ? '현재 방문 중이에요'
                    : idx < store.activeProgress
                      ? '다녀온 장소'
                      : '다음 장소'
                }}
              </p>
            </div>
            <div class="place-actions">
              <button class="like-toggle" @click="handleLikePlace(idx)">
                {{ store.activeCourse.likes[idx] ? '♥ 좋아요' : '♡ 좋아요' }}
              </button>
              <button
                v-if="idx === store.activeProgress && idx < store.activeCourse.places.length - 1"
                class="next-step-btn"
                @click="handleNext"
              >
                다음 장소
              </button>
            </div>
          </div>
        </div>

        <BaseButton variant="primary" class="end-btn" @click="endDating">
          데이트 종료하기
        </BaseButton>
        <p class="help-text">종료 후 한 줄 코멘트를 남기면 랭킹보드에 공유돼요.</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.current-view {
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

.live-badge {
  padding: 8px 10px;
  border-radius: 12px;
  background: #e4f6ee;
  color: #4e806c;
  font-size: 9px;
  font-weight: 800;
}

.empty-state {
  text-align: center;
  padding: 65px 24px;
}

.empty-emoji {
  font-size: 55px;
}

.empty-state h3 {
  margin: 13px 0 7px;
  font-size: 16px;
  font-weight: 800;
}

.empty-state p {
  color: var(--muted);
  font-size: 11px;
  line-height: 1.5;
  margin-bottom: 20px;
}

.active-body {
  margin-top: 15px;
}

.today-card {
  padding: 17px;
  background: linear-gradient(135deg, #fff0cc, #ffe3e7);
  border-radius: 21px;
  box-shadow: var(--shadow);
}

.label {
  display: block;
  color: #e75d74;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.today-card h3 {
  margin: 5px 0 6px;
  font-size: 17px;
  font-weight: 800;
}

.desc {
  margin: 4px 0 0;
  color: var(--muted);
  font-size: 10px;
}

.progress-meta {
  display: flex;
  justify-content: space-between;
  margin: 14px 0 6px;
  color: var(--muted);
  font-size: 9px;
  font-weight: 800;
}

.progress-bar {
  height: 8px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 8px;
  overflow: hidden;
}

.progress-bar span {
  display: block;
  height: 100%;
  background: var(--pink);
  transition: width 0.25s ease-in-out;
}

.minimap {
  height: 130px;
  margin-top: 11px;
  position: relative;
  overflow: hidden;
  background:
    linear-gradient(90deg, rgba(255, 255, 255, 0.55) 1px, transparent 1px),
    linear-gradient(rgba(255, 255, 255, 0.55) 1px, transparent 1px), #e3ece5;
  background-size: 28px 28px;
}

.marker {
  position: absolute;
  z-index: 3;
  width: 31px;
  height: 31px;
  display: grid;
  place-items: center;
  border: 3px solid #fff;
  border-radius: 50% 50% 50% 5px;
  transform: rotate(-45deg);
  background: var(--pink);
  color: #fff;
  font-size: 10px;
  font-weight: 900;
  box-shadow: var(--marker-shadow);
}

.marker i {
  font-style: normal;
  transform: rotate(45deg);
}

.place-list {
  display: grid;
  gap: 9px;
  margin: 11px 0;
}

.place-card {
  display: grid;
  grid-template-columns: 36px 1fr auto;
  gap: 10px;
  align-items: center;
  padding: 12px;
  background: #fff;
  border-radius: 17px;
  box-shadow: var(--shadow);
}

.place-card.current {
  outline: 2px solid rgba(255, 130, 149, 0.35);
}

.step-badge {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border-radius: 13px;
  background: var(--pink);
  color: #fff;
  font-size: 10px;
  font-weight: 900;
}

.place-card.done .step-badge {
  background: #76c2a3;
}

.place-info h4 {
  margin: 0 0 4px;
  font-size: 11px;
  font-weight: 800;
}

.place-info p {
  margin: 0;
  color: var(--muted);
  font-size: 8px;
}

.place-actions {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.place-actions button {
  padding: 7px;
  border-radius: 10px;
  font-size: 8px;
  font-weight: 800;
  border: 0;
}

.like-toggle {
  background: #fff0f2;
  color: #d2576b;
}

.next-step-btn {
  background: #eee8ff;
  color: #66568d;
}

.end-btn {
  background: #ffe7eb;
  color: #c84d61;
  box-shadow: none;
  font-weight: 800;
  width: 100%;
}

.help-text {
  text-align: center;
  color: var(--muted);
  font-size: 10px;
  margin-top: 10px;
}
</style>
