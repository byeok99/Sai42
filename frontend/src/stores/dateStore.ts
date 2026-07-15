import { defineStore } from 'pinia'
import { ref } from 'vue'
import { chatService } from '@/services/chatService'
import { communityService } from '@/services/communityService'
import { courseService } from '@/services/courseService'
import { historyService } from '@/services/historyService'
import { identityService } from '@/services/identityService'
import { rankingService } from '@/services/rankingService'
import type { AuthenticatedApiHeaders } from '@/types/api/common'
import type { CommunityPostSummaryDto } from '@/types/api/community'
import type { DateCourseDto, HistoryCourseSummaryDto } from '@/types/api/course'
import type { CreateChatSessionRequestDto } from '@/types/api/chat'

type SurveyKey = 'pref' | 'mood' | 'move'

const activityByOption: Record<string, CreateChatSessionRequestDto['activities'][number]> = {
  '☕ 감성 카페': 'FOOD',
  '🌳 산책과 자연': 'WALK',
  '🖼️ 전시와 문화': 'CULTURE_EXHIBITION',
  '🍜 맛집 탐방': 'FOOD',
  '🎳 활동적인 체험': 'LEPORTS',
  '🌙 야경과 드라이브': 'TOURISM',
}
const moodByOption: Record<string, CreateChatSessionRequestDto['moods'][number]> = {
  '🌷 설레고 아기자기': 'EMOTIONAL',
  '🤎 조용하고 편안': 'QUIET',
  '📸 사진이 잘 나오는': 'EMOTIONAL',
  '✨ 새로운 자극': 'SPECIAL',
  '😆 웃기고 활동적': 'LIVELY',
  '🫧 아무 계획 없는 여유': 'QUIET',
}
const transportationByOption: Record<string, CreateChatSessionRequestDto['transportation']> = {
  '🚶 도보 중심': 'WALK',
  '🚌 대중교통': 'PUBLIC_TRANSIT',
  '🚗 자가용': 'CAR',
  '🎲 그날그날 달라요': 'FLEXIBLE',
}

function todaySeoul() {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Seoul',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(new Date())
}

