<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useDateStore } from '@/stores/dateStore'
import BaseButton from './BaseButton.vue'
import type { District, SpaceType, TimeSlot } from '@/types/api/course'

const store = useDateStore()
const router = useRouter()

const currentStepData = computed(() => store.surveyStepsList[store.surveyStep]!)
const answersForKey = computed(() =>
  currentStepData.value.key ? store.surveyAnswers[currentStepData.value.key] : [],
)
const progressWidth = computed(
  () => `${((store.surveyStep + 1) / store.surveyStepsList.length) * 100}%`,
)
const timeOptions: Array<{ value: TimeSlot; emoji: string; label: string; time: string }> = [
  { value: 'MORNING', emoji: '🌤️', label: '오전', time: '09:00부터' },
  { value: 'AFTERNOON', emoji: '☀️', label: '오후', time: '14:00부터' },
  { value: 'FULL_DAY', emoji: '💞', label: '종일', time: '10:00부터' },
]
const districtOptions: Array<{ value: District; label: string }> = [
  { value: 'DONG_GU', label: '동구' },
  { value: 'JUNG_GU', label: '중구' },
  { value: 'SEO_GU', label: '서구' },
  { value: 'YUSEONG_GU', label: '유성구' },
  { value: 'DAEDEOK_GU', label: '대덕구' },
  { value: 'ANY', label: '대전 어디든' },
]
const spaceOptions: Array<{ value: SpaceType; emoji: string; label: string }> = [
  { value: 'ANY', emoji: '✨', label: '상관없어요' },
  { value: 'INDOOR', emoji: '🏠', label: '실내 중심' },
  { value: 'OUTDOOR', emoji: '🌳', label: '실외 중심' },
]

async function handleNextSurveyStep() {
  await store.nextSurveyStep()
  if (!store.showSurvey && store.surveyDone) await router.push({ name: 'chat' })
}
</script>

<template>
  <div v-if="store.showSurvey" class="overlay open">
    <div class="sheet">
      <div class="sheet-notch">
        <div class="handle"></div>
        <button class="close-btn" type="button" aria-label="설문 닫기" @click="store.closeSurvey">
          &times;
        </button>
      </div>
      <div class="surveyhead">
        <span>{{ store.surveyStep + 1 }} / {{ store.surveyStepsList.length }}</span>
        <div class="surveybar">
          <i :style="{ width: progressWidth }"></i>
        </div>
      </div>
      <div class="survey-content">
        <div class="q">
          <b>{{ currentStepData.emoji }}</b>
          <h3>{{ currentStepData.title }}</h3>
          <p>{{ currentStepData.desc }}</p>
        </div>
        <div v-if="store.loading" class="ai-loading" aria-live="polite">
          <div class="orbit"><span>💞</span><i>✨</i><b>🌷</b></div>
          <strong>42봇이 두 분의 코스를 고르는 중이에요</strong>
          <p>날씨와 취향, 이동 동선을 살펴보고 있어요.</p>
        </div>
        <div v-else-if="currentStepData.kind === 'datetime'" class="schedule-options">
          <div class="today-chip">
            <span>데이트 날짜</span>
            <strong>{{ store.courseDate }}</strong>
            <small>오늘 날짜로 코스를 만들어요</small>
          </div>
          <div class="choice-label">시간대</div>
          <div class="time-options">
            <button
              v-for="option in timeOptions"
              :key="option.value"
              type="button"
              :class="{ selected: store.timeSlot === option.value }"
              @click="store.selectTimeSlot(option.value)"
            >
              <b>{{ option.emoji }}</b>
              <strong>{{ option.label }}</strong>
              <small>{{ option.time }}</small>
            </button>
          </div>
        </div>
        <div v-else-if="currentStepData.kind === 'location'" class="location-options">
          <div class="choice-label">데이트 지역</div>
          <div class="district-options">
            <button
              v-for="option in districtOptions"
              :key="option.value"
              type="button"
              :class="{ selected: store.district === option.value }"
              @click="store.district = option.value"
            >
              {{ option.label }}
            </button>
          </div>
          <div class="choice-label space-label">공간 선호</div>
          <div class="space-options">
            <button
              v-for="option in spaceOptions"
              :key="option.value"
              type="button"
              :class="{ selected: store.spaceType === option.value }"
              @click="store.spaceType = option.value"
            >
              <span>{{ option.emoji }}</span
              >{{ option.label }}
            </button>
          </div>
        </div>
        <div v-else class="opts">
          <button
            v-for="opt in currentStepData.opts ?? []"
            :key="opt"
            :class="{ selected: answersForKey.includes(opt) }"
            @click="currentStepData.key && store.toggleSurveyOption(currentStepData.key, opt)"
          >
            {{ opt }}
          </button>
        </div>
      </div>
      <div class="sheetacts">
        <BaseButton
          variant="secondary"
          :style="{ visibility: store.surveyStep > 0 ? 'visible' : 'hidden' }"
          @click="store.prevSurveyStep"
        >
          이전
        </BaseButton>
        <BaseButton variant="primary" :disabled="store.loading" @click="handleNextSurveyStep">
          {{
            store.surveyStep === store.surveyStepsList.length - 1
              ? store.loading
                ? 'AI 코스를 만드는 중…'
                : '완료하고 AI 코스 만들기'
              : '다음'
          }}
        </BaseButton>
      </div>
    </div>
  </div>
