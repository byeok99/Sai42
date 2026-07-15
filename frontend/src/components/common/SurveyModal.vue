<script setup lang="ts">
import { computed } from 'vue'
import { useDateStore } from '@/stores/dateStore'
import BaseButton from './BaseButton.vue'

const store = useDateStore()

const currentStepData = computed(() => store.surveyStepsList[store.surveyStep]!)
const answersForKey = computed(() =>
  currentStepData.value.key ? store.surveyAnswers[currentStepData.value.key] : [],
)
const progressWidth = computed(
  () => `${((store.surveyStep + 1) / store.surveyStepsList.length) * 100}%`,
)
</script>

<template>
  <div v-if="store.showSurvey" class="overlay open">
    <div class="sheet">
      <div class="handle"></div>
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
          <strong>사이봇이 두 분의 코스를 고르는 중이에요</strong>
          <p>날씨와 취향, 이동 동선을 살펴보고 있어요.</p>
        </div>
        <div v-else-if="currentStepData.kind === 'datetime'" class="form-options">
          <label>
            날짜
            <input v-model="store.courseDate" type="date" :min="store.minimumCourseDate" />
          </label>
          <label>
            시작 시각
            <input v-model="store.startTime" type="time" min="19:00" />
          </label>
        </div>
        <div v-else-if="currentStepData.kind === 'location'" class="form-options">
          <label>
            지역
            <select v-model="store.district">
              <option value="DONG_GU">동구</option>
              <option value="JUNG_GU">중구</option>
              <option value="SEO_GU">서구</option>
              <option value="YUSEONG_GU">유성구</option>
              <option value="DAEDEOK_GU">대덕구</option>
              <option value="ANY">대전 어디든</option>
            </select>
          </label>
          <label>
            공간 선호
            <select v-model="store.spaceType">
              <option value="ANY">상관없어요</option>
              <option value="INDOOR">실내 중심</option>
              <option value="OUTDOOR">실외 중심</option>
            </select>
          </label>
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
        <BaseButton variant="primary" :disabled="store.loading" @click="store.nextSurveyStep">
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

.handle {
  width: 45px;
  height: 5px;
  margin: 0 auto 13px;
  background: #e6dad7;
  border-radius: 6px;
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
