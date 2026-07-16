<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'

const emit = defineEmits<{
  close: []
}>()

const firstInput = ref<HTMLInputElement | null>(null)
const firstName = ref('')
const secondName = ref('')
const rotation = ref(0)
const spinning = ref(false)
const winner = ref('')
let resultTimer: number | null = null

const names = computed(() => [firstName.value.trim(), secondName.value.trim()])
const wheelNames = computed(() =>
  Array.from({ length: 8 }, (_, index) => names.value[index % names.value.length] || '?'),
)
const labelRotation = computed(() => ((rotation.value % 360) + 360) % 360)
const canSpin = computed(() => names.value.every(Boolean) && !spinning.value)

function spinRoulette() {
  if (!canSpin.value) return

  winner.value = ''
  spinning.value = true
  const selectedIndex = Math.floor(Math.random() * wheelNames.value.length)
  const currentAngle = ((rotation.value % 360) + 360) % 360
  const targetAngle = (360 - selectedIndex * 45) % 360
  rotation.value += 5 * 360 + ((targetAngle - currentAngle + 360) % 360)

  resultTimer = window.setTimeout(() => {
    winner.value = wheelNames.value[selectedIndex] ?? ''
    spinning.value = false
    resultTimer = null
  }, 3200)
}

function requestClose() {
  if (!spinning.value) emit('close')
}

watch(names, () => {
  if (!spinning.value) winner.value = ''
})

onMounted(() => {
  void nextTick(() => firstInput.value?.focus())
})

onUnmounted(() => {
  if (resultTimer !== null) window.clearTimeout(resultTimer)
})
</script>

<template>
  <div class="roulette-overlay" @click.self="requestClose" @keydown.esc="requestClose">
    <section
      class="roulette-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="roulette-title"
    >
      <header class="roulette-modal-head">
        <div>
          <span>COUPLE MINI GAME</span>
          <h3 id="roulette-title">오늘은 누가 정할까요?</h3>
          <p>두 사람의 이름을 넣고 룰렛에게 선택을 맡겨보세요.</p>
        </div>
        <button type="button" :disabled="spinning" aria-label="룰렛 닫기" @click="requestClose">
          &times;
        </button>
      </header>

      <div class="name-fields">
        <label>
          <span>PLAYER 01</span>
          <input ref="firstInput" v-model="firstName" maxlength="8" placeholder="첫 번째 이름" />
        </label>
        <div class="name-heart" aria-hidden="true">♥</div>
        <label>
          <span>PLAYER 02</span>
          <input v-model="secondName" maxlength="8" placeholder="두 번째 이름" />
        </label>
      </div>

      <div class="roulette-stage" aria-label="커플 이름 룰렛">
        <div class="roulette-pointer" aria-hidden="true"></div>
        <div class="roulette-rim">
          <div class="roulette-wheel" :style="{ transform: `rotate(${rotation}deg)` }">
            <span
              v-for="(name, index) in wheelNames"
              :key="index"
              :style="{
                transform: `rotate(${index * 45}deg) translateY(-91px) rotate(${-index * 45 - labelRotation}deg)`,
              }"
            >
              {{ name }}
            </span>
          </div>
          <div class="roulette-cap"><b>42</b><small>PLAY</small></div>
        </div>
      </div>

      <div :class="['roulette-result', { visible: winner }]" aria-live="polite">
        <template v-if="winner">
          <span>오늘의 선택</span>
          <strong>{{ winner }}</strong>
          <p>결정 완료! 이제 즐겁게 데이트할 차례예요.</p>
        </template>
        <template v-else>
          <span>{{ spinning ? '룰렛이 선택하고 있어요' : '두 이름을 입력해 주세요' }}</span>
          <strong>{{ spinning ? '두근두근…' : 'WHO IS NEXT?' }}</strong>
        </template>
      </div>

      <button class="spin-button" type="button" :disabled="!canSpin" @click="spinRoulette">
        <span aria-hidden="true">↻</span>
        {{ spinning ? '룰렛 돌리는 중…' : winner ? '한 번 더 돌리기' : '룰렛 돌리기' }}
      </button>
      <small class="local-note">입력한 이름과 결과는 저장되지 않아요.</small>
    </section>
  </div>
