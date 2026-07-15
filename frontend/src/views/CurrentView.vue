<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useDateStore } from '@/stores/dateStore'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import LeafletMap from '@/components/map/LeafletMap.vue'

const showMapModal = ref(false)

const store = useDateStore()
const router = useRouter()

const progressPct = computed(() => {
  return store.activeCourse?.progress.progressPercent ?? 0
})

function handleLikePlace(coursePlaceId: string, hearted: boolean) {
  void store.togglePlaceLike(coursePlaceId, hearted)
}

function handleNext(coursePlaceId: string) {
  void store.nextPlace(coursePlaceId)
}

function endDating() {
  store.showCommentModal = true
}

function navigateToChat() {
  store.startNewCourseSetup()
  router.push({ name: 'chat' })
}

onMounted(() => {
  void store.loadCurrentCourse()
})
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
          <span class="label">{{ store.activeCourse.date }} · 대전</span>
          <h3>{{ store.activeCourse.title }}</h3>
          <p class="desc">오늘의 날씨와 두 분의 취향을 반영했어요.</p>
          <div class="progress-meta">
            <span
              >{{ store.activeCourse.progress.completedPlaceCount }} /
              {{ store.activeCourse.progress.totalPlaceCount }} 장소</span
            >
            <span>{{ progressPct }}%</span>
          </div>
          <div class="progress-bar">
            <span :style="{ width: `${progressPct}%` }"></span>
          </div>
        </div>

        <!-- Minimap Wrapper -->
        <BaseCard class="minimap-wrapper">
          <LeafletMap
            v-if="store.activeCourse"
            :coords="
              store.activeCourse.places.flatMap((place) =>
                place.place.latitude !== null && place.place.longitude !== null
                  ? [[place.place.latitude, place.place.longitude]]
                  : [],
              )
            "
            :places="store.activeCourse.places.map((place) => place.place.name)"
            static
          />
          <button class="small-btn map-zoom-btn" @click="showMapModal = true">전체보기</button>
        </BaseCard>

        <!-- Places List -->
        <div class="place-list">
          <div
            v-for="place in store.activeCourse.places"
            :key="place.coursePlaceId"
            :class="[
              'place-card',
              { done: place.order < store.activeCourse.progress.currentOrderNo },
              { current: place.order === store.activeCourse.progress.currentOrderNo },
            ]"
          >
            <div class="step-badge">
              {{ place.order < store.activeCourse.progress.currentOrderNo ? '✓' : place.order }}
            </div>
            <div class="place-info">
              <h4>{{ place.place.name }}</h4>
              <p>
                {{
                  place.order === store.activeCourse.progress.currentOrderNo
                    ? '현재 방문 중이에요'
                    : place.order < store.activeCourse.progress.currentOrderNo
                      ? '다녀온 장소'
                      : '다음 장소'
                }}
              </p>
            </div>
            <div class="place-actions">
              <button
                class="like-toggle"
                @click="handleLikePlace(place.coursePlaceId, place.heartedByMe)"
              >
                {{ place.heartedByMe ? '♥ 좋아요' : '♡ 좋아요' }}
              </button>
              <button
                v-if="
                  place.order === store.activeCourse.progress.currentOrderNo &&
                  !store.activeCourse.progress.allPlacesCompleted
                "
                class="next-step-btn"
                @click="handleNext(place.coursePlaceId)"
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
    <!-- Fullscreen Map Modal -->
    <div
      v-if="showMapModal"
      class="overlay open map-modal-overlay"
      @click.self="showMapModal = false"
    >
      <div class="modal map-modal">
        <div class="modal-header">
          <h3>진행 중인 데이트 코스</h3>
          <button class="close-x-btn" @click="showMapModal = false">&times;</button>
        </div>
        <div class="modal-map-container" style="margin-bottom: 0">
          <LeafletMap
            v-if="store.activeCourse"
            :coords="
              store.activeCourse.places.flatMap((place) =>
                place.place.latitude !== null && place.place.longitude !== null
                  ? [[place.place.latitude, place.place.longitude]]
                  : [],
              )
            "
            :places="store.activeCourse.places.map((place) => place.place.name)"
          />
        </div>
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

.minimap-wrapper {
  height: 130px;
  margin-top: 11px;
  position: relative;
  overflow: hidden;
  border-radius: 21px;
  box-shadow: var(--shadow);
}

.map-zoom-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 10;
  min-height: 28px;
  padding: 0 8px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
  color: #db536a;
  font-size: 9px;
  font-weight: 800;
  border: 0;
}

.map-modal-overlay {
  position: absolute;
  z-index: 100;
  inset: 0;
  background: rgba(53, 42, 45, 0.45);
  backdrop-filter: blur(3px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.map-modal {
  width: 100%;
  max-width: 440px;
  height: 62vh;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 24px;
  padding: 16px;
  box-shadow: var(--shadow);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 800;
  flex: 1;
  text-align: center;
  padding-left: 24px;
}

.close-x-btn {
  font-size: 24px;
  font-weight: 300;
  color: var(--muted);
  background: transparent;
  border: 0;
  cursor: pointer;
  line-height: 1;
  padding: 4px 8px;
  transition: color 0.2s;
}

.close-x-btn:hover {
  color: var(--ink);
}

.modal-map-container {
  flex: 1;
  border-radius: 16px;
  overflow: hidden;
  margin-bottom: 0;
  border: 1px solid var(--line);
}
</style>