</template>

<style scoped>
.overlay {
  position: absolute;
  z-index: 100;
  inset: 0;
  display: flex;
  align-items: flex-end;
  padding: 14px;
  background: rgba(53, 42, 45, 0.45);
  backdrop-filter: blur(3px);
}

.sheet {
  width: 100%;
  background: #fff;
  box-shadow: var(--shadow);
  padding: 11px 17px 19px;
  border-radius: 27px;
}

.sheet-notch {
  position: relative;
}

.handle {
  width: 45px;
  height: 5px;
  margin: 0 auto 13px;
  background: #e6dad7;
  border-radius: 6px;
}

.close-btn {
  position: absolute;
  top: -7px;
  right: -4px;
  width: 28px;
  height: 28px;
  border: 0;
  border-radius: 10px;
  background: #f6efed;
  color: var(--muted);
  font-size: 21px;
  line-height: 1;
}

.surveyhead {
  display: flex;
  gap: 10px;
  align-items: center;
  color: var(--muted);
  font-size: 9px;
  font-weight: 800;
}

.surveybar {
  flex: 1;
  height: 6px;
  border-radius: 7px;
  background: #f0e7e5;
  overflow: hidden;
}

.surveybar i {
  display: block;
  height: 100%;
  background: var(--pink);
  transition: width 0.2s ease-in-out;
}

.q {
  padding: 20px 0 13px;
}

.q b {
  display: block;
  font-size: 32px;
}

.q h3 {
  margin: 8px 0 5px;
  font-size: 16px;
}

.q p {
  margin: 0;
  color: var(--muted);
  font-size: 10px;
  line-height: 1.5;
}

.opts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.form-options {
  display: grid;
  gap: 10px;
}

.schedule-options,
.location-options {
  display: grid;
}

.today-chip {
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: center;
  gap: 3px 10px;
  padding: 13px 14px;
  border: 1px solid #f1dce1;
  border-radius: 15px;
  background: linear-gradient(135deg, #fff4f6, #f7f2ff);
}

.today-chip span,
.choice-label {
  color: #a66f7c;
  font-size: 9px;
  font-weight: 900;
}

.today-chip strong {
  grid-row: 1 / 3;
  grid-column: 2;
  color: #d45d75;
  font-size: 12px;
}

.today-chip small {
  color: var(--muted);
  font-size: 8px;
}

.choice-label {
  margin: 12px 2px 7px;
}

.time-options,
.space-options {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 7px;
}

.time-options button {
  min-height: 82px;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 3px;
  border: 1px solid var(--line);
  border-radius: 16px;
  background: #fffdfa;
}

.time-options button b {
  font-size: 21px;
}

.time-options button strong {
  font-size: 11px;
}

.time-options button small {
  color: var(--muted);
  font-size: 7px;
}

.district-options {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 7px;
}

.district-options button,
.space-options button {
  min-height: 42px;
  padding: 8px 5px;
  border: 1px solid var(--line);
  border-radius: 13px;
  background: #fffdfa;
  color: var(--ink);
  font-size: 9px;
  font-weight: 800;
}

.space-options button {
  display: grid;
  gap: 3px;
}

.space-options button span {
  font-size: 16px;
}

.time-options button.selected,
.district-options button.selected,
.space-options button.selected {
  border-color: var(--pink);
  background: linear-gradient(145deg, #fff0f3, #f5efff);
  box-shadow: 0 7px 14px rgba(216, 91, 120, 0.12);
  color: #d6536b;
}

.ai-loading {
  min-height: 174px;
  display: grid;
  justify-items: center;
  align-content: center;
  text-align: center;
}

.ai-loading strong {
  font-size: 13px;
}
.ai-loading p {
  margin: 6px 0 0;
  color: var(--muted);
  font-size: 10px;
}

.orbit {
  position: relative;
  width: 76px;
  height: 66px;
  margin-bottom: 13px;
  animation: float 1.5s ease-in-out infinite;
}

.orbit span {
  position: absolute;
  inset: 15px 0 auto;
  font-size: 35px;
}
.orbit i,
.orbit b {
  position: absolute;
  font-style: normal;
  font-size: 17px;
  animation: twinkle 0.9s ease-in-out infinite alternate;
}
.orbit i {
  top: 0;
  right: 3px;
}
.orbit b {
  bottom: 0;
  left: 2px;
  animation-delay: 0.35s;
}

@keyframes float {
  50% {
    transform: translateY(-6px) rotate(2deg);
  }
}
@keyframes twinkle {
  to {
    transform: scale(1.35) rotate(15deg);
    opacity: 0.55;
  }
}

.form-options label {
  display: grid;
  gap: 6px;
  color: var(--muted);
  font-size: 10px;
  font-weight: 800;
}

.form-options input,
.form-options select {
  width: 100%;
  min-height: 44px;
  padding: 0 11px;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: #fffdfa;
  color: var(--ink);
  font: inherit;
}

.opts button {
  min-height: 59px;
  padding: 9px;
  border: 1px solid var(--line);
  border-radius: 15px;
  background: #fffdfa;
  color: var(--ink);
  font-size: 10px;
  font-weight: 800;
  transition: all 0.2s;
  text-align: center;
}

.opts button.selected {
  border-color: var(--pink);
  background: #fff0f3;
  color: #dc536a;
}

.sheetacts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-top: 15px;
}
</style>
