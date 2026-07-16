<script setup lang="ts">
import { computed, ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useDateStore } from '@/stores/dateStore'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseBadge from '@/components/common/BaseBadge.vue'
import LeafletMap from '@/components/map/LeafletMap.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import { formatDistrict } from '@/utils/district'
import type { WeatherCondition } from '@/types/api/course'

const store = useDateStore()
const router = useRouter()

const chatInput = ref('')
const messagesContainer = ref<HTMLDivElement | null>(null)
const showMapModal = ref(false)
const showProfileMenu = ref(false)

const nearbyPreviewPlaces = ['한밭수목원', '대전시립미술관', '엑스포다리']
const nearbyPreviewCoords: [number, number][] = [
  [36.3675, 127.388],
  [36.367, 127.387],
  [36.376, 127.389],
]
const hasCourseDraft = computed(() => store.course.places.length > 0)
const displayedPlaces = computed(() =>
  hasCourseDraft.value ? store.course.places : nearbyPreviewPlaces,
)
const displayedCoords = computed(() =>
  hasCourseDraft.value ? store.course.coords : nearbyPreviewCoords,
)
const displayedWeather = computed(() => store.course.weather ?? store.todayWeather)

function weatherEmoji(condition: WeatherCondition | null) {
  if (condition === 'RAIN' || condition === 'LIGHT_RAIN' || condition === 'RAIN_SNOW') return '🌦️'
  if (condition === 'SNOW') return '❄️'
  if (condition === 'CLOUDY' || condition === 'OVERCAST') return '⛅'
  return '☀️'
}

