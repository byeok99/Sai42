<script setup lang="ts">
import { computed } from 'vue'
import { useDateStore } from '@/stores/dateStore'
import BaseButton from './BaseButton.vue'

const store = useDateStore()

const currentStepData = computed(() => store.surveyStepsList[store.surveyStep]!)
const answersForKey = computed(() => store.surveyAnswers[currentStepData.value.key])
const progressWidth = computed(() => `${(store.surveyStep + 1) * 33.33}%`)
</script>

<template>
  <div v-if="store.showSurvey" class="overlay open">
    <div class="sheet">
      <div class="handle"></div>
      <div class="surveyhead">
        <span>{{ store.surveyStep + 1 }} / 3</span>
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
        <div class="opts">
          <button
            v-for="opt in currentStepData.opts"
            :key="opt"
            :class="{ selected: answersForKey.includes(opt) }"
            @click="store.toggleSurveyOption(currentStepData.key, opt)"
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
        <BaseButton variant="primary" @click="store.nextSurveyStep">
          {{ store.surveyStep === 2 ? '취향 저장' : '다음' }}
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
