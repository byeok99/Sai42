<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useDateStore } from '@/stores/dateStore'
import BaseCard from '@/components/common/BaseCard.vue'
import LeafletMap from '@/components/map/LeafletMap.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import { formatDistrict } from '@/utils/district'

const store = useDateStore()
const router = useRouter()
const rankTab = ref<'all' | 'masters'>('all')
const currentPage = ref(1)
const PAGE_SIZE = 5

const sortedRankings = computed(() => {
  return [...store.rankings]
    .sort(
      (a, b) =>
        b.courseLikeCount - a.courseLikeCount ||
        b.publishedAt.localeCompare(a.publishedAt) ||
        a.postId.localeCompare(b.postId),
    )
    .slice(0, PAGE_SIZE)
})
const pagedMasters = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE
  return store.masters.slice(start, start + PAGE_SIZE)
})
const podiumMasters = computed(() =>
  [2, 1, 3].flatMap((rank) => {
    const master = store.masters.find((item) => item.rank === rank)
    return master ? [master] : []
  }),
)
const listedMasters = computed(() =>
  currentPage.value === 1
    ? pagedMasters.value.filter((master) => master.rank > 3)
    : pagedMasters.value,
)
const totalPages = computed(() =>
  rankTab.value === 'all'
    ? Math.max(1, store.rankingMeta?.totalPages ?? 1)
    : Math.max(1, Math.ceil(store.masters.length / PAGE_SIZE)),
)

function courseRank(index: number) {
  return (currentPage.value - 1) * PAGE_SIZE + index + 1
}

function rankerClass(rank: number) {
  return rank <= 3 ? `ranker-card rank-${rank}` : ''
}

function masterInitial(nickname: string) {
  return Array.from(nickname.trim())[0] ?? '♥'
}

async function handleLike(postId: string, likedByMe: boolean) {
  await store.likeRankItem(postId, likedByMe, currentPage.value)
}

function showHelp() {
  store.triggerToast('인기 코스와 마스터는 공개 게시글이 받은 좋아요를 기준으로 선정해요')
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
  if (!confirm('랭킹보드에서 이 게시글을 삭제할까요?')) return
  if (await store.deleteCommunityPost(postId)) await refreshRankings()
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
  if (rankTab.value === 'masters') {
    await store.loadMasters()
  } else {
    await store.loadRankings(currentPage.value)
    const lastPage = Math.max(1, store.rankingMeta?.totalPages ?? 1)
    if (currentPage.value > lastPage) {
      currentPage.value = lastPage
      await store.loadRankings(currentPage.value)
    }
  }
  const remainingDuration = 600 - (Date.now() - startedAt)
  if (remainingDuration > 0) await new Promise((resolve) => setTimeout(resolve, remainingDuration))
  refreshing.value = false
}

async function changePage(page: number) {
  const targetPage = Math.min(Math.max(page, 1), totalPages.value)
  if (targetPage === currentPage.value) return
  currentPage.value = targetPage
  if (rankTab.value === 'all') await refreshRankings()
  scrollArea.value?.scrollTo({ top: 0, behavior: 'smooth' })
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
  currentPage.value = 1
  void refreshRankings()
})
</script>

