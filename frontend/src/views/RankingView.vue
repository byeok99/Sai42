<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useDateStore } from '@/stores/dateStore'
import BaseCard from '@/components/common/BaseCard.vue'

const store = useDateStore()
const router = useRouter()

const rankTab = ref<'popular' | 'masters' | 'new'>('popular')

const sortedRankings = computed(() => {
  const list = [...store.rankings]
  if (rankTab.value === 'popular') {
    return list.sort((x, y) => y.likes - x.likes)
  }
  if (rankTab.value === 'masters') {
    return list.sort((x, y) => y.likes + y.use - (x.likes + x.use))
  }
  if (rankTab.value === 'new') {
    // Treat IDs with 'u' (user created) as newest, or simple reverse order for demo
    return list.reverse()
  }
  return list
})

function handleLike(id: string) {
  store.likeRankItem(id)
}

function handleImport(id: string) {
  const item = store.rankings.find((x) => x.id === id)
  if (item) {
    store.importRankedCourse(item)
    setTimeout(() => {
      router.push({ name: 'chat' })
    }, 450)
  }
}

function showHelp() {
  store.triggerToast('이용 횟수와 좋아요를 합산해 마스터를 선정해요')
}

const editingId = ref<string | null>(null)
const editCommentText = ref('')

function startEdit(id: string, comment: string) {
  editingId.value = id
  editCommentText.value = comment
}

function cancelEdit() {
  editingId.value = null
  editCommentText.value = ''
}

function saveEdit(id: string) {
  if (!editCommentText.value.trim()) return
  store.updateRankComment(id, editCommentText.value)
  editingId.value = null
  editCommentText.value = ''
}

function handleDelete(id: string) {
  if (confirm('이 포스트를 삭제하시겠습니까?')) {
    store.deleteRankItem(id)
  }
}
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

    <div class="scroll-area">
      <!-- Master Banner Card -->
      <BaseCard class="master-card">
        <span class="banner-label">이번 주 데이트 마스터</span>
        <h3>🏆 구름이와 몽글이</h3>
        <p>코스 이용 128회 · 좋아요 342개</p>
        <div class="crown">👑</div>
      </BaseCard>

      <!-- Tabs -->
      <div class="tabs">
        <button :class="{ active: rankTab === 'popular' }" @click="rankTab = 'popular'">
          인기 코스
        </button>
        <button :class="{ active: rankTab === 'masters' }" @click="rankTab = 'masters'">
          데이트 마스터
        </button>
        <button :class="{ active: rankTab === 'new' }" @click="rankTab = 'new'">새 코스</button>
      </div>

      <!-- Rankings List -->
      <div class="ranklist">
        <BaseCard v-for="(item, idx) in sortedRankings" :key="item.id" class="rank-card">
          <div class="rank-head">
            <div class="num">{{ idx + 1 }}</div>
            <div class="rank-info">
              <span class="theme-tag">{{ item.theme || '커플 추천' }}</span>
              <h3>{{ item.title }}</h3>
              <div class="meta">
                <span>{{ item.creator }}</span>
                <span>★ {{ item.rating }}</span>
              </div>
            </div>
          </div>
          <!-- Comment Container -->
          <div class="comment-container">
            <div v-if="editingId === item.id" class="edit-comment-row">
              <input
                v-model="editCommentText"
                class="edit-input"
                @keydown.enter="saveEdit(item.id)"
              />
              <div class="edit-actions">
                <button class="text-action-btn save-btn" @click="saveEdit(item.id)">저장</button>
                <button class="text-action-btn" @click="cancelEdit">취소</button>
              </div>
            </div>
            <div v-else class="comment-body">
              <div class="comment">“{{ item.comment }}”</div>
              <div v-if="item.creator === store.name" class="my-post-actions">
                <button class="text-action-btn" @click="startEdit(item.id, item.comment)">
                  수정
                </button>
                <button class="text-action-btn delete-text" @click="handleDelete(item.id)">
                  삭제
                </button>
              </div>
            </div>
          </div>
          <div class="places">
            <span v-for="place in item.places" :key="place">{{ place }}</span>
          </div>
          <div class="actions">
            <button class="like-btn" @click="handleLike(item.id)">♡ {{ item.likes }}</button>
            <span class="use-count">사용 {{ item.use }}회</span>
            <button class="import-btn" @click="handleImport(item.id)">내 코스로 가져오기</button>
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
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.rank-card h3 {
  margin: 0 0 4px;
  font-size: 13px;
  font-weight: 800;
}

.meta {
  display: flex;
  justify-content: space-between;
  color: var(--muted);
  font-size: 9px;
}

.comment {
  margin: 9px 0;
  padding: 9px 10px;
  border-radius: 11px;
  background: #fff5f7;
  color: #6f5b5f;
  font-size: 9px;
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
  font-size: 8px;
  font-weight: 700;
}

.actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
}

.actions button {
  padding: 8px 9px;
  border-radius: 10px;
  font-size: 8px;
  font-weight: 800;
  border: 0;
}

.like-btn {
  background: #fff0f2;
  color: #d2576b;
}

.use-count {
  font-size: 8px;
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