function handleLogout() {
  store.logout()
  router.push({ name: 'entrance' })
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

function handleSend() {
  if (!chatInput.value.trim() || store.chatLoading) return
  void store.sendChatMessage(chatInput.value)
  chatInput.value = ''
  scrollToBottom()
}

function handleQuickAction(
  action: 'CHANGE_CAFE' | 'ADD_NIGHT_VIEW' | 'REDUCE_ROUTE' | 'INCREASE_INDOOR',
) {
  if (store.chatLoading) return
  void store.sendQuickAction(action)
  scrollToBottom()
}

function triggerMapFit() {
  showMapModal.value = true
}

async function confirmCourse() {
  if (await store.decideCourse()) router.push({ name: 'current' })
}

function startCourseSetup() {
  store.startNewCourseSetup()
}

function goToCurrentDate() {
  showProfileMenu.value = false
  void router.push({ name: 'current' })
}

onMounted(async () => {
  await Promise.all([store.loadCurrentCourse(), store.loadTodayWeather()])
  if (!store.activeCourse) store.fetchChatSession()
  scrollToBottom()
})
</script>

<template>
  <div class="chat-view">
    <PageHeader eyebrow="AI DATE MAKER" title="사이봇과 코스 만들기">
      <div class="profile-wrapper">
        <button class="profile-chip" @click="showProfileMenu = !showProfileMenu">
          💞 {{ store.name || '우리 취향' }}
        </button>
        <div v-if="showProfileMenu" class="profile-menu">
          <button @click="goToCurrentDate">취향 수정</button>
          <button @click="handleLogout" class="logout-item">로그아웃</button>
        </div>
      </div>
      <!-- click outside to close menu -->
      <div v-if="showProfileMenu" class="menu-overlay" @click="showProfileMenu = false"></div>
    </PageHeader>

    <div class="scroll-area">
      <!-- Weather Card -->
      <BaseCard v-if="displayedWeather" class="weather-card">
        <div class="weather-left">
          <span class="emoji">{{ weatherEmoji(displayedWeather.condition) }}</span>
          <div>
            <strong>
              {{
                displayedWeather.district === 'ANY'
                  ? '대전'
                  : formatDistrict(displayedWeather.district)
              }}
              {{ displayedWeather.temperatureMin ?? '-' }}°C
              <template v-if="displayedWeather.temperatureMax !== null">
                · {{ displayedWeather.temperatureMax }}°C
              </template>
            </strong>
            <p>{{ displayedWeather.summary || '오늘의 대전 날씨를 확인했어요.' }}</p>
          </div>
        </div>
        <BaseBadge variant="default">
          강수 {{ displayedWeather.precipitationProbability ?? 0 }}%
        </BaseBadge>
      </BaseCard>
      <BaseCard class="weather-card" v-else>
        <div class="weather-left">
          <span class="emoji">🌦️</span>
          <div>
            <strong>{{
              store.weatherLoading ? '대전 날씨 불러오는 중...' : '날씨를 준비하지 못했어요'
            }}</strong>
            <p>
              {{
                store.weatherLoading
                  ? '오늘의 데이트 날씨를 확인하고 있어요.'
                  : '코스 생성 시 다시 확인할게요.'
              }}
            </p>
          </div>
        </div>
      </BaseCard>

      <!-- Map Card -->
      <BaseCard class="map-card">
        <div class="map-row">
          <div>
            <span class="label">LIVE COURSE</span>
            <strong>현재 데이트 지도</strong>
          </div>
          <button class="small-btn" @click="triggerMapFit">전체보기</button>
        </div>
        <div class="map-container">
          <LeafletMap
            :coords="displayedCoords"
            :places="displayedPlaces"
            :images="hasCourseDraft ? store.course.images : []"
            static
          />
        </div>
      </BaseCard>

      <section v-if="!hasCourseDraft" class="planning-guide" aria-label="사이봇 코스 생성 과정">
        <div class="guide-copy">
          <span>HOW IT WORKS</span>
          <strong>둘의 취향이 코스가 되는 과정</strong>
          <p>간단한 선택만 하면 날씨와 이동 동선까지 사이봇이 정리해요.</p>
        </div>
        <div class="guide-steps">
          <div><b>01</b><span>취향 선택</span><small>분위기와 이동 방식</small></div>
          <div><b>02</b><span>AI 큐레이션</span><small>날씨·거리까지 반영</small></div>
          <div><b>03</b><span>함께 출발</span><small>마음에 들면 바로 시작</small></div>
        </div>
      </section>

      <!-- Course Summary Card -->
      <BaseCard v-if="hasCourseDraft" class="course-card">
        <div class="course-row">
          <div>
            <span class="label">AI 추천 코스</span>
            <h3>{{ store.course.title }}</h3>
          </div>
          <BaseBadge variant="time">{{ store.course.places.length }}곳 추천</BaseBadge>
        </div>
        <div class="stats">
          <span>📍 {{ store.course.places.length }}개 장소</span>
          <span>🤖 AI가 취향 반영</span>
          <span>✏️ 대화로 수정 가능</span>
        </div>
        <ol class="timeline">
          <li v-for="(place, idx) in store.course.places" :key="idx" :data-n="idx + 1">
            {{ place }}
          </li>
        </ol>
        <BaseButton
          v-if="store.activeCourse"
          class="current-course-btn"
          variant="secondary"
          full
          @click="router.push({ name: 'current' })"
        >
          현재 데이트 이어가기
        </BaseButton>
      </BaseCard>

      <BaseCard v-else class="empty-course-card">
        <div class="empty-course-icon">42</div>
        <div class="empty-course-copy">
          <span>READY FOR YOUR DATE</span>
          <h3>오늘의 둘만을 위한 코스를 시작해 볼까요?</h3>
          <p>약 1분이면 취향을 반영한 세 장소와 이동 순서를 준비해 드려요.</p>
        </div>
        <BaseButton variant="primary" full @click="startCourseSetup">
          사이봇과 코스 만들기 →
        </BaseButton>
      </BaseCard>

      <!-- Chatbox Card -->
      <BaseCard v-if="!store.activeCourse && hasCourseDraft" class="chatbox-card">
        <div class="bot-head">
          <div class="bot-avatar">42</div>
          <div>
            <strong>사이봇</strong>
            <p>대화로 코스를 바꿔드려요</p>
          </div>
        </div>
        <div ref="messagesContainer" class="messages">
          <div v-for="(msg, idx) in store.messages" :key="idx" :class="['msg', msg.role]">
            <p v-html="msg.content"></p>
          </div>
          <div v-if="store.chatLoading" class="msg bot pending-message" aria-live="polite">
            <p><i></i><i></i><i></i><span>사이봇이 코스를 다듬고 있어요</span></p>
          </div>
        </div>
        <div class="quick-options">
          <button :disabled="store.chatLoading" @click="handleQuickAction('CHANGE_CAFE')">
            ☕ 카페로 변경
          </button>
          <button :disabled="store.chatLoading" @click="handleQuickAction('ADD_NIGHT_VIEW')">
            🌙 야경 추가
          </button>
          <button :disabled="store.chatLoading" @click="handleQuickAction('REDUCE_ROUTE')">
            🚌 동선 줄이기
          </button>
          <button :disabled="store.chatLoading" @click="handleQuickAction('INCREASE_INDOOR')">
            ☂️ 실내 강화
          </button>
        </div>
        <div class="chat-input-row">
          <input
            v-model="chatInput"
            :disabled="store.chatLoading"
            placeholder="예: 마지막은 야경으로 바꿔줘"
            @keydown.enter="handleSend"
          />
          <button class="send-btn" :disabled="store.chatLoading" @click="handleSend">➤</button>
        </div>
      </BaseCard>

      <!-- Bottom padding spacer for fixed button -->
      <div class="spacer"></div>
    </div>

    <!-- Decide Fixed Bottom Panel -->
    <div v-if="!store.activeCourse && hasCourseDraft" class="decide-action-bar">
      <BaseButton variant="primary" full @click="confirmCourse"> 이 코스로 결정하기 💗 </BaseButton>
    </div>
    <!-- Fullscreen Map Modal -->
    <div
      v-if="showMapModal"
      class="overlay open map-modal-overlay"
      @click.self="showMapModal = false"
    >
      <div class="modal map-modal">
        <div class="modal-header">
          <h3>전체 데이트 코스</h3>
          <button class="close-x-btn" @click="showMapModal = false">&times;</button>
        </div>
        <div class="modal-map-container" style="margin-bottom: 0">
          <LeafletMap
            :coords="displayedCoords"
            :places="displayedPlaces"
            :images="hasCourseDraft ? store.course.images : []"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #fffaf7 0%, #fff7f9 58%, #f8f4ff 100%);
}

