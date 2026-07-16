<script setup lang="ts">
import { computed, ref } from 'vue'
import { useDateStore } from '@/stores/dateStore'
import BaseCard from '@/components/common/BaseCard.vue'
import { formatDistrict } from '@/utils/district'

const store = useDateStore()
const scrollArea = ref<HTMLElement | null>(null)
const pullDistance = ref(0)
const pullStartY = ref<number | null>(null)
const refreshing = ref(false)

const averageRating = computed(() => {
  if (store.history.length === 0) return '0'
  return String(store.history.reduce((acc, curr) => acc + curr.heartedPlaceCount, 0))
})

const totalPlacesVisited = computed(() => {
  return store.history.reduce((acc, curr) => acc + curr.totalPlaceCount, 0)
})

const postsByCourseId = computed(
  () =>
    new Map(
      store.rankings
        .filter((post) => post.authorNickname === store.name)
        .map((post) => [post.courseId, post]),
    ),
)

function showInfo() {
  store.triggerToast('완료한 데이트 코스를 불러왔어요.')
}

async function refreshHistory() {
  if (refreshing.value) return
  refreshing.value = true
  const startedAt = Date.now()
  await Promise.all([store.loadHistory(), store.loadRankings()])
  const remainingDuration = 600 - (Date.now() - startedAt)
  if (remainingDuration > 0) await new Promise((resolve) => setTimeout(resolve, remainingDuration))
  refreshing.value = false
}

function startPull(event: TouchEvent) {
  if (refreshing.value || (scrollArea.value?.scrollTop ?? 0) > 0 || event.touches.length !== 1)
    return
  pullStartY.value = event.touches[0]?.clientY ?? null
}

function movePull(event: TouchEvent) {
  if (pullStartY.value === null) return
  if ((scrollArea.value?.scrollTop ?? 0) > 0) {
    pullStartY.value = null
    pullDistance.value = 0
    return
  }

  const distance = (event.touches[0]?.clientY ?? pullStartY.value) - pullStartY.value
  if (distance <= 0) {
    pullDistance.value = 0
    return
  }

  if (event.cancelable) event.preventDefault()
  pullDistance.value = Math.min(
    78,
    distance,
  )
}

function endPull() {
  const shouldRefresh = pullDistance.value >= 58
  pullStartY.value = null
  pullDistance.value = 0
  if (shouldRefresh) void refreshHistory()
}

async function editPost(courseId: string, currentComment: string) {
  const post = postsByCourseId.value.get(courseId)
  if (!post) return
  const nextComment = prompt('수정할 한 줄 코멘트를 입력해 주세요.', currentComment)
  if (nextComment !== null) await store.updateCommunityPost(post.postId, nextComment)
}

async function deletePost(courseId: string) {
  const post = postsByCourseId.value.get(courseId)
  if (post && confirm('랭킹보드에서 이 게시글을 삭제할까요?')) {
    await store.deleteCommunityPost(post.postId)
  }
}

</script>

<template>
  <div class="history-view">
    <header class="top-bar">
      <div>
        <p class="section-label">OUR MEMORY</p>
        <h2>옛날 데이트 코스</h2>
      </div>
      <button class="info-btn" @click="showInfo">⌁</button>
    </header>

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
        {{ refreshing ? '추억을 새로 불러오는 중…' : '놓으면 새로고침' }}
      </div>
      <!-- Stats Summary Card -->
      <BaseCard class="summary-card">
        <div>
          <strong>{{ store.history.length }}</strong>
          <span>함께한 데이트</span>
        </div>
        <div>
          <strong>{{ totalPlacesVisited }}</strong>
          <span>방문한 장소</span>
        </div>
        <div>
          <strong>{{ averageRating }}</strong>
          <span>남긴 장소 하트</span>
        </div>
      </BaseCard>

      <!-- Month Header -->
      <div class="month-header">
        <strong>완료한 데이트</strong>
        <span>우리의 기록</span>
      </div>

      <!-- History List -->
      <div class="hlist">
        <BaseCard v-for="item in store.history" :key="item.courseId" class="history-card">
          <div class="hhead">
            <div class="date-badge">{{ item.date.slice(-2) }}</div>
            <div>
              <span class="label">{{ formatDistrict(item.mainDistrict) }}</span>
              <h3>{{ item.courseTitle }}</h3>
              <p>{{ item.totalPlaceCount }}개 장소 · 하트 {{ item.heartedPlaceCount }}개</p>
            </div>
          </div>
          <div class="hcomment">“{{ item.oneLineComment ?? '남긴 코멘트가 없어요.' }}”</div>
          <div v-if="postsByCourseId.has(item.courseId)" class="post-actions">
            <button @click="editPost(item.courseId, item.oneLineComment ?? '')">게시글 수정</button>
            <button class="delete" @click="deletePost(item.courseId)">게시글 삭제</button>
          </div>
        </BaseCard>
      </div>
    </div>
  </div>
</template>

<style scoped>
.history-view {
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

.info-btn {
  width: 36px;
  height: 36px;
  border-radius: 13px;
  background: #fff;
  box-shadow: var(--shadow);
  font-weight: 900;
  border: 0;
  cursor: pointer;
  color: var(--ink);
  display: grid;
  place-items: center;
}

.summary-card {
  padding: 14px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  background: linear-gradient(135deg, #ffe7eb, #eee8ff);
  margin-top: 15px;
}

.summary-card div {
  text-align: center;
}

.summary-card div + div {
  border-left: 1px solid rgba(85, 61, 68, 0.12);
}

.summary-card strong {
  display: block;
  font-size: 18px;
  font-weight: 800;
}

.summary-card span {
  font-size: 8px;
  color: var(--muted);
}

.month-header {
  display: flex;
  justify-content: space-between;
  padding: 17px 3px 9px;
  font-size: 12px;
}

.month-header span {
  color: var(--muted);
  font-size: 9px;
}

.hlist {
  display: grid;
  gap: 10px;
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

.history-card {
  padding: 13px;
}

.hhead {
  display: flex;
  gap: 10px;
}

.date-badge {
  width: 43px;
  height: 43px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  background: #ffe4e9;
  color: #dc526a;
  font-weight: 900;
}

.label {
  display: block;
  color: #e75d74;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.history-card h3 {
  margin: 2px 0 4px;
  font-size: 14px;
  font-weight: 800;
}

.history-card p {
  margin: 0;
  color: var(--muted);
  font-size: 9px;
}

.hcomment {
  margin-top: 10px;
  padding: 9px;
  border-radius: 11px;
  background: #f8f3f1;
  font-size: 11px;
  line-height: 1.5;
}

.post-actions {
  display: flex;
  justify-content: flex-end;
  gap: 6px;
  margin-top: 8px;
}

.post-actions button {
  padding: 5px 7px;
  border: 0;
  border-radius: 7px;
  background: #f3eceb;
  color: #66575a;
  font-size: 9px;
  font-weight: 800;
}

.post-actions .delete {
  background: #ffebeb;
  color: #c84d61;
}

.places {
  display: flex;
  gap: 5px;
  overflow-x: auto;
  margin-top: 9px;
  scrollbar-width: none;
}

.places::-webkit-scrollbar {
  display: none;
}

.places span {
  flex: none;
  padding: 6px 8px;
  border-radius: 9px;
  background: #f3efed;
  font-size: 8px;
  font-weight: 700;
}
</style>