export const useDateStore = defineStore('dateStore', () => {
  const authMode = ref<'enter' | 'register'>('enter')
  const name = ref('')
  const profileId = ref<string | null>(null)
  const password = ref<string | null>(null)
  const surveyDone = ref(false)
  const surveyStep = ref(0)
  const surveyAnswers = ref<Record<SurveyKey, string[]>>({ pref: [], mood: [], move: [] })
  const showSurvey = ref(false)
  const showCommentModal = ref(false)
  const toastMessage = ref('')
  const toastVisible = ref(false)
  const loading = ref(false)
  const sessionId = ref<string | null>(null)
  const draftId = ref<string | null>(null)
  const draftVersion = ref<number | null>(null)
  const course = ref<{ title: string; places: string[]; coords: [number, number][] }>({
    title: '', places: [], coords: [],
  })
  const messages = ref<Array<{ role: 'bot' | 'user'; content: string }>>([])
  const activeCourse = ref<DateCourseDto | null>(null)
  const rankings = ref<CommunityPostSummaryDto[]>([])
  const history = ref<HistoryCourseSummaryDto[]>([])

  const surveyStepsList: Array<{ emoji: string; title: string; desc: string; key: SurveyKey; opts: string[]; single?: boolean }> = [
    { emoji: '🎨', title: '내가 선호하는 데이트는?', desc: '여러 개 골라도 괜찮아요.', key: 'pref', opts: Object.keys(activityByOption) },
    { emoji: '💭', title: '평소 좋아하는 분위기는?', desc: '둘 사이의 공통점을 찾아볼게요.', key: 'mood', opts: Object.keys(moodByOption) },
    { emoji: '🚌', title: '주로 어떻게 이동하나요?', desc: '장소 사이의 거리를 조절해요.', key: 'move', single: true, opts: Object.keys(transportationByOption) },
  ]

  function triggerToast(message: string) {
    toastMessage.value = message
    toastVisible.value = true
    window.setTimeout(() => { toastVisible.value = false }, 2200)
  }

  function authHeaders(): AuthenticatedApiHeaders {
    if (!profileId.value || !password.value) throw new Error('다시 로그인해 주세요.')
    return { 'X-Profile-Id': profileId.value, 'X-User-Password': password.value }
  }

  function applyDraft(draft: { draftId: string; version: number; title: string; places: Array<{ place: { name: string; latitude: number | null; longitude: number | null } }> }) {
    draftId.value = draft.draftId
    draftVersion.value = draft.version
    course.value = {
      title: draft.title,
      places: draft.places.map((item) => item.place.name),
      coords: draft.places.flatMap((item) => item.place.latitude !== null && item.place.longitude !== null ? [[item.place.latitude, item.place.longitude] as [number, number]] : []),
    }
  }

  async function authenticate(nickname: string, inputPassword: string, register: boolean) {
    if (!nickname.trim() || !/^\d{4}$/.test(inputPassword)) {
      triggerToast('닉네임과 숫자 4자리 비밀번호를 입력해 주세요.')
      return false
    }
    loading.value = true
    try {
      const response = register
        ? await identityService.createProfile({ nickname: nickname.trim(), password: inputPassword })
        : await identityService.verifyProfile({ nickname: nickname.trim(), password: inputPassword })
      if (!response.data) throw new Error('프로필 정보를 받지 못했습니다.')
      profileId.value = response.data.profileId
      password.value = inputPassword
      name.value = response.data.nickname
      surveyDone.value = false
      triggerToast(register ? '두 분의 사이42가 등록됐어요 💞' : '입장했습니다 💞')
      return true
    } catch (error) {
      triggerToast(error instanceof Error ? error.message : '인증에 실패했습니다.')
      return false
    } finally { loading.value = false }
  }

  const register = (nickname: string, inputPassword: string) => authenticate(nickname, inputPassword, true)
  const login = (nickname: string, inputPassword: string) => authenticate(nickname, inputPassword, false)

  function toggleSurveyOption(key: SurveyKey, option: string) {
    const step = surveyStepsList[surveyStep.value]!
    if (step.single) surveyAnswers.value[key] = [option]
    else surveyAnswers.value[key] = surveyAnswers.value[key].includes(option)
      ? surveyAnswers.value[key].filter((item) => item !== option)
      : [...surveyAnswers.value[key], option]
  }

  async function createChatSession() {
    const activities = [...new Set(surveyAnswers.value.pref.map((value) => activityByOption[value]).filter((value): value is NonNullable<typeof value> => value !== undefined))]
    const moods = [...new Set(surveyAnswers.value.mood.map((value) => moodByOption[value]).filter((value): value is NonNullable<typeof value> => value !== undefined))]
    const transportation = transportationByOption[surveyAnswers.value.move[0] ?? '']
    if (!activities.length || !moods.length || !transportation) throw new Error('설문 항목을 모두 선택해 주세요.')
    const response = await chatService.createSession({
      date: todaySeoul(), timeSlot: 'AFTERNOON', startTime: '14:00', district: 'YUSEONG_GU',
      spaceType: 'ANY', moods, activities, scheduleDensity: 'NORMAL', transportation,
    }, authHeaders())
    sessionId.value = response.data.id
    messages.value = [{ role: 'bot', content: response.data.assistantMessage.content }]
    applyDraft(response.data.draft)
  }

  async function nextSurveyStep() {
    const key = surveyStepsList[surveyStep.value]!.key
    if (!surveyAnswers.value[key].length) return triggerToast('하나 이상 선택해 주세요.')
    if (surveyStep.value < surveyStepsList.length - 1) { surveyStep.value += 1; return }
    loading.value = true
    try {
      await createChatSession()
      surveyDone.value = true
      showSurvey.value = false
      triggerToast('취향을 반영한 첫 코스를 만들었어요.')
    } catch (error) { triggerToast(error instanceof Error ? error.message : '코스 생성에 실패했습니다.') }
    finally { loading.value = false }
  }
  function prevSurveyStep() { if (surveyStep.value > 0) surveyStep.value -= 1 }

  async function sendChatMessage(message: string) {
    if (!message.trim() || !sessionId.value || !draftVersion.value) return
    loading.value = true
    try {
      const response = await chatService.sendMessage(sessionId.value, { message, expectedDraftVersion: draftVersion.value }, authHeaders())
      messages.value.push({ role: 'user', content: response.data.userMessage.content }, { role: 'bot', content: response.data.assistantMessage.content })
      applyDraft(response.data.draft)
    } catch (error) { triggerToast(error instanceof Error ? error.message : '메시지 전송에 실패했습니다.') }
    finally { loading.value = false }
  }

  async function decideCourse() {
    if (!sessionId.value || !draftId.value || !draftVersion.value) return
    loading.value = true
    try {
      const response = await chatService.confirmSession(sessionId.value, { draftId: draftId.value, expectedVersion: draftVersion.value }, authHeaders())
      activeCourse.value = response.data
      triggerToast('오늘의 데이트 코스로 등록했어요 💗')
      return true
    } catch (error) { triggerToast(error instanceof Error ? error.message : '코스 확정에 실패했습니다.'); return false }
    finally { loading.value = false }
  }

  async function loadCurrentCourse() {
    try { activeCourse.value = (await courseService.getCurrentCourse(authHeaders())).data } catch (error) { if (error instanceof Error && !error.message.includes('다시 로그인')) triggerToast(error.message) }
  }
  async function togglePlaceLike(coursePlaceId: string, hearted: boolean) {
    try {
      const response = hearted ? await courseService.unheartCoursePlace(coursePlaceId, authHeaders()) : await courseService.heartCoursePlace(coursePlaceId, authHeaders())
      if (activeCourse.value && response.data) activeCourse.value.places = activeCourse.value.places.map((place) => place.coursePlaceId === coursePlaceId ? { ...place, heartedByMe: response.data!.heartedByMe, heartCount: response.data!.heartCount } : place)
    } catch (error) { triggerToast(error instanceof Error ? error.message : '좋아요 처리에 실패했습니다.') }
  }
  async function nextPlace(coursePlaceId: string) { try { await courseService.completeCoursePlace(coursePlaceId, authHeaders()); await loadCurrentCourse() } catch (error) { triggerToast(error instanceof Error ? error.message : '장소 완료 처리에 실패했습니다.') } }
  async function submitReview(oneLineComment: string) {
    try { await courseService.completeCurrentCourse({ oneLineComment }, authHeaders()); activeCourse.value = null; showCommentModal.value = false; triggerToast('데이트가 추억으로 저장됐어요 💌') } catch (error) { triggerToast(error instanceof Error ? error.message : '데이트 종료에 실패했습니다.') }
  }
  async function loadRankings(sort: 'POPULAR' | 'LATEST' = 'POPULAR') { try { rankings.value = (await communityService.listPosts({ sort })).data ?? [] } catch (error) { triggerToast(error instanceof Error ? error.message : '랭킹을 불러오지 못했습니다.') } }
  async function likeRankItem(postId: string, liked: boolean) { try { const result = liked ? await communityService.unlikePost(postId, authHeaders()) : await communityService.likePost(postId, authHeaders()); if (result.data) rankings.value = rankings.value.map((item) => item.postId === postId ? { ...item, likedByMe: result.data!.likedByMe, courseLikeCount: result.data!.likeCount } : item) } catch (error) { triggerToast(error instanceof Error ? error.message : '좋아요 처리에 실패했습니다.') } }
  async function loadHistory() { try { history.value = (await historyService.listMyDateCourses(authHeaders())).data ?? [] } catch (error) { if (error instanceof Error && !error.message.includes('다시 로그인')) triggerToast(error.message) } }
  async function loadMasters() { return rankingService.getMasters() }

  return { authMode, name, profileId, surveyDone, surveyStep, surveyAnswers, surveyStepsList, showSurvey, showCommentModal, toastMessage, toastVisible, loading, course, messages, activeCourse, rankings, history, register, login, toggleSurveyOption, nextSurveyStep, prevSurveyStep, sendChatMessage, decideCourse, loadCurrentCourse, togglePlaceLike, nextPlace, submitReview, loadRankings, likeRankItem, loadHistory, loadMasters, triggerToast }
})