<template>
  <div class="ranking-view">
    <PageHeader eyebrow="COMMUNITY" title="데이트 랭킹보드">
      <button class="help-btn" @click="showHelp">?</button>
    </PageHeader>

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
        <button :class="{ active: rankTab === 'all' }" @click="rankTab = 'all'">인기 코스</button>
        <button :class="{ active: rankTab === 'masters' }" @click="rankTab = 'masters'">
          마스터 랭킹
        </button>
      </div>

      <!-- Rankings List -->
      <div class="ranking-section-head">
        <div>
          <span>{{ rankTab === 'all' ? 'COURSE LEADERBOARD' : 'DATE MASTERS' }}</span>
          <h3>{{ rankTab === 'all' ? '가장 사랑받은 데이트' : '이번 주 명예의 전당' }}</h3>
        </div>
        <strong>{{ rankTab === 'all' ? '코스 하트순' : '받은 좋아요순' }}</strong>
      </div>
      <div v-if="rankTab === 'all'" class="ranklist">
        <BaseCard
          v-for="(item, idx) in sortedRankings"
          :key="item.postId"
          :class="['rank-card', rankerClass(courseRank(idx))]"
        >
          <div class="rank-head">
            <div class="num">
              <span v-if="courseRank(idx) <= 3" class="rank-trophy" aria-hidden="true">🏆</span>
              <span>{{ courseRank(idx) }}</span>
            </div>
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
      <div v-else class="master-view">
        <BaseCard v-if="currentPage === 1 && podiumMasters.length" class="podium-card">
          <div class="podium-glow podium-glow-left"></div>
          <div class="podium-glow podium-glow-right"></div>
          <div class="podium-caption">
            <span>WEEKLY TOP 3</span>
            <strong>함께 만든 데이트가 누군가의 영감이 되었어요</strong>
          </div>
          <div class="podium-stage" aria-label="마스터 랭킹 상위 3명">
            <div
              v-for="master in podiumMasters"
              :key="master.profileId"
              :class="['podium-column', `podium-rank-${master.rank}`]"
            >
              <div class="podium-profile">
                <span v-if="master.rank === 1" class="podium-crown" aria-hidden="true">♛</span>
                <div class="podium-avatar">{{ masterInitial(master.nickname) }}</div>
                <strong>{{ master.nickname }}</strong>
                <span>♥ {{ master.receivedLikeCount }}</span>
              </div>
              <div class="podium-step">
                <b>{{ master.rank }}</b>
                <small>공개 코스 {{ master.publishedCourseCount }}개</small>
              </div>
            </div>
          </div>
        </BaseCard>

        <div v-if="listedMasters.length" class="ranklist master-list">
          <BaseCard
            v-for="master in listedMasters"
            :key="master.profileId"
            class="rank-card master-rank-card"
          >
            <div class="rank-head">
              <div class="num">
                <span>{{ master.rank }}</span>
              </div>
              <div class="master-list-avatar">{{ masterInitial(master.nickname) }}</div>
              <div class="rank-info">
                <span class="theme-tag">데이트 마스터</span>
                <h3>{{ master.nickname }}</h3>
                <div class="meta">
                  <span>공개 코스 {{ master.publishedCourseCount }}개</span>
                  <span>♥ {{ master.receivedLikeCount }}개</span>
                </div>
              </div>
            </div>
          </BaseCard>
        </div>
      </div>
      <nav v-if="totalPages > 1" class="pagination" aria-label="랭킹 페이지">
        <button
          type="button"
          :disabled="currentPage === 1 || refreshing"
          aria-label="이전 페이지"
          @click="changePage(currentPage - 1)"
        >
          이전
        </button>
        <span>{{ currentPage }} / {{ totalPages }}</span>
        <button
          type="button"
          :disabled="currentPage === totalPages || refreshing"
          aria-label="다음 페이지"
          @click="changePage(currentPage + 1)"
        >
          다음
        </button>
      </nav>
    </div>
  </div>
</template>

<style scoped>
.ranking-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #fffaf7 0%, #fff7f9 46%, #f8f3ff 100%);
}

.help-btn {
  width: 36px;
  height: 36px;
  border-radius: 13px;
  background: #fff;
  box-shadow: 0 8px 18px rgba(91, 61, 68, 0.1);
  font-weight: 900;
  border: 0;
  cursor: pointer;
  color: var(--ink);
  display: grid;
  place-items: center;
}

