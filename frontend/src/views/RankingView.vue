<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useDateStore } from '@/stores/dateStore'
import BaseCard from '@/components/common/BaseCard.vue'
import LeafletMap from '@/components/map/LeafletMap.vue'
import { formatDistrict } from '@/utils/district'

const store = useDateStore()
const router = useRouter()
const rankTab = ref<'all' | 'masters'>('all')

const sortedRankings = computed(() => {
  return store.rankings
})

function handleLike(postId: string, likedByMe: boolean) {
  void store.likeRankItem(postId, likedByMe)
}

function showHelp() {
  store.triggerToast('이용 횟수와 좋아요를 합산해 마스터를 선정해요')
}

const editingId = ref<string | null>(null)
const editCommentText = ref('')
const scrollArea = ref<HTMLElement | null>(null)
const pullDistance = ref(0)
const pullStartY = ref<number | null>(null)
const refreshing = ref(false)

function startEdit(postId: string, comment: string) {
  editingId.value = postId
  editCommentText.value = comment
}

function cancelEdit() {
  editingId.value = null
  editCommentText.value = ''
}

async function saveEdit(postId: string) {
  if (await store.updateCommunityPost(postId, editCommentText.value)) cancelEdit()
}

async function handleDelete(postId: string) {
  if (confirm('랭킹보드에서 이 게시글을 삭제할까요?')) await store.deleteCommunityPost(postId)
}

async function startCourse(postId: string) {
  if (await store.startCommunityCourse(postId)) await router.push({ name: 'current' })
}

function toggleRoute(postId: string) {
  if (store.selectedCommunityCourse?.postId === postId) {
    store.selectedCommunityCourse = null
  } else {
    void store.loadCommunityCourse(postId)
  }
}

async function refreshRankings() {
  if (refreshing.value) return
  refreshing.value = true
  const startedAt = Date.now()
  if (rankTab.value === 'masters') await store.loadMasters()
  else await store.loadRankings()
  const remainingDuration = 600 - (Date.now() - startedAt)
  if (remainingDuration > 0) await new Promise((resolve) => setTimeout(resolve, remainingDuration))
  refreshing.value = false
}

function startPull(event: TouchEvent) {
  if ((scrollArea.value?.scrollTop ?? 0) <= 0) pullStartY.value = event.touches[0]?.clientY ?? null
}

function movePull(event: TouchEvent) {
  if (pullStartY.value === null) return
  pullDistance.value = Math.min(
    78,
    Math.max(0, (event.touches[0]?.clientY ?? pullStartY.value) - pullStartY.value),
  )
}

function endPull() {
  const shouldRefresh = pullDistance.value >= 58
  pullStartY.value = null
  pullDistance.value = 0
  if (shouldRefresh) void refreshRankings()
}

onMounted(() => {
  void refreshRankings()
})
watch(rankTab, () => {
  void refreshRankings()
})
</script>

