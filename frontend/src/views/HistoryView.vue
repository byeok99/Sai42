<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useDateStore } from '@/stores/dateStore'
import BaseCard from '@/components/common/BaseCard.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import { formatDistrict } from '@/utils/district'

const store = useDateStore()
const scrollArea = ref<HTMLElement | null>(null)
const pullDistance = ref(0)
const pullStartY = ref<number | null>(null)
const refreshing = ref(false)
const selectedDate = ref<string | null>(null)

const seoulParts = new Intl.DateTimeFormat('en-CA', {
  timeZone: 'Asia/Seoul',
  year: 'numeric',
  month: '2-digit',
}).formatToParts(new Date())
const seoulPart = (type: string) =>
  Number(seoulParts.find((part) => part.type === type)?.value ?? 0)
const selectedYear = ref(seoulPart('year'))
const selectedMonth = ref(seoulPart('month'))

const monthLabel = computed(() => `${selectedYear.value}년 ${selectedMonth.value}월`)
const dateCounts = computed(() => {
  const counts = new Map<string, number>()
  store.history.forEach((item) => counts.set(item.date, (counts.get(item.date) ?? 0) + 1))
  return counts
})
const calendarDays = computed(() => {
  const firstDay = new Date(Date.UTC(selectedYear.value, selectedMonth.value - 1, 1))
  const startOffset = firstDay.getUTCDay()
  const daysInMonth = new Date(Date.UTC(selectedYear.value, selectedMonth.value, 0)).getUTCDate()
  const previousMonthDays = new Date(
    Date.UTC(selectedYear.value, selectedMonth.value - 1, 0),
  ).getUTCDate()

  return Array.from({ length: 42 }, (_, index) => {
    const relativeDay = index - startOffset + 1
    const isCurrentMonth = relativeDay >= 1 && relativeDay <= daysInMonth
    const day =
      relativeDay < 1
        ? previousMonthDays + relativeDay
        : relativeDay > daysInMonth
          ? relativeDay - daysInMonth
          : relativeDay
    const date = isCurrentMonth
      ? `${selectedYear.value}-${String(selectedMonth.value).padStart(2, '0')}-${String(day).padStart(2, '0')}`
      : null
    return {
      key: `${selectedYear.value}-${selectedMonth.value}-${index}`,
      day,
      date,
      isCurrentMonth,
      count: date ? (dateCounts.value.get(date) ?? 0) : 0,
    }
  })
})
const filteredHistory = computed(() =>
  selectedDate.value
    ? store.history.filter((item) => item.date === selectedDate.value)
    : store.history,
)
const totalHearts = computed(() =>
  store.history.reduce((total, item) => total + item.heartedPlaceCount, 0),
)
const totalPlacesVisited = computed(() =>
  store.history.reduce((total, item) => total + item.totalPlaceCount, 0),
)
const postsByCourseId = computed(
  () =>
    new Map(
      store.rankings
        .filter((post) => post.authorNickname === store.name)
        .map((post) => [post.courseId, post]),
    ),
)

function showInfo() {
  store.triggerToast('완료한 데이트가 날짜별로 캘린더에 기록돼요.')
}

async function refreshHistory() {
  if (refreshing.value) return
  refreshing.value = true
  const startedAt = Date.now()
  await Promise.all([
    store.loadHistory({
      year: selectedYear.value,
      month: selectedMonth.value,
      page: 1,
      size: 50,
    }),
    store.loadRankings(),
  ])
  const remainingDuration = 600 - (Date.now() - startedAt)
  if (remainingDuration > 0) await new Promise((resolve) => setTimeout(resolve, remainingDuration))
  refreshing.value = false
}

function changeMonth(offset: number) {
  const next = new Date(Date.UTC(selectedYear.value, selectedMonth.value - 1 + offset, 1))
  selectedYear.value = next.getUTCFullYear()
  selectedMonth.value = next.getUTCMonth() + 1
  selectedDate.value = null
  void refreshHistory()
  scrollArea.value?.scrollTo({ top: 0, behavior: 'smooth' })
}