.profile-chip {
  padding: 8px 12px;
  border-radius: 14px;
  background: #ffe3e7;
  color: #d85169;
  font-size: 10px;
  font-weight: 800;
  border: 0;
  cursor: pointer;
  position: relative;
  z-index: 12;
}

.profile-wrapper {
  position: relative;
}

.profile-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 8px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 12;
  min-width: 100px;
}

.profile-menu button {
  padding: 12px 16px;
  font-size: 11px;
  font-weight: 700;
  text-align: center;
  background: transparent;
  border: none;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  color: #333;
}

.profile-menu button:last-child {
  border-bottom: none;
}

.profile-menu .logout-item {
  color: #d85169;
}

.menu-overlay {
  position: fixed;
  inset: 0;
  z-index: 11;
}

.weather-card {
  margin-top: 15px;
  padding: 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border: 1px solid rgba(245, 207, 171, 0.62);
  background:
    radial-gradient(circle at 90% 10%, rgba(255, 255, 255, 0.72), transparent 24%),
    linear-gradient(135deg, #fff1c9, #ffe1e8 68%, #eee6ff);
  box-shadow: 0 12px 26px rgba(110, 73, 82, 0.1);
}

.weather-left {
  display: flex;
  gap: 11px;
  align-items: center;
}

.emoji {
  font-size: 31px;
}

.weather-left strong {
  display: block;
  font-size: 15px;
}

.weather-left p {
  margin: 4px 0 0;
  color: var(--muted);
  font-size: 10px;
}

.festival-card {
  margin-top: 11px;
  padding: 13px 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border: 1px dashed #e5a7b4;
  background: #fff7fa;
}

.label {
  display: block;
  color: #e75d74;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.festival-card strong {
  font-size: 12px;
}

.festival-card p {
  margin: 4px 0 0;
  color: var(--muted);
  font-size: 10px;
}

.small-btn {
  min-height: 33px;
  padding: 0 10px;
  border-radius: 11px;
  background: #ffe4e9;
  color: #db536a;
  font-size: 9px;
  font-weight: 800;
  border: 0;
}

.map-card {
  margin-top: 11px;
  padding: 15px;
  border: 1px solid rgba(225, 218, 228, 0.8);
  box-shadow: 0 12px 26px rgba(88, 65, 77, 0.09);
}

.map-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.map-container {
  height: 190px;
  margin-top: 10px;
  position: relative;
  overflow: hidden;
  border-radius: 16px;
  background:
    linear-gradient(90deg, rgba(255, 255, 255, 0.55) 1px, transparent 1px),
    linear-gradient(rgba(255, 255, 255, 0.55) 1px, transparent 1px), #e3ece5;
  background-size: 28px 28px;
}

.map-container::before {
  content: '';
  position: absolute;
  width: 420px;
  height: 50px;
  left: -20px;
  top: 75px;
  border-top: 12px solid #b9dff0;
  border-bottom: 8px solid #b9dff0;
  border-radius: 50%;
  transform: rotate(-8deg);
}

.road {
  position: absolute;
  height: 5px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 9px;
}

.r1 {
  width: 300px;
  left: -30px;
  top: 45px;
  transform: rotate(17deg);
}

.r2 {
  width: 320px;
  left: 55px;
  top: 140px;
  transform: rotate(-17deg);
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
  border: 0;
  padding: 0;
}

.marker i {
  font-style: normal;
  transform: rotate(45deg);
}

.marker.fest {
  background: #8b78cf;
}

.marker.bounce {
  animation: bounce-marker 0.45s;
}

@keyframes bounce-marker {
  50% {
    transform: rotate(-45deg) translateY(-8px);
  }
}

.course-card {
  margin-top: 11px;
  padding: 14px;
}

.empty-course-card {
  position: relative;
  display: grid;
  grid-template-columns: 50px 1fr;
  gap: 13px;
  margin-top: 12px;
  padding: 17px;
  overflow: hidden;
  border: 1px solid rgba(244, 192, 207, 0.72);
  background:
    radial-gradient(circle at 95% 5%, rgba(255, 255, 255, 0.72), transparent 25%),
    linear-gradient(135deg, #fff0f4, #f2eaff);
  box-shadow: 0 14px 28px rgba(122, 78, 101, 0.12);
}

.empty-course-card h3 {
  margin: 3px 0 6px;
  font-size: 15px;
  line-height: 1.35;
}

.empty-course-card p {
  margin: 0;
  color: var(--muted);
  font-size: 10px;
  line-height: 1.55;
}

.empty-course-card :deep(.btn) {
  grid-column: 1 / -1;
  margin-top: 2px;
}

.empty-course-icon {
  width: 50px;
  height: 50px;
  display: grid;
  place-items: center;
  border-radius: 18px 18px 18px 6px;
  background: linear-gradient(145deg, var(--pink), #9d83db);
  box-shadow: 0 10px 20px rgba(210, 91, 132, 0.22);
  color: #fff;
  font-size: 16px;
  font-weight: 900;
}

.empty-course-copy > span {
  color: #c06078;
  font-size: 7px;
  font-weight: 900;
  letter-spacing: 0.12em;
}

.planning-guide {
  margin-top: 12px;
  padding: 16px;
  border: 1px solid rgba(228, 219, 238, 0.9);
  border-radius: 21px;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: 0 10px 24px rgba(88, 65, 77, 0.07);
}

.guide-copy > span {
  color: #aa7391;
  font-size: 7px;
  font-weight: 900;
  letter-spacing: 0.14em;
}

.guide-copy strong {
  display: block;
  margin-top: 3px;
  font-size: 14px;
  font-weight: 900;
}

.guide-copy p {
  margin: 4px 0 0;
  color: var(--muted);
  font-size: 9px;
  line-height: 1.5;
}

.guide-steps {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 7px;
  margin-top: 13px;
}

.guide-steps div {
  min-width: 0;
  padding: 11px 8px;
  border-radius: 14px;
  background: linear-gradient(145deg, #fff6f7, #f7f2ff);
  text-align: center;
}

.guide-steps b {
  display: block;
  color: #d6677e;
  font-size: 8px;
}

.guide-steps span {
  display: block;
  margin: 4px 0 3px;
  font-size: 10px;
  font-weight: 900;
}

.guide-steps small {
  display: block;
  overflow: hidden;
  color: var(--muted);
  font-size: 7px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.course-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.course-card h3 {
  margin: 3px 0 0;
  font-size: 15px;
}

.stats {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  margin: 11px 0;
  scrollbar-width: none;
}

.stats::-webkit-scrollbar {
  display: none;
}

.stats span {
  flex: none;
  padding: 7px 9px;
  border-radius: 11px;
  background: #f6f0ee;
  color: #746266;
  font-size: 9px;
  font-weight: 700;
}

.timeline {
  list-style: none;
  margin: 0;
  padding: 0;
}

.timeline li {
  position: relative;
  padding: 8px 0 8px 29px;
  font-size: 11px;
  font-weight: 800;
}

.timeline li::before {
  content: attr(data-n);
  position: absolute;
  left: 0;
  top: 5px;
  width: 21px;
  height: 21px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  background: var(--pink);
  color: #fff;
  font-size: 9px;
}

.current-course-btn {
  margin-top: 12px;
}

.chatbox-card {
  margin-top: 11px;
  padding: 13px;
}

.bot-head {
  display: flex;
  gap: 10px;
  align-items: center;
  padding-bottom: 11px;
  border-bottom: 1px solid var(--line);
}

.bot-avatar {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 15px 15px 15px 5px;
  background: var(--pink);
  color: #fff;
  font-size: 11px;
  font-weight: 900;
}

.bot-head p {
  margin: 4px 0 0;
  color: var(--muted);
  font-size: 10px;
}

.messages {
  min-height: 85px;
  max-height: 190px;
  overflow-y: auto;
  padding: 11px 0;
  scrollbar-width: none;
}

.messages::-webkit-scrollbar {
  display: none;
}

.msg {
  display: flex;
  margin: 7px 0;
}

.msg p {
  margin: 0;
  max-width: 84%;
  padding: 10px 11px;
  border-radius: 14px;
  font-size: 10px;
  line-height: 1.55;
  word-break: break-all;
}

.msg.bot p {
  background: #f5efed;
  border-bottom-left-radius: 4px;
}

.msg.user {
  justify-content: flex-end;
}

.msg.user p {
  background: var(--pink);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.pending-message p {
  display: flex;
  align-items: center;
  gap: 4px;
}

.pending-message i {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #d46b80;
  animation: typing-dot 1s ease-in-out infinite;
}

.pending-message i:nth-child(2) {
  animation-delay: 0.15s;
}

.pending-message i:nth-child(3) {
  animation-delay: 0.3s;
}

.pending-message span {
  margin-left: 4px;
  color: var(--muted);
  font-size: 8px;
}

@keyframes typing-dot {
  50% {
    opacity: 0.35;
    transform: translateY(-3px);
  }
}

.quick-options {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  padding-bottom: 9px;
  scrollbar-width: none;
}

.quick-options::-webkit-scrollbar {
  display: none;
}

.quick-options button {
  flex: none;
  padding: 8px 9px;
  border: 1px solid var(--line);
  border-radius: 11px;
  background: #fff;
  font-size: 9px;
  font-weight: 800;
}

.quick-options button:disabled,
.send-btn:disabled,
.chat-input-row input:disabled {
  cursor: not-allowed;
  opacity: 0.52;
}

.chat-input-row {
  display: flex;
  gap: 7px;
}

.chat-input-row input {
  flex: 1;
  height: 42px;
  border: 1px solid var(--line);
  border-radius: 13px;
  padding: 0 11px;
  outline: 0;
  background: #fffdfa;
  color: var(--ink);
}

.send-btn {
  width: 42px;
  height: 42px;
  border-radius: 13px;
  background: var(--pink);
  color: #fff;
  display: grid;
  place-items: center;
}

.spacer {
  height: 68px;
}

.decide-action-bar {
  position: absolute;
  z-index: 20;
  left: 0;
  right: 0;
  bottom: 76px;
  padding: 10px 15px 13px;
  background: linear-gradient(transparent, rgba(255, 250, 245, 0.97) 38%);
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
