<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
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
const calendarYear = ref(0)
const calendarMonth = ref(0)
const availabilityTick = ref(Date.now())
let availabilityTimer: number | null = null

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
const weekdays = ['일', '월', '화', '수', '목', '금', '토']

const calendarMonthLabel = computed(() => `${calendarYear.value}년 ${calendarMonth.value}월`)
const minimumMonth = computed(() => store.minimumCourseDate.slice(0, 7))
const currentCalendarMonth = computed(
  () => `${calendarYear.value}-${String(calendarMonth.value).padStart(2, '0')}`,
)
const canMoveToPreviousMonth = computed(() => currentCalendarMonth.value > minimumMonth.value)
const selectedDateLabel = computed(() => {
  const [year, month, day] = store.courseDate.split('-').map(Number)
  if (!year || !month || !day) return '날짜를 선택해 주세요'
  const weekday = new Intl.DateTimeFormat('ko-KR', {
    timeZone: 'Asia/Seoul',
    weekday: 'short',
  }).format(new Date(Date.UTC(year, month - 1, day)))
  return `${month}월 ${day}일 ${weekday}요일`
})
const calendarDays = computed(() => {
  const firstDay = new Date(Date.UTC(calendarYear.value, calendarMonth.value - 1, 1))
  const startOffset = firstDay.getUTCDay()
  const previousMonthDays = new Date(
    Date.UTC(calendarYear.value, calendarMonth.value - 1, 0),
  ).getUTCDate()
  const daysInMonth = new Date(Date.UTC(calendarYear.value, calendarMonth.value, 0)).getUTCDate()

  return Array.from({ length: 42 }, (_, index) => {
    const relativeDay = index - startOffset + 1
    const inCurrentMonth = relativeDay >= 1 && relativeDay <= daysInMonth
    const day =
      relativeDay < 1
        ? previousMonthDays + relativeDay
        : relativeDay > daysInMonth
          ? relativeDay - daysInMonth
          : relativeDay
    const target = new Date(Date.UTC(calendarYear.value, calendarMonth.value - 1, relativeDay))
    const date = target.toISOString().slice(0, 10)
    return {
      date,
      day,
      inCurrentMonth,
      disabled: !inCurrentMonth || date < store.minimumCourseDate,
    }
  })
})
const noAvailableTimeSlots = computed(() => {
  return (
    availabilityTick.value > 0 &&
    timeOptions.every((option) => store.isTimeSlotUnavailable(option.value))
  )
})

function syncCalendarMonth(date: string) {
  const [year, month] = date.split('-').map(Number)
  if (!year || !month) return
  calendarYear.value = year
  calendarMonth.value = month
}

function changeCalendarMonth(offset: number) {
  const target = new Date(Date.UTC(calendarYear.value, calendarMonth.value - 1 + offset, 1))
  const targetMonth = `${target.getUTCFullYear()}-${String(target.getUTCMonth() + 1).padStart(2, '0')}`
  if (targetMonth < minimumMonth.value) return
  calendarYear.value = target.getUTCFullYear()
  calendarMonth.value = target.getUTCMonth() + 1
}

function selectCalendarDate(date: string, disabled: boolean) {
  if (!disabled) store.selectCourseDate(date)
}

function isTimeOptionDisabled(value: TimeSlot) {
  return availabilityTick.value > 0 && store.isTimeSlotUnavailable(value)
}

function stopAvailabilityClock() {
  if (availabilityTimer !== null) {
    window.clearInterval(availabilityTimer)
    availabilityTimer = null
  }
}

function refreshAvailability() {
  availabilityTick.value = Date.now()
  store.refreshServerDateBoundaries()
  if (store.courseDate < store.minimumCourseDate) {
    store.selectCourseDate(store.minimumCourseDate)
  } else {
    store.selectCourseDate(store.courseDate)
  }
}

watch(
  () => store.showSurvey,
  (isOpen) => {
    stopAvailabilityClock()
    if (!isOpen) return
    refreshAvailability()
    syncCalendarMonth(store.courseDate)
    availabilityTimer = window.setInterval(refreshAvailability, 30_000)
  },
  { immediate: true },
)
watch(
  () => store.courseDate,
  (date) => syncCalendarMonth(date),
)
onUnmounted(stopAvailabilityClock)

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
          <div class="date-picker-card">
            <div class="calendar-head">
              <button
                type="button"
                aria-label="이전 달"
                :disabled="!canMoveToPreviousMonth"
                @click="changeCalendarMonth(-1)"
              >
                ‹
              </button>
              <div>
                <span>DATE CALENDAR</span>
                <strong>{{ calendarMonthLabel }}</strong>
              </div>
              <button type="button" aria-label="다음 달" @click="changeCalendarMonth(1)">›</button>
            </div>
            <div class="calendar-weekdays" aria-hidden="true">
              <span v-for="weekday in weekdays" :key="weekday">{{ weekday }}</span>
            </div>
            <div class="calendar-days">
              <button
                v-for="day in calendarDays"
                :key="day.date"
                type="button"
                :disabled="day.disabled"
                :class="{
                  outside: !day.inCurrentMonth,
                  today: day.date === store.minimumCourseDate,
                  selected: day.date === store.courseDate,
                }"
                :aria-label="`${day.date}${day.disabled ? ' 선택 불가' : ' 선택'}`"
                @click="selectCalendarDate(day.date, day.disabled)"
              >
                <span>{{ day.day }}</span>
                <small v-if="day.date === store.minimumCourseDate">오늘</small>
              </button>
            </div>
          </div>
          <div class="selected-date-summary">
            <span>선택한 데이트</span>
            <strong>{{ selectedDateLabel }}</strong>
            <small>{{ store.courseDate }}</small>
          </div>
          <div class="choice-label">시간대</div>
          <div class="time-options">
            <button
              v-for="option in timeOptions"
              :key="option.value"
              type="button"
              :disabled="isTimeOptionDisabled(option.value)"
              :class="{
                selected: store.timeSlot === option.value,
                expired: isTimeOptionDisabled(option.value),
              }"
              @click="store.selectTimeSlot(option.value)"
            >
              <b>{{ option.emoji }}</b>
              <strong>{{ option.label }}</strong>
              <small>{{ isTimeOptionDisabled(option.value) ? '선택 마감' : option.time }}</small>
            </button>
          </div>
          <p v-if="store.courseDate === store.minimumCourseDate" class="server-time-guide">
            <span>SERVER TIME</span>
            오늘은 서버 기준으로 이미 시작된 시간대를 선택할 수 없어요.
          </p>
          <p v-if="noAvailableTimeSlots" class="slot-unavailable-guide">
            오늘 선택 가능한 시간대가 없어요. 내일 이후 날짜를 선택해 주세요.
          </p>
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
  max-height: calc(100% - 18px);
  overflow-y: auto;
  background: #fff;
  box-shadow: var(--shadow);
  padding: 11px 17px 19px;
  border-radius: 27px;
  scrollbar-width: none;
}