function selectCalendarDate(date: string | null, count: number) {
  if (!date || count === 0) return
  selectedDate.value = selectedDate.value === date ? null : date
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

onMounted(() => {
  void refreshHistory()
})
</script>

<template>
  <div class="history-view">
    <PageHeader eyebrow="OUR MEMORY" title="우리의 추억">
      <button class="info-btn" aria-label="추억 캘린더 안내" @click="showInfo">✦</button>
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
        {{ refreshing ? '추억을 새로 불러오는 중…' : '놓으면 새로고침' }}
      </div>

      <BaseCard class="summary-card">
        <div>
          <strong>{{ store.history.length }}</strong>
          <span>이번 달 데이트</span>
        </div>
        <div>
          <strong>{{ totalPlacesVisited }}</strong>
          <span>방문한 장소</span>
        </div>
        <div>
          <strong>{{ totalHearts }}</strong>
          <span>남긴 장소 하트</span>
        </div>
      </BaseCard>

      <BaseCard class="calendar-card">
        <div class="calendar-head">
          <button aria-label="이전 달" @click="changeMonth(-1)">‹</button>
          <div>
            <span>MEMORY CALENDAR</span>
            <h3>{{ monthLabel }}</h3>
          </div>
          <button aria-label="다음 달" @click="changeMonth(1)">›</button>
        </div>
        <div class="weekdays" aria-hidden="true">
          <span>일</span><span>월</span><span>화</span><span>수</span><span>목</span><span>금</span
          ><span>토</span>
        </div>
        <div class="calendar-grid">
          <button
            v-for="day in calendarDays"
            :key="day.key"
            type="button"
            :disabled="!day.isCurrentMonth || day.count === 0"
            :class="{
              outside: !day.isCurrentMonth,
              recorded: day.count > 0,
              selected: day.date !== null && selectedDate === day.date,
            }"
            :aria-label="day.date ? `${day.date}, 데이트 ${day.count}건` : undefined"
            @click="selectCalendarDate(day.date, day.count)"
          >
            <span>{{ day.day }}</span>
            <i v-if="day.count > 0">{{ day.count > 1 ? day.count : '♥' }}</i>
          </button>
        </div>
        <p class="calendar-help">하트가 있는 날짜를 누르면 그날의 추억만 볼 수 있어요.</p>
      </BaseCard>

      <div class="list-header">
        <div>
          <span>COMPLETED DATES</span>
          <strong>{{
            selectedDate
              ? `${selectedDate.slice(5).replace('-', '월 ')}일의 기록`
              : `${monthLabel} 완료한 데이트`
          }}</strong>
        </div>
        <button v-if="selectedDate" @click="selectedDate = null">전체 보기</button>
        <em v-else>{{ filteredHistory.length }}건</em>
      </div>

      <div v-if="filteredHistory.length" class="hlist">
        <BaseCard v-for="item in filteredHistory" :key="item.courseId" class="history-card">
          <div class="hhead">
            <div class="date-badge">
              <strong>{{ item.date.slice(-2) }}</strong>
              <span>DAY</span>
            </div>
            <div class="history-main">
              <span class="label">{{ formatDistrict(item.mainDistrict) }}</span>
              <h3>{{ item.courseTitle }}</h3>
              <p>{{ item.totalPlaceCount }}개 장소 · 하트 {{ item.heartedPlaceCount }}개</p>
            </div>
            <span class="completed-badge">완료</span>
          </div>
          <div class="hcomment">“{{ item.oneLineComment ?? '남긴 코멘트가 없어요.' }}”</div>
          <div v-if="postsByCourseId.has(item.courseId)" class="post-actions">
            <button @click="editPost(item.courseId, item.oneLineComment ?? '')">게시글 수정</button>
            <button class="delete" @click="deletePost(item.courseId)">게시글 삭제</button>
          </div>
        </BaseCard>
      </div>
      <BaseCard v-else class="history-empty">
        <div>💌</div>
        <strong>{{
          selectedDate ? '이 날짜에는 완료한 데이트가 없어요.' : '이번 달에는 아직 추억이 없어요.'
        }}</strong>
        <p>데이트를 완료하면 이곳에 날짜와 코스가 자동으로 기록돼요.</p>
      </BaseCard>
    </div>
  </div>
</template>

<style scoped>
.history-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #fffaf7 0%, #fff7f9 55%, #f7f3ff 100%);
}

.info-btn {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border-radius: 13px;
  background: #fff;
  box-shadow: 0 8px 18px rgba(91, 61, 68, 0.1);
  color: #bd6580;
  font-weight: 900;
}

.pull-indicator {
  display: grid;
  place-items: center;
  overflow: hidden;
  color: var(--muted);
  font-size: 9px;
  font-weight: 800;
  transition: height 0.15s ease;
}

.pull-indicator.visible {
  padding: 15px 0;
}

.summary-card {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  margin-top: 15px;
  padding: 15px 12px;
  border: 1px solid rgba(240, 211, 222, 0.72);
  background:
    radial-gradient(circle at 92% 4%, rgba(255, 255, 255, 0.8), transparent 25%),
    linear-gradient(135deg, #ffe5eb, #eee7ff);
  box-shadow: 0 13px 28px rgba(103, 68, 88, 0.11);
}

.summary-card div {
  text-align: center;
}

.summary-card div + div {
  border-left: 1px solid rgba(85, 61, 68, 0.12);
}

.summary-card strong {
  display: block;
  font-size: 19px;
  font-weight: 900;
}

.summary-card span {
  color: var(--muted);
  font-size: 8px;
}

.calendar-card {
  margin-top: 12px;
  padding: 16px;
  border: 1px solid rgba(232, 221, 229, 0.88);
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 13px 28px rgba(83, 58, 68, 0.08);
}

.calendar-head {
  display: grid;
  grid-template-columns: 34px 1fr 34px;
  align-items: center;
  text-align: center;
}

.calendar-head button {
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  border-radius: 11px;
  background: #f7f1f4;
  color: #a86579;
  font-size: 20px;
}

.calendar-head span {
  color: #ba7188;
  font-size: 7px;
  font-weight: 900;
  letter-spacing: 0.13em;
}

.calendar-head h3 {
  margin: 3px 0 0;
  font-size: 16px;
  font-weight: 900;
}

.weekdays,
.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
}

