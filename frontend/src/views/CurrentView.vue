<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useDateStore } from '@/stores/dateStore'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import LeafletMap from '@/components/map/LeafletMap.vue'
import PageHeader from '@/components/common/PageHeader.vue'

const showMapModal = ref(false)
const scrollArea = ref<HTMLElement | null>(null)
const pullDistance = ref(0)
const pullStartY = ref<number | null>(null)
const refreshing = ref(false)

const store = useDateStore()

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

function openCourseSurvey() {
  store.startNewCourseSetup()
}

async function refreshCurrentCourse() {
  if (refreshing.value) return
  refreshing.value = true
  const startedAt = Date.now()
  await store.loadCurrentCourse()
  const remainingDuration = 600 - (Date.now() - startedAt)
  if (remainingDuration > 0) await new Promise((resolve) => setTimeout(resolve, remainingDuration))
  refreshing.value = false
}

function startPull(event: TouchEvent) {
  if ((scrollArea.value?.scrollTop ?? 0) <= 0) pullStartY.value = event.touches[0]?.clientY ?? null
}

function movePull(event: TouchEvent) {
  if (pullStartY.value === null) return
  pullDistance.value = Math.min(
    78,
    Math.max(0, (event.touches[0]?.clientY ?? pullStartY.value) - pullStartY.value),
  )
}

function endPull() {
  const shouldRefresh = pullDistance.value >= 58
  pullStartY.value = null
  pullDistance.value = 0
  if (shouldRefresh) void refreshCurrentCourse()
}

onMounted(() => {
  void store.loadCurrentCourse()
})
</script>

<template>
  <div class="current-view">
    <PageHeader eyebrow="TODAY'S DATE" title="현재 데이트">
      <span v-if="store.activeCourse" class="live-badge">● 진행 중</span>
      <span v-else class="ready-badge">코스 준비 전</span>
    </PageHeader>

    <div
      ref="scrollArea"
      class="scroll-area"
      @touchstart="startPull"
      @touchmove="movePull"
      @touchend="endPull"
      @touchcancel="endPull"
    >
      <div
        class="pull-indicator"
        :class="{ visible: pullDistance > 0 || refreshing }"
        :style="{ height: `${refreshing ? 30 : pullDistance}px` }"
      >
        {{ refreshing ? '현재 데이트를 새로 불러오는 중…' : '놓으면 새로고침' }}
      </div>
      <!-- Empty State -->
      <div v-if="!store.activeCourse" class="empty-state">
        <BaseCard class="empty-hero">
          <div class="empty-map-visual" aria-hidden="true">
            <span class="route-line"></span>
            <i class="route-point point-one"><span>1</span></i>
            <i class="route-point point-two"><span>2</span></i>
            <i class="route-point point-three"><span>3</span></i>
            <b>💗</b>
          </div>
          <span class="empty-kicker">YOUR NEXT DATE</span>
          <h3>오늘의 둘을 위한 코스를<br />아직 준비하지 않았어요</h3>
          <p>날씨와 취향, 이동 방법을 알려주면 사이봇이 세 장소를 자연스럽게 이어드려요.</p>
          <BaseButton variant="primary" full @click="openCourseSurvey">
            오늘의 코스 만들기 →
          </BaseButton>
        </BaseCard>

        <section class="empty-benefits" aria-label="데이트 코스 준비 과정">
          <div><span>01</span><b>취향 확인</b><small>둘이 좋아하는 분위기</small></div>
          <div><span>02</span><b>동선 설계</b><small>가까운 세 장소 연결</small></div>
          <div><span>03</span><b>실시간 기록</b><small>하트와 방문 완료</small></div>
        </section>

        <BaseCard class="date-tip-card">
          <div class="tip-icon">✨</div>
          <div>
            <span>사이42 TIP</span>
            <strong>완료한 데이트는 추억 캘린더에 자동으로 기록돼요.</strong>
          </div>
        </BaseCard>
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
          <button class="small-btn map-zoom-btn" @click="showMapModal = true">지도 크게보기</button>
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
  background: linear-gradient(180deg, #fffaf7 0%, #fff7f9 60%, #f7f3ff 100%);
}

.pull-indicator {
  display: grid;
  place-items: center;
  overflow: hidden;
  color: var(--muted);
  font-size: calc(9px * 1.014);
  font-weight: 800;
  transition: height 0.15s ease;
}

.pull-indicator.visible {
  padding: 15px 0;
}

.live-badge {
  padding: 8px 10px;
  border-radius: 12px;
  background: #e4f6ee;
  color: #4e806c;
  font-size: 9px;
  font-weight: 800;
}