.master-card {
  padding: 22px 20px;
  position: relative;
  overflow: hidden;
  color: #fff;
  background:
    radial-gradient(circle at 82% 18%, rgba(255, 255, 255, 0.28), transparent 24%),
    linear-gradient(135deg, #ff8397 0%, #cc79b5 48%, #8f7cd3 100%);
  margin-top: 16px;
  box-shadow: 0 16px 32px rgba(153, 100, 157, 0.24);
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
  gap: 4px;
  overflow-x: auto;
  margin: 14px 0 16px;
  padding: 4px;
  border: 1px solid rgba(238, 227, 224, 0.9);
  border-radius: 15px;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: 0 8px 20px rgba(80, 55, 60, 0.06);
  scrollbar-width: none;
}

.tabs::-webkit-scrollbar {
  display: none;
}

.tabs button {
  flex: 1;
  padding: 10px 12px;
  border-radius: 11px;
  background: transparent;
  color: var(--muted);
  font-size: 10px;
  font-weight: 800;
  box-shadow: none;
  transition:
    color 0.2s ease,
    background 0.2s ease,
    box-shadow 0.2s ease;
}

.tabs button.active {
  background: linear-gradient(135deg, var(--pink), #a887df);
  color: #fff;
  box-shadow: 0 7px 14px rgba(225, 103, 134, 0.22);
}

.ranking-section-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 12px;
  margin: 0 2px 11px;
}

.ranking-section-head span {
  display: block;
  margin-bottom: 3px;
  color: #b17691;
  font-size: 8px;
  font-weight: 900;
  letter-spacing: 0.12em;
}

.ranking-section-head h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 900;
}

.ranking-section-head > strong {
  flex: none;
  padding: 6px 9px;
  border-radius: 999px;
  background: #fff;
  color: #ad687d;
  box-shadow: 0 5px 12px rgba(94, 62, 70, 0.07);
  font-size: 8px;
  font-weight: 900;
}

.ranklist {
  display: grid;
  gap: 10px;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  padding: 16px 0 20px;
}

.pagination button {
  min-width: 58px;
  padding: 8px 12px;
  border: 0;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.9);
  color: var(--ink);
  box-shadow: 0 4px 10px rgba(80, 55, 60, 0.08);
  font-size: 10px;
  font-weight: 800;
  cursor: pointer;
}

.pagination button:disabled {
  cursor: default;
  opacity: 0.4;
}

.pagination span {
  min-width: 54px;
  padding: 7px 10px;
  border-radius: 999px;
  background: #f2eaff;
  color: #75648f;
  font-size: 10px;
  font-weight: 800;
  text-align: center;
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
  padding: 15px;
  border: 1px solid rgba(238, 227, 224, 0.72);
  box-shadow: 0 10px 24px rgba(87, 57, 65, 0.08);
}

.rank-card.ranker-card {
  position: relative;
  overflow: hidden;
  border: 1px solid transparent;
  isolation: isolate;
  box-shadow: 0 14px 28px rgba(117, 75, 97, 0.13);
}

.rank-card.ranker-card::after {
  position: absolute;
  z-index: -1;
  top: -34px;
  right: -24px;
  width: 115px;
  height: 115px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.43);
  content: '';
}