.weekdays {
  margin-top: 15px;
  padding-bottom: 7px;
  border-bottom: 1px solid #f1e8e9;
  color: var(--muted);
  font-size: 8px;
  font-weight: 800;
  text-align: center;
}

.weekdays span:first-child {
  color: #d96b7f;
}

.weekdays span:last-child {
  color: #7c78b8;
}

.calendar-grid {
  row-gap: 4px;
  margin-top: 7px;
}

.calendar-grid button {
  position: relative;
  height: 34px;
  display: grid;
  place-items: center;
  border-radius: 11px;
  color: #66575a;
  font-size: 9px;
  font-weight: 800;
}

.calendar-grid button.outside {
  color: #d8ced0;
}

.calendar-grid button.recorded {
  background: linear-gradient(145deg, #fff0f3, #f2ebff);
  color: #c2536c;
  cursor: pointer;
}

.calendar-grid button.selected {
  background: linear-gradient(145deg, var(--pink), #a487dc);
  box-shadow: 0 7px 14px rgba(207, 92, 132, 0.22);
  color: #fff;
}

.calendar-grid i {
  position: absolute;
  right: 3px;
  bottom: 2px;
  color: inherit;
  font-size: 6px;
  font-style: normal;
  font-weight: 900;
}

.calendar-help {
  margin: 10px 0 0;
  color: var(--muted);
  font-size: 8px;
  text-align: center;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 10px;
  padding: 18px 3px 9px;
}

.list-header span {
  display: block;
  color: #b26d84;
  font-size: 7px;
  font-weight: 900;
  letter-spacing: 0.12em;
}

.list-header strong {
  display: block;
  margin-top: 3px;
  font-size: 13px;
}

.list-header em,
.list-header button {
  padding: 6px 9px;
  border-radius: 999px;
  background: #fff;
  color: #a7667b;
  box-shadow: 0 5px 12px rgba(92, 61, 70, 0.06);
  font-size: 8px;
  font-style: normal;
  font-weight: 900;
}

.hlist {
  display: grid;
  gap: 10px;
}

.history-card {
  padding: 14px;
  border: 1px solid rgba(235, 224, 226, 0.82);
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 10px 24px rgba(86, 57, 64, 0.08);
}

.hhead {
  display: grid;
  grid-template-columns: 46px 1fr auto;
  gap: 11px;
  align-items: center;
}

.date-badge {
  width: 46px;
  height: 46px;
  display: grid;
  align-content: center;
  justify-items: center;
  border-radius: 15px;
  background: linear-gradient(145deg, #ffe2e9, #eee5ff);
  color: #cf5871;
}

.date-badge strong {
  font-size: 15px;
  line-height: 1;
}

.date-badge span {
  margin-top: 3px;
  font-size: 6px;
  font-weight: 900;
  letter-spacing: 0.08em;
}

.history-main {
  min-width: 0;
}

.label {
  display: block;
  color: #e75d74;
  font-size: 9px;
  font-weight: 900;
}

.history-card h3 {
  margin: 3px 0 4px;
  overflow: hidden;
  font-size: 14px;
  font-weight: 900;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-card p {
  margin: 0;
  color: var(--muted);
  font-size: 8px;
}

.completed-badge {
  padding: 5px 7px;
  border-radius: 999px;
  background: #e8f5ef;
  color: #4f826d;
  font-size: 7px;
  font-weight: 900;
}

.hcomment {
  margin-top: 10px;
  padding: 10px;
  border-radius: 12px;
  background: linear-gradient(135deg, #fff7f8, #f8f4ff);
  color: #6f5b5f;
  font-size: 10px;
  line-height: 1.5;
}

.post-actions {
  display: flex;
  justify-content: flex-end;
  gap: 6px;
  margin-top: 8px;
}

.post-actions button {
  padding: 6px 8px;
  border-radius: 8px;
  background: #f3eceb;
  color: #66575a;
  font-size: 8px;
  font-weight: 800;
}

.post-actions .delete {
  background: #ffebeb;
  color: #c84d61;
}

.history-empty {
  display: grid;
  justify-items: center;
  gap: 6px;
  padding: 28px 18px;
  border: 1px dashed #e6d6db;
  background: rgba(255, 255, 255, 0.78);
  text-align: center;
}

.history-empty div {
  font-size: 28px;
}

.history-empty strong {
  font-size: 12px;
}

.history-empty p {
  margin: 0;
  color: var(--muted);
  font-size: 9px;
}
</style>