<template>
  <div class="ranking-view">
    <header class="top-bar">
      <div>
        <p class="section-label">COMMUNITY</p>
        <h2>데이트 랭킹보드</h2>
      </div>
      <button class="help-btn" @click="showHelp">?</button>
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
        {{ refreshing ? '랭킹을 새로 불러오는 중…' : '놓으면 새로고침' }}
      </div>
      <!-- Master Banner Card -->
      <BaseCard class="master-card">
        <span class="banner-label">이번 주 데이트 마스터</span>
        <h3>🏆 공개 코스 랭킹</h3>
        <p>완료한 데이트 코스를 다른 커플과 나눠요.</p>
        <div class="crown">👑</div>
      </BaseCard>

      <!-- Tabs -->
      <div class="tabs">
        <button :class="{ active: rankTab === 'all' }" @click="rankTab = 'all'">
          전체
        </button>
        <button :class="{ active: rankTab === 'masters' }" @click="rankTab = 'masters'">
          마스터 랭킹
        </button>
      </div>

      <!-- Rankings List -->
      <div v-if="rankTab === 'all'" class="ranklist">
        <BaseCard v-for="(item, idx) in sortedRankings" :key="item.postId" class="rank-card">
          <div class="rank-head">
            <div class="num">{{ idx + 1 }}</div>
            <div class="rank-info">
              <div class="theme-row">
                <span class="theme-tag">{{ formatDistrict(item.mainDistrict) }}</span>
                <span class="heart-place-message">
                  경로 중에 하트 {{ item.placeHeartCount }}곳 받은 장소가 있어요!!
                </span>
              </div>
              <h3>{{ item.courseTitle }}</h3>
              <div class="meta">
                <span>{{ item.authorNickname }}</span>
                <!-- <span>순위 {{ item.rank ?? idx + 1 }}</span> -->
              </div>
            </div>
          </div>
          <!-- Comment Container -->
          <div class="comment-container">
            <div v-if="editingId === item.postId" class="edit-comment-row">
              <input
                v-model="editCommentText"
                class="edit-input"
                @keydown.enter="saveEdit(item.postId)"
              />
              <div class="edit-actions">
                <button class="text-action-btn save-btn" @click="saveEdit(item.postId)">
                  저장
                </button>
                <button class="text-action-btn" @click="cancelEdit">취소</button>
              </div>
            </div>
            <div v-else class="comment-body">
              <div class="comment">“{{ item.oneLineComment }}”</div>
              <div v-if="item.authorNickname === store.name" class="my-post-actions">
                <button
                  class="text-action-btn"
                  @click="startEdit(item.postId, item.oneLineComment)"
                >
                  수정
                </button>
                <button class="text-action-btn delete-text" @click="handleDelete(item.postId)">
                  삭제
                </button>
              </div>
            </div>
          </div>
          <div class="places">
            <span v-for="tag in item.tags" :key="tag">{{ tag }}</span>
          </div>
          <button class="route-btn" @click="toggleRoute(item.postId)">
            {{
              store.selectedCommunityCourse?.postId === item.postId
                ? '코스 경로 닫기'
                : '🗺️ 코스 경로 보기'
            }}
          </button>
          <div v-if="store.selectedCommunityCourse?.postId === item.postId" class="route-preview">
            <LeafletMap
              :coords="
                store.selectedCommunityCourse.places.flatMap((place) =>
                  place.place.latitude !== null && place.place.longitude !== null
                    ? [[place.place.latitude, place.place.longitude]]
                    : [],
                )
              "
              :places="store.selectedCommunityCourse.places.map((place) => place.place.name)"
              static
            />
          </div>
          <div class="actions">
            <button class="like-btn" @click="handleLike(item.postId, item.likedByMe)">
              {{ item.likedByMe ? '♥' : '♡' }} {{ item.courseLikeCount }}
            </button>
            <button class="import-btn" :disabled="store.loading" @click="startCourse(item.postId)">
              현재 데이트로 시작
            </button>
          </div>
        </BaseCard>
      </div>
      <div v-else class="ranklist">
        <BaseCard v-for="master in store.masters" :key="master.profileId" class="rank-card master-rank-card">
          <div class="rank-head">
            <div class="num">{{ master.rank }}</div>
            <div class="rank-info">
              <span class="theme-tag">데이트 마스터</span>
              <h3>{{ master.nickname }}</h3>
              <div class="meta">
                <span>공개 코스 {{ master.publishedCourseCount }}개</span>
                <span>받은 좋아요 {{ master.receivedLikeCount }}개</span>
              </div>
            </div>
          </div>
        </BaseCard>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ranking-view {
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

.help-btn {
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

.master-card {
  padding: 20px;
  position: relative;
  overflow: hidden;
  color: #fff;
  background: linear-gradient(135deg, #ff8397, #917ed4);
  margin-top: 15px;
}

.banner-label {
  color: #fff;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.master-card h3 {
  margin: 5px 0 6px;
  font-size: 18px;
  font-weight: 800;
}

.master-card p {
  margin: 0;
  color: rgba(255, 255, 255, 0.8);
  font-size: 10px;
}

.crown {
  position: absolute;
  right: 11px;
  bottom: -8px;
  font-size: 68px;
  opacity: 0.34;
}

.tabs {
  display: flex;
  gap: 7px;
  overflow-x: auto;
  padding: 13px 0 10px;
  scrollbar-width: none;
}

.tabs::-webkit-scrollbar {
  display: none;
}

.tabs button {
  flex: none;
  padding: 9px 11px;
  border-radius: 12px;
  background: #fff;
  color: var(--muted);
  font-size: 9px;
  font-weight: 800;
  box-shadow: 0 4px 10px rgba(80, 55, 60, 0.06);
}

.tabs button.active {
  background: var(--pink);
  color: #fff;
}

.ranklist {
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

.rank-card {
  padding: 13px;
}

.rank-head {
  display: flex;
  gap: 11px;
}

.num {
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  background: #ffe4e9;
  color: #db536a;
  font-weight: 900;
}

.rank-info {
  flex: 1;
}

.theme-tag {
  color: #e75d74;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.theme-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.heart-place-message {
  color: var(--muted);
  font-size: 9px;
  font-weight: 700;
}

.rank-card h3 {
  margin: 0 0 4px;
  font-size: 15px;
  font-weight: 800;
}

.meta {
  display: flex;
  justify-content: space-between;
  color: var(--muted);
  font-size: 11px;
}

.comment {
  margin: 9px 0;
  padding: 9px 10px;
  border-radius: 11px;
  background: #fff5f7;
  color: #6f5b5f;
  font-size: 11px;
  line-height: 1.5;
}

.places {
  display: flex;
  gap: 5px;
  overflow-x: auto;
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
  font-size: 9px;
  font-weight: 700;
}

.actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
}

.route-btn {
  width: 100%;
  margin-top: 10px;
  padding: 9px;
  border-radius: 10px;
  background: #f3efed;
  color: #66575a;
  font-size: 11px;
  font-weight: 800;
}
.route-preview {
  height: 180px;
  margin-top: 8px;
  overflow: hidden;
  border-radius: 13px;
}

.actions button {
  padding: 8px 9px;
  border-radius: 10px;
  font-size: 9px;
  font-weight: 800;
  border: 0;
}

.like-btn {
  background: #fff0f2;
  color: #d2576b;
}

.use-count {
  font-size: 9px;
  color: var(--muted);
}

.import-btn {
  background: #eee8ff;
  color: #66568d;
}

/* My Post Comments Edit/Delete Actions */
.comment-container {
  margin-top: 11px;
}

.comment-body {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.my-post-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.text-action-btn {
  font-size: 8px;
  font-weight: 800;
  padding: 4px 6px;
  background: #f3eceb;
  color: #66575a;
  border-radius: 6px;
  border: 0;
  cursor: pointer;
}

.text-action-btn.delete-text {
  background: #ffebeb;
  color: #c84d61;
}

.edit-comment-row {
  display: flex;
  gap: 8px;
  align-items: center;
  width: 100%;
}

.edit-input {
  flex: 1;
  height: 28px;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 0 8px;
  font-size: 10px;
  background: #fffdfa;
  outline: 0;
}

.edit-actions {
  display: flex;
  gap: 4px;
}

.text-action-btn.save-btn {
  background: #e1ffd4;
  color: #2b6118;
}
</style>
