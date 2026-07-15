<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useDateStore } from '@/stores/dateStore'
import BaseInput from '@/components/common/BaseInput.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseCard from '@/components/common/BaseCard.vue'

const store = useDateStore()
const router = useRouter()

const nameInput = ref(store.name)
const pwInput = ref('')

function changeAuthMode(mode: 'enter' | 'register') {
  store.authMode = mode
}

function handleAuth() {
  if (store.authMode === 'register') {
    const success = store.register(nameInput.value, pwInput.value)
    if (success) {
      router.push({ name: 'chat' })
      if (!store.surveyDone) {
        store.showSurvey = true
      }
    }
  } else {
    const success = store.login(nameInput.value, pwInput.value)
    if (success) {
      router.push({ name: 'chat' })
      if (!store.surveyDone) {
        store.showSurvey = true
      }
    }
  }
}
</script>

<template>
  <div class="entrance-container">
    <div class="brand">
      <div class="logo">42</div>
      <small>우리 사이의 데이트 코스</small>
      <h1>사이<span>42</span></h1>
      <p>오늘의 둘을 위한,<br />조금 더 다정한 대전 데이트</p>
    </div>

    <BaseCard class="login-card">
      <div class="seg">
        <button :class="{ active: store.authMode === 'enter' }" @click="changeAuthMode('enter')">
          입장하기
        </button>
        <button
          :class="{ active: store.authMode === 'register' }"
          @click="changeAuthMode('register')"
        >
          처음 등록
        </button>
      </div>

      <BaseInput
        id="name"
        v-model="nameInput"
        label="커플 닉네임"
        placeholder="예: 복숭아와호두"
        :maxlength="14"
      />

      <BaseInput
        id="pw"
        v-model="pwInput"
        type="password"
        label="우리만의 비밀번호"
        placeholder="숫자 4자리"
        :maxlength="4"
        inputmode="numeric"
      />

      <BaseButton variant="primary" full @click="handleAuth">
        {{ store.authMode === 'register' ? '우리 사이42 등록하기 →' : '우리 데이트 보러 가기 →' }}
      </BaseButton>

      <p class="help">
        {{
          store.authMode === 'register'
            ? '새 닉네임과 숫자 4자리 비밀번호를 등록해요.'
            : '등록한 닉네임과 비밀번호로 입장해요.'
        }}
      </p>
    </BaseCard>

    <p class="demo-help">와이어프레임 데모 계정: 복숭아와호두 / 0420</p>
  </div>
</template>

<style scoped>
.entrance-container {
  padding: 43px 22px 28px;
  overflow-y: auto;
  height: 100%;
  background: linear-gradient(150deg, #fff0dc, #fff8f8 45%, #ece6ff);
}

.brand {
  text-align: center;
  margin: 22px 0 30px;
}

.logo {
  width: 74px;
  height: 74px;
  margin: auto;
  display: grid;
  place-items: center;
  border-radius: 27px 27px 27px 8px;
  transform: rotate(-6deg);
  background: linear-gradient(145deg, var(--pink), var(--pink-gradient-end));
  color: #fff;
  font-size: 28px;
  font-weight: 900;
  box-shadow: 0 14px 26px rgba(243, 93, 117, 0.26);
}

.brand small {
  display: block;
  margin-top: 16px;
  color: #e75d74;
  font-weight: 800;
  font-size: 10px;
  letter-spacing: 0.08em;
}

.brand h1 {
  margin: 3px 0 7px;
  font-size: 47px;
  letter-spacing: -3px;
  font-weight: 900;
}

.brand h1 span {
  color: var(--pink);
}

.brand p {
  margin: 0;
  color: var(--muted);
  font-size: 14px;
  line-height: 1.55;
}

.login-card {
  padding: 19px;
}

.seg {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px;
  padding: 4px;
  border-radius: 14px;
  background: #f3ebe8;
}

.seg button {
  padding: 10px;
  border-radius: 11px;
  background: transparent;
  color: var(--muted);
  font-size: 12px;
  font-weight: 800;
  transition: all 0.2s;
}

.seg button.active {
  background: #fff;
  color: #e75d74;
  box-shadow: 0 4px 10px rgba(92, 66, 72, 0.08);
}

.login-card :deep(.btn) {
  margin-top: 19px;
}

.help {
  text-align: center;
  color: var(--muted);
  font-size: 10px;
  line-height: 1.5;
  margin-top: 10px;
}

.demo-help {
  text-align: center;
  color: var(--muted);
  font-size: 10px;
  line-height: 1.5;
  margin-top: 20px;
}
</style>
