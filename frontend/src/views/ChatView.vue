<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useDateStore } from '@/stores/dateStore'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseBadge from '@/components/common/BaseBadge.vue'

const store = useDateStore()
const router = useRouter()

const chatInput = ref('')
const messagesContainer = ref<HTMLDivElement | null>(null)
const bouncedMarker = ref<number | null>(null)

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

function handleSend() {
  if (!chatInput.value.trim()) return
  store.sendChatMessage(chatInput.value)
  chatInput.value = ''
  scrollToBottom()
}

function handleQuickAction(text: string) {
  store.sendChatMessage(text)
  scrollToBottom()
}

function clickMarker(idx: number, title: string) {
  bouncedMarker.value = idx
  setTimeout(() => {
    bouncedMarker.value = null
  }, 500)
  store.triggerToast(title)
}

function triggerMapFit() {
  store.course.coords.forEach((_, idx) => {
    setTimeout(() => {
      clickMarker(idx, store.course.places[idx] || '')
    }, idx * 80)
  })
  store.triggerToast('전체 코스를 한눈에 보여드릴게요')
}

function confirmCourse() {
  store.decideCourse()
  router.push({ name: 'current' })
}

onMounted(() => {
  scrollToBottom()
})
</script>

<template>
  <div class="chat-view">
    <header class="top-bar">
      <div>
        <p class="section-label">AI DATE MAKER</p>
        <h2>사이봇과 코스 만들기</h2>
      </div>
      <button class="profile-chip" @click="store.showSurvey = true">
        💞 {{ store.name || '우리 취향' }}
      </button>
    </header>

    <div class="scroll-area">
      <!-- Weather Card -->
      <BaseCard class="weather-card">
        <div class="weather-left">
          <span class="emoji">🌦️</span>
          <div>
            <strong>대전 23°C</strong>
            <p>오후 4시부터 약한 비</p>
          </div>
        </div>
        <BaseBadge variant="default">실내 70%</BaseBadge>
      </BaseCard>

      <!-- Festival Card -->
      <BaseCard class="festival-card">
        <div>
          <span class="label">오늘의 축제</span>
          <strong>유성온천문화축제</strong>
          <p>유림공원 일원 · 18:00 야간 프로그램</p>
        </div>
        <button class="small-btn" @click="store.addFestivalToCourse">코스에 넣기</button>
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
          <span class="road r1"></span>
          <span class="road r2"></span>
          <div class="markers-wrapper">
            <button
              v-for="(coord, idx) in store.course.coords"
              :key="idx"
              :class="['marker', { bounce: bouncedMarker === idx }]"
              :style="{ left: `${coord[0]}%`, top: `${coord[1]}%` }"
              @click="clickMarker(idx, store.course.places[idx] || '')"
            >
              <i>{{ idx + 1 }}</i>
            </button>
            <button
              v-if="store.course.fest"
              class="marker fest"
              style="left: 39%; top: 32%"
              @click="store.triggerToast('유성온천문화축제')"
            >
              <i>F</i>
            </button>
          </div>
        </div>
      </BaseCard>

      <!-- Course Summary Card -->
      <BaseCard class="course-card">
        <div class="course-row">
          <div>
            <span class="label">AI가 조정 중</span>
            <h3>{{ store.course.title }}</h3>
          </div>
          <BaseBadge variant="time">4시간</BaseBadge>
        </div>
        <div class="stats">
          <span>💗 설렘 4.6</span>
          <span>👟 체력 2</span>
          <span>☂️ 비 생존력 5</span>
        </div>
        <ol class="timeline">
          <li v-for="(place, idx) in store.course.places" :key="idx" :data-n="idx + 1">
            {{ place }}
          </li>
        </ol>
      </BaseCard>

      <!-- Chatbox Card -->
      <BaseCard class="chatbox-card">
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
        </div>
        <div class="quick-options">
          <button @click="handleQuickAction('두 번째 장소를 카페로 바꿔줘')">☕ 카페로 변경</button>
          <button @click="handleQuickAction('야경 장소를 추가해줘')">🌙 야경 추가</button>
          <button @click="handleQuickAction('이동 거리를 줄여줘')">🚌 동선 줄이기</button>
          <button @click="handleQuickAction('비가 와도 괜찮게 바꿔줘')">☂️ 실내 강화</button>
        </div>
        <div class="chat-input-row">
          <input
            v-model="chatInput"
            placeholder="예: 마지막은 야경으로 바꿔줘"
            @keydown.enter="handleSend"
          />
          <button class="send-btn" @click="handleSend">➤</button>
        </div>
      </BaseCard>

      <!-- Bottom padding spacer for fixed button -->
      <div class="spacer"></div>
    </div>

    <!-- Decide Fixed Bottom Panel -->
    <div class="decide-action-bar">
      <BaseButton variant="primary" full @click="confirmCourse"> 이 코스로 결정하기 💗 </BaseButton>
    </div>
  </div>
</template>

<style scoped>
.chat-view {
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

.profile-chip {
  padding: 9px 11px;
  border-radius: 14px;
  background: #fff;
  box-shadow: var(--shadow);
  font-size: 11px;
  font-weight: 800;
  border: 0;
  color: var(--ink);
  cursor: pointer;
}

.weather-card {
  margin-top: 15px;
  padding: 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #fff0be, #ffe0e5);
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
  padding: 13px;
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
  bottom: 74px;
  padding: 10px 15px 13px;
  background: linear-gradient(transparent, rgba(255, 250, 245, 0.97) 38%);
}
</style>