.sheet::-webkit-scrollbar {
  display: none;
}

.sheet-notch {
  position: relative;
  min-height: 40px;
}

.handle {
  width: 45px;
  height: 5px;
  margin: 0 auto;
  background: #e6dad7;
  border-radius: 6px;
}

.close-btn {
  position: absolute;
  top: 1px;
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

.date-picker-card {
  padding: 14px 13px 12px;
  border: 1px solid #f0dce2;
  border-radius: 20px;
  background:
    radial-gradient(circle at 100% 0%, rgba(236, 218, 255, 0.68), transparent 38%),
    linear-gradient(145deg, #fff8f9 0%, #fff 55%, #fff5f8 100%);
  box-shadow: 0 12px 28px rgba(168, 91, 112, 0.08);
}

.calendar-head {
  display: grid;
  grid-template-columns: 34px 1fr 34px;
  align-items: center;
  margin-bottom: 13px;
}

.calendar-head > div {
  display: grid;
  justify-items: center;
  gap: 2px;
}

.calendar-head span {
  color: #b88794;
  font-size: 7px;
  font-weight: 900;
  letter-spacing: 0.16em;
}

.calendar-head strong {
  color: #4d3d43;
  font-size: 13px;
}

.calendar-head button {
  width: 30px;
  height: 30px;
  border: 1px solid #f0dce2;
  border-radius: 11px;
  background: rgba(255, 255, 255, 0.82);
  color: #c9697e;
  font-size: 20px;
  line-height: 1;
}

.calendar-head button:disabled {
  border-color: #f2ecee;
  background: rgba(249, 246, 247, 0.7);
  color: #d9ced1;
}

.calendar-weekdays,
.calendar-days {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
}

.calendar-weekdays {
  margin-bottom: 4px;
}

.calendar-weekdays span {
  color: #a99ca0;
  font-size: 8px;
  font-weight: 800;
  text-align: center;
}

.calendar-weekdays span:first-child {
  color: #d78394;
}

.calendar-days {
  gap: 2px 1px;
}

.calendar-days button {
  position: relative;
  min-width: 0;
  height: 34px;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 0;
  border: 0;
  border-radius: 11px;
  background: transparent;
  color: #55474c;
  font-size: 9px;
  font-weight: 800;
}

.calendar-days button:nth-child(7n + 1):not(.selected) {
  color: #d4798c;
}

.calendar-days button:hover:not(:disabled):not(.selected) {
  background: #fff0f4;
}

.calendar-days button.today:not(.selected) {
  box-shadow: inset 0 0 0 1px #edb1bf;
}

.calendar-days button.selected {
  background: linear-gradient(145deg, #ec7890, #d95f7c);
  box-shadow: 0 7px 14px rgba(216, 91, 120, 0.24);
  color: #fff;
}

.calendar-days button:disabled {
  color: #d9d1d3;
  cursor: not-allowed;
}

.calendar-days button.outside {
  opacity: 0.24;
}

.calendar-days button small {
  font-size: 5px;
  font-weight: 800;
  line-height: 1;
}

.selected-date-summary {
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: center;
  gap: 2px 10px;
  margin-top: 8px;
  padding: 10px 12px;
  border-radius: 13px;
  background: #f9f3f5;
}

.selected-date-summary span,
.choice-label {
  color: #a66f7c;
  font-size: 9px;
  font-weight: 900;
}

.selected-date-summary strong {
  grid-row: 1 / 3;
  grid-column: 2;
  color: #c95670;
  font-size: 11px;
}

.selected-date-summary small {
  color: var(--muted);
  font-size: 7px;
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

.time-options button:disabled {
  border-color: #eee7e8;
  background: #f7f4f4;
  box-shadow: none;
  color: #bdb4b6;
  cursor: not-allowed;
}

.time-options button:disabled b {
  filter: grayscale(1);
  opacity: 0.44;
}

.time-options button:disabled small {
  color: #c4babc;
}

.server-time-guide,
.slot-unavailable-guide {
  margin: 8px 2px 0;
  padding: 0 2px;
  color: #8d7d82;
  font-size: 8px;
  line-height: 1.55;
}

.server-time-guide span {
  margin-right: 4px;
  color: #cc657c;
  font-size: 6px;
  font-weight: 900;
  letter-spacing: 0.08em;
}

.slot-unavailable-guide {
  padding: 8px 10px;
  border: 1px solid #f3dce2;
  border-radius: 10px;
  background: #fff4f6;
  color: #bd596f;
  font-weight: 800;
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