.rank-card.rank-1 {
  border-color: #f2c7d9;
  background: linear-gradient(135deg, #ffeef3 0%, #f4eaff 58%, #fff8f2 100%);
}

.rank-card.rank-2 {
  border-color: #d9d2ec;
  background: linear-gradient(135deg, #f5f1ff 0%, #edf5ff 60%, #fff 100%);
}

.rank-card.rank-3 {
  border-color: #efcbbb;
  background: linear-gradient(135deg, #fff0eb 0%, #fff4df 58%, #fffafb 100%);
}

.master-view {
  display: grid;
  gap: 12px;
}

.podium-card {
  position: relative;
  padding: 18px 12px 0;
  overflow: hidden;
  background:
    linear-gradient(rgba(77, 53, 84, 0.96), rgba(87, 62, 98, 0.98)),
    linear-gradient(135deg, #ff8397, #917ed4);
  box-shadow: 0 18px 34px rgba(75, 48, 83, 0.25);
  color: #fff;
}

.podium-glow {
  position: absolute;
  width: 150px;
  height: 150px;
  border-radius: 50%;
  filter: blur(4px);
  opacity: 0.28;
  pointer-events: none;
}

.podium-glow-left {
  top: -86px;
  left: -52px;
  background: #ff8fa3;
}

.podium-glow-right {
  right: -65px;
  bottom: 12px;
  background: #b69bff;
}

.podium-caption {
  position: relative;
  z-index: 1;
  display: grid;
  justify-items: center;
  gap: 3px;
  text-align: center;
}

.podium-caption span {
  color: #ffd4df;
  font-size: 8px;
  font-weight: 900;
  letter-spacing: 0.16em;
}

.podium-caption strong {
  color: rgba(255, 255, 255, 0.86);
  font-size: 9px;
  font-weight: 700;
}

.podium-stage {
  position: relative;
  z-index: 1;
  height: 252px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  align-items: end;
  gap: 6px;
  margin-top: 8px;
}

.podium-column {
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  text-align: center;
}

.podium-profile {
  position: relative;
  display: flex;
  min-height: 112px;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
  padding-bottom: 9px;
}

.podium-profile strong {
  width: 100%;
  overflow: hidden;
  color: #fff;
  font-size: 10px;
  font-weight: 900;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.podium-profile > span:last-child {
  color: rgba(255, 255, 255, 0.74);
  font-size: 8px;
  font-weight: 800;
}

.podium-avatar {
  width: 47px;
  height: 47px;
  display: grid;
  place-items: center;
  border: 3px solid rgba(255, 255, 255, 0.88);
  border-radius: 50%;
  background: linear-gradient(145deg, #ff9aae, #b99bea);
  box-shadow: 0 9px 20px rgba(35, 20, 42, 0.28);
  color: #fff;
  font-size: 18px;
  font-weight: 900;
}

.podium-rank-1 .podium-avatar {
  width: 56px;
  height: 56px;
  border-color: #ffe6a8;
  background: linear-gradient(145deg, #ff8397, #8e7ad0);
  box-shadow:
    0 0 0 5px rgba(255, 220, 145, 0.11),
    0 12px 24px rgba(35, 20, 42, 0.32);
  font-size: 21px;
}

.podium-crown {
  position: absolute;
  top: -2px;
  color: #ffe29a;
  font-size: 24px;
  line-height: 1;
  text-shadow: 0 4px 10px rgba(255, 211, 107, 0.3);
}

.podium-step {
  min-height: 80px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 5px;
  border-radius: 15px 15px 0 0;
  box-shadow: inset 0 1px rgba(255, 255, 255, 0.38);
}

.podium-step b {
  color: rgba(255, 255, 255, 0.96);
  font-size: 31px;
  font-weight: 900;
  line-height: 1;
}

.podium-step small {
  color: rgba(255, 255, 255, 0.72);
  font-size: 7px;
  font-weight: 800;
}

.podium-rank-1 .podium-step {
  min-height: 118px;
  background: linear-gradient(180deg, #ff8ea3, #a67fce);
}

.podium-rank-2 .podium-step {
  min-height: 91px;
  background: linear-gradient(180deg, #a896c4, #786b91);
}

.podium-rank-3 .podium-step {
  min-height: 73px;
  background: linear-gradient(180deg, #d89588, #a96f73);
}

.master-list {
  margin-top: 2px;
}

.master-rank-card {
  background: rgba(255, 255, 255, 0.88);
}

.master-list-avatar {
  width: 38px;
  height: 38px;
  display: grid;
  flex: none;
  place-items: center;
  border-radius: 50%;
  background: linear-gradient(145deg, #ffdce4, #ddd1ff);
  color: #8d657b;
  font-size: 14px;
  font-weight: 900;
}

.rank-head {
  display: flex;
  align-items: flex-start;
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

.ranker-card .num {
  height: 40px;
  grid-template-rows: 16px 14px;
  align-content: center;
  line-height: 1;
}

.rank-trophy {
  font-size: 13px;
  filter: saturate(0.9);
}

.rank-card.rank-1 .num {
  background: #f8df9a;
  color: #8c6418;
}

.rank-card.rank-2 .num {
  background: #e4dfea;
  color: #6c6178;
}

.rank-card.rank-3 .num {
  background: #efc5b3;
  color: #8a5540;
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