</template>

<style scoped>
.roulette-overlay {
  position: absolute;
  z-index: 130;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  background: rgba(54, 41, 47, 0.52);
  backdrop-filter: blur(5px);
}

.roulette-modal {
  width: 100%;
  max-width: 410px;
  max-height: calc(100% - 16px);
  overflow-y: auto;
  padding: 20px;
  border: 1px solid rgba(255, 255, 255, 0.78);
  border-radius: 27px;
  background:
    radial-gradient(circle at 100% 0%, rgba(227, 215, 255, 0.78), transparent 28%),
    linear-gradient(160deg, #fffaf8, #fff 55%, #fff4f7);
  box-shadow: 0 26px 70px rgba(58, 37, 46, 0.3);
  scrollbar-width: none;
}

.roulette-modal::-webkit-scrollbar {
  display: none;
}

.roulette-modal-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.roulette-modal-head span {
  color: #c75e77;
  font-size: 7px;
  font-weight: 900;
  letter-spacing: 0.16em;
}

.roulette-modal-head h3 {
  margin: 4px 0 5px;
  color: #4f3d43;
  font-size: 18px;
  letter-spacing: -0.04em;
}

.roulette-modal-head p {
  margin: 0;
  color: var(--muted);
  font-size: 9px;
  line-height: 1.5;
}

.roulette-modal-head button {
  width: 34px;
  height: 34px;
  display: grid;
  flex: none;
  place-items: center;
  border-radius: 12px;
  background: rgba(247, 238, 240, 0.92);
  color: #8d777d;
  font-size: 23px;
}

.roulette-modal-head button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.name-fields {
  display: grid;
  grid-template-columns: 1fr 24px 1fr;
  align-items: end;
  gap: 7px;
  margin-top: 17px;
}

.name-fields label {
  min-width: 0;
}

.name-fields label span {
  display: block;
  margin: 0 0 5px 3px;
  color: #a37d88;
  font-size: 6px;
  font-weight: 900;
  letter-spacing: 0.12em;
}

.name-fields input {
  width: 100%;
  height: 42px;
  padding: 0 11px;
  border: 1px solid #eadde1;
  border-radius: 13px;
  outline: none;
  background: rgba(255, 255, 255, 0.9);
  font-size: 11px;
  font-weight: 800;
  text-align: center;
}

.name-fields input:focus {
  border-color: #e17b91;
  box-shadow: 0 0 0 3px rgba(231, 105, 133, 0.1);
}

.name-heart {
  height: 42px;
  display: grid;
  place-items: center;
  color: #df7188;
  font-size: 12px;
}

.roulette-stage {
  position: relative;
  min-height: 270px;
  display: grid;
  place-items: center;
  margin-top: 7px;
}

.roulette-rim {
  position: relative;
  width: 238px;
  height: 238px;
  display: grid;
  place-items: center;
  border: 9px solid #fff;
  border-radius: 50%;
  background: #fff;
  box-shadow:
    0 17px 34px rgba(104, 61, 83, 0.2),
    0 0 0 1px rgba(219, 195, 203, 0.8),
    inset 0 0 0 1px rgba(255, 255, 255, 0.7);
}

.roulette-wheel {
  position: relative;
  width: 220px;
  height: 220px;
  border-radius: 50%;
  background: conic-gradient(
    from -22.5deg,
    #ef8299 0 45deg,
    #a98bd6 45deg 90deg,
    #f5a083 90deg 135deg,
    #897dc1 135deg 180deg,
    #ef8299 180deg 225deg,
    #a98bd6 225deg 270deg,
    #f5a083 270deg 315deg,
    #897dc1 315deg 360deg
  );
  box-shadow: inset 0 0 0 2px rgba(255, 255, 255, 0.48);
  transition: transform 3.2s cubic-bezier(0.12, 0.68, 0.08, 1);
}

.roulette-wheel::after {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: radial-gradient(circle, transparent 54%, rgba(77, 46, 59, 0.12));
  content: '';
}

.roulette-wheel > span {
  position: absolute;
  z-index: 1;
  top: calc(50% - 10px);
  left: calc(50% - 34px);
  width: 68px;
  overflow: hidden;
  color: #fff;
  font-size: 9px;
  font-weight: 900;
  text-align: center;
  text-overflow: ellipsis;
  text-shadow: 0 1px 5px rgba(59, 35, 45, 0.24);
  white-space: nowrap;
}

.roulette-cap {
  position: absolute;
  z-index: 3;
  width: 62px;
  height: 62px;
  display: grid;
  place-items: center;
  align-content: center;
  border: 6px solid rgba(255, 255, 255, 0.92);
  border-radius: 50%;
  background: linear-gradient(145deg, #fff, #faedf1);
  box-shadow: 0 7px 18px rgba(78, 47, 59, 0.25);
  color: #d85e78;
}

.roulette-cap b {
  font-size: 17px;
  line-height: 1;
}

.roulette-cap small {
  margin-top: 2px;
  font-size: 5px;
  font-weight: 900;
  letter-spacing: 0.1em;
}

.roulette-pointer {
  position: absolute;
  z-index: 5;
  top: 8px;
  left: 50%;
  width: 0;
  height: 0;
  border-top: 25px solid #cf526d;
  border-right: 14px solid transparent;
  border-left: 14px solid transparent;
  filter: drop-shadow(0 5px 5px rgba(72, 42, 51, 0.24));
  transform: translateX(-50%);
}

.roulette-result {
  min-height: 73px;
  display: grid;
  place-items: center;
  align-content: center;
  padding: 10px;
  border: 1px solid #eadfe2;
  border-radius: 17px;
  background: rgba(249, 244, 246, 0.84);
  text-align: center;
}

.roulette-result.visible {
  border-color: #f0c5cf;
  background: linear-gradient(135deg, #fff0f4, #f4efff);
  box-shadow: 0 8px 18px rgba(177, 87, 118, 0.1);
}

.roulette-result span {
  color: #af7a88;
  font-size: 7px;
  font-weight: 900;
  letter-spacing: 0.1em;
}

.roulette-result strong {
  margin-top: 3px;
  color: #c94f69;
  font-size: 17px;
}

.roulette-result p {
  margin: 3px 0 0;
  color: var(--muted);
  font-size: 8px;
}

.spin-button {
  width: 100%;
  min-height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  margin-top: 11px;
  border-radius: 15px;
  background: linear-gradient(135deg, #ea7189, #9c7bd0);
  box-shadow: 0 10px 20px rgba(196, 84, 120, 0.22);
  color: #fff;
  font-size: 11px;
  font-weight: 900;
}

.spin-button span {
  font-size: 18px;
}

.spin-button:disabled {
  cursor: not-allowed;
  box-shadow: none;
  filter: grayscale(0.5);
  opacity: 0.48;
}

.local-note {
  display: block;
  margin-top: 9px;
  color: #a08f94;
  font-size: 7px;
  text-align: center;
}

@media (max-width: 360px), (max-height: 680px) {
  .roulette-overlay {
    align-items: flex-start;
    padding: 9px;
  }

  .roulette-modal {
    max-height: 100%;
    padding: 16px;
    border-radius: 22px;
  }

  .roulette-stage {
    min-height: 238px;
  }

  .roulette-rim {
    width: 210px;
    height: 210px;
  }

  .roulette-wheel {
    width: 192px;
    height: 192px;
  }

  .roulette-pointer {
    top: 7px;
  }
}
</style>
