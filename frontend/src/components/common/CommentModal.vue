<script setup lang="ts">
import { ref } from 'vue';
import { useDateStore } from '@/stores/dateStore';
import BaseButton from './BaseButton.vue';

const store = useDateStore();
const comment = ref('');
const rating = ref(5);

function setRating(r: number) {
  rating.value = r;
}

function submit() {
  store.submitReview(comment.value, rating.value);
  comment.value = '';
  rating.value = 5;
}

function cancel() {
  store.showCommentModal = false;
}
</script>

<template>
  <div v-if="store.showCommentModal" class="overlay open">
    <div class="modal">
      <div class="big">💌</div>
      <h3>오늘 우리 사이, 어땠나요?</h3>
      <p>한 줄 코멘트를 남기면 다른 커플에게도 도움이 돼요.</p>
      <textarea
        v-model="comment"
        maxlength="60"
        placeholder="예: 비 오는 날에도 이동이 편해서 좋았어요!"
      ></textarea>
      <div class="rating">
        <button
          v-for="i in 5"
          :key="i"
          @click="setRating(i)"
        >
          {{ i <= rating ? '♥' : '♡' }}
        </button>
      </div>
      <div class="modalacts">
        <BaseButton variant="secondary" @click="cancel">조금 더 데이트</BaseButton>
        <BaseButton variant="primary" @click="submit">기록 남기기</BaseButton>
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
  align-items: center;
  justify-content: center;
  padding: 14px;
  background: rgba(53, 42, 45, 0.45);
  backdrop-filter: blur(3px);
}

.modal {
  width: 100%;
  max-width: 340px;
  background: #fff;
  box-shadow: var(--shadow);
  padding: 21px;
  border-radius: 24px;
  text-align: center;
}

.big {
  font-size: 40px;
}

h3 {
  margin: 8px 0 6px;
  font-size: 16px;
}

p {
  margin: 0 0 13px;
  color: var(--muted);
  font-size: 10px;
  line-height: 1.5;
}

textarea {
  width: 100%;
  height: 88px;
  padding: 12px;
  border: 1px solid var(--line);
  border-radius: 14px;
  resize: none;
  outline: 0;
  font-family: inherit;
  color: var(--ink);
}

textarea:focus {
  border-color: var(--pink);
}

.rating {
  display: flex;
  justify-content: center;
  gap: 7px;
  margin: 11px 0;
}

.rating button {
  background: transparent;
  color: var(--pink);
  font-size: 25px;
  border: 0;
  cursor: pointer;
}

.modalacts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-top: 15px;
}
</style>