.ready-badge {
  padding: 8px 10px;
  border-radius: 999px;
  background: #f1eaff;
  color: #75648f;
  font-size: 8px;
  font-weight: 900;
}

.empty-state {
  display: grid;
  gap: 12px;
  padding: 16px 0 8px;
}

.empty-hero {
  position: relative;
  padding: 176px 20px 20px;
  overflow: hidden;
  border: 1px solid rgba(239, 207, 218, 0.8);
  background:
    radial-gradient(circle at 86% 8%, rgba(255, 255, 255, 0.78), transparent 24%),
    linear-gradient(145deg, #fff0e0, #ffe9ef 52%, #eee7ff);
  box-shadow: 0 16px 34px rgba(117, 76, 97, 0.14);
}

.empty-map-visual {
  position: absolute;
  top: 16px;
  right: 18px;
  left: 18px;
  height: 142px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.7);
  border-radius: 19px;
  background:
    linear-gradient(90deg, rgba(255, 255, 255, 0.55) 1px, transparent 1px),
    linear-gradient(rgba(255, 255, 255, 0.55) 1px, transparent 1px),
    linear-gradient(135deg, #e8f2eb, #eae6f6);
  background-size:
    28px 28px,
    28px 28px,
    auto;
}

.empty-map-visual::before,
.empty-map-visual::after {
  position: absolute;
  width: 250px;
  height: 60px;
  border: 8px solid rgba(255, 255, 255, 0.72);
  border-radius: 50%;
  content: '';
  transform: rotate(-12deg);
}

.empty-map-visual::before {
  top: 42px;
  left: -35px;
}

.empty-map-visual::after {
  right: -64px;
  bottom: -12px;
  transform: rotate(18deg);
}

.route-line {
  position: absolute;
  top: 67px;
  right: 68px;
  left: 55px;
  height: 3px;
  border-top: 3px dashed rgba(220, 82, 106, 0.48);
  transform: rotate(-7deg);
}

.route-point {
  position: absolute;
  z-index: 2;
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  border: 3px solid #fff;
  border-radius: 50% 50% 50% 7px;
  background: linear-gradient(145deg, var(--pink), #a187dc);
  box-shadow: 0 7px 14px rgba(95, 62, 84, 0.2);
  color: #fff;
  font-size: 8px;
  font-style: normal;
  font-weight: 900;
  transform: rotate(-45deg);
}

.route-point span {
  display: block;
  transform: rotate(45deg);
}

.point-one {
  top: 74px;
  left: 46px;
}

.point-two {
  top: 43px;
  left: 48%;
}

.point-three {
  top: 57px;
  right: 48px;
}

.empty-map-visual b {
  position: absolute;
  right: 14px;
  bottom: 10px;
  font-size: 24px;
}

.empty-kicker {
  color: #c55f76;
  font-size: 8px;
  font-weight: 900;
  letter-spacing: 0.13em;
}

.empty-hero h3 {
  margin: 5px 0 7px;
  font-size: 19px;
  font-weight: 900;
  line-height: 1.38;
}

.empty-hero p {
  color: var(--muted);
  font-size: 10px;
  line-height: 1.6;
  margin: 0 0 15px;
}

.empty-benefits {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.empty-benefits div {
  min-width: 0;
  padding: 13px 9px;
  border: 1px solid rgba(235, 225, 230, 0.84);
  border-radius: 17px;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: 0 8px 18px rgba(87, 57, 65, 0.06);
  text-align: center;
}

.empty-benefits span,
.empty-benefits b,
.empty-benefits small {
  display: block;
}

.empty-benefits span {
  color: #d5647c;
  font-size: 8px;
  font-weight: 900;
}

.empty-benefits b {
  margin: 5px 0 3px;
  font-size: 10px;
}

.empty-benefits small {
  overflow: hidden;
  color: var(--muted);
  font-size: 7px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.date-tip-card {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 13px 15px;
  border: 1px solid rgba(220, 209, 255, 0.7);
  background: linear-gradient(135deg, #fff, #f4efff);
}

.tip-icon {
  width: 38px;
  height: 38px;
  display: grid;
  flex: none;
  place-items: center;
  border-radius: 13px;
  background: #eee7ff;
}

.date-tip-card span {
  display: block;
  color: #8c72b5;
  font-size: 7px;
  font-weight: 900;
  letter-spacing: 0.1em;
}

.date-tip-card strong {
  display: block;
  margin-top: 3px;
  font-size: 9px;
  line-height: 1.45;
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
