import { defineStore } from 'pinia'
import { ref } from 'vue'
import { chatService } from '@/services/chatService'
import { communityService } from '@/services/communityService'
import { courseService } from '@/services/courseService'
import { historyService } from '@/services/historyService'
import { identityService } from '@/services/identityService'
import { rankingService } from '@/services/rankingService'
import { weatherService } from '@/services/weatherService'
import type { AuthenticatedApiHeaders, PageMetaDto } from '@/types/api/common'
import type {
  CommunityPostDetailDto,
  CommunityPostSummaryDto,
  DateMasterDto,
} from '@/types/api/community'
import type { DateCourseDto, HistoryCourseSummaryDto, WeatherSummaryDto } from '@/types/api/course'
import type { CourseEditAction, CreateChatSessionRequestDto } from '@/types/api/chat'

type SurveyKey = 'pref' | 'mood' | 'density' | 'move'

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
  '✨ 상관없어요': 'FLEXIBLE',
}
const densityByOption: Record<string, CreateChatSessionRequestDto['scheduleDensity']> = {
  '⚡ 타이트하게': 'TIGHT',
  '☁️ 널널하게': 'RELAXED',
}
const timeBySlot: Record<CreateChatSessionRequestDto['timeSlot'], string> = {
  MORNING: '09:00',
  AFTERNOON: '14:00',
  FULL_DAY: '10:00',
}

function defaultCourseSchedule() {
  return { date: todayInSeoul(), startTime: '10:00' }
}

function todayInSeoul(referenceDate = new Date()) {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Seoul',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(referenceDate)
  const value = (type: string) => parts.find((part) => part.type === type)?.value ?? ''
  return `${value('year')}-${value('month')}-${value('day')}`
}

export const useDateStore = defineStore('dateStore', () => {
  const authMode = ref<'enter' | 'register'>('enter')
  const name = ref('')
  const profileId = ref<string | null>(null)
  const password = ref<string | null>(null)
  const surveyDone = ref(false)
  const surveyStep = ref(0)
  const surveyAnswers = ref<Record<SurveyKey, string[]>>({
    pref: [],
    mood: [],
    density: [],
    move: [],
  })
  const defaultSchedule = defaultCourseSchedule()
  const courseDate = ref(defaultSchedule.date)
  const startTime = ref(defaultSchedule.startTime)
  const timeSlot = ref<CreateChatSessionRequestDto['timeSlot'] | null>('FULL_DAY')
  const serverClockOffsetMs = ref(0)

  const minimumCourseDate = ref(defaultSchedule.date)

  const district = ref<CreateChatSessionRequestDto['district']>('YUSEONG_GU')
  const spaceType = ref<CreateChatSessionRequestDto['spaceType']>('ANY')
  const showSurvey = ref(false)
  const showCommentModal = ref(false)
  const toastMessage = ref('')
  const toastVisible = ref(false)
  const loading = ref(false)
  const chatLoading = ref(false)
  const sessionId = ref<string | null>(null)
  const draftId = ref<string | null>(null)
  const draftVersion = ref<number | null>(null)
  const course = ref<{
    title: string
    places: string[]
    coords: [number, number][]
    images: Array<string | null>
    weather: WeatherSummaryDto | null
  }>({
    title: '',
    places: [],
    coords: [],
    images: [],
    weather: null,
  })
  const messages = ref<Array<{ role: 'bot' | 'user'; content: string }>>([])
  const activeCourse = ref<DateCourseDto | null>(null)
  const todayWeather = ref<WeatherSummaryDto | null>(null)
  const weatherLoading = ref(false)
  const rankings = ref<CommunityPostSummaryDto[]>([])
  const featuredRankings = ref<CommunityPostSummaryDto[]>([])
  const rankingMeta = ref<PageMetaDto | null>(null)
  const masters = ref<DateMasterDto[]>([])
  const selectedCommunityCourse = ref<CommunityPostDetailDto | null>(null)
  const history = ref<HistoryCourseSummaryDto[]>([])

  function serverNow() {
    return new Date(Date.now() + serverClockOffsetMs.value)
  }

  function refreshServerDateBoundaries() {
    const currentServerTime = serverNow()
    minimumCourseDate.value = todayInSeoul(currentServerTime)
  }

  function syncServerClock(timestamp: string) {
    const serverTimestamp = Date.parse(timestamp)
    if (Number.isFinite(serverTimestamp)) serverClockOffsetMs.value = serverTimestamp - Date.now()
    refreshServerDateBoundaries()
  }

  function isTimeSlotUnavailable(
    value: CreateChatSessionRequestDto['timeSlot'],
    date = courseDate.value,
  ) {
    if (date < minimumCourseDate.value) return true
    if (date > minimumCourseDate.value) return false
    const scheduledAt = Date.parse(`${date}T${timeBySlot[value]}:00+09:00`)
    return scheduledAt <= serverNow().getTime()
  }

  function selectCourseDate(value: string) {
    if (value < minimumCourseDate.value) return false
    courseDate.value = value

    const candidates: CreateChatSessionRequestDto['timeSlot'][] = [
      ...(timeSlot.value ? [timeSlot.value] : []),
      'FULL_DAY',
      'AFTERNOON',
      'MORNING',
    ]
    const availableSlot = [...new Set(candidates)].find(
      (candidate) => !isTimeSlotUnavailable(candidate, value),
    )
    if (availableSlot) {
      timeSlot.value = availableSlot
      startTime.value = timeBySlot[availableSlot]
    } else {
      timeSlot.value = null
      startTime.value = ''
    }
    return true
  }

  const surveyStepsList: Array<{
    emoji: string
    title: string
    desc: string
    key?: SurveyKey
    opts?: string[]
    single?: boolean
    kind?: 'datetime' | 'location'
  }> = [
    {
      emoji: '📅',
      title: '언제 만날까요?',
      desc: '날짜와 서버 시간 이후의 시간대를 골라 주세요.',
      kind: 'datetime',
    },
    {
      emoji: '📍',
      title: '데이트 지역과 공간',
      desc: '이동 동선과 날씨를 반영할게요.',
      kind: 'location',
    },
    {
      emoji: '🎨',
      title: '선호하는 데이트는?',
      desc: '여러 개 골라도 괜찮아요.',
      key: 'pref',
      opts: Object.keys(activityByOption),
    },
    {
      emoji: '💭',
      title: '좋아하는 분위기는?',
      desc: '둘 사이의 공통점을 찾아볼게요.',
      key: 'mood',
      opts: Object.keys(moodByOption),
    },
    {
      emoji: '⏱️',
      title: '오늘 일정은?',
      desc: '코스 간 이동과 머무는 시간을 조절해요.',
      key: 'density',
      single: true,
      opts: Object.keys(densityByOption),
    },
    {
      emoji: '🚌',
      title: '이동 방식 선택',
      desc: '장소 사이의 거리를 조절해요.',
      key: 'move',
      single: true,
      opts: Object.keys(transportationByOption),
    },
  ]

  function triggerToast(message: string) {
    toastMessage.value = message
    toastVisible.value = true
    window.setTimeout(() => {
      toastVisible.value = false
    }, 2200)
  }

  function authHeaders(): AuthenticatedApiHeaders {
    if (!profileId.value || !password.value) throw new Error('다시 로그인해 주세요.')
    return { 'X-Profile-Id': profileId.value, 'X-User-Password': password.value }
  }

  function applyDraft(draft: {
    draftId: string
    version: number
    title: string
    places: Array<{
      place: {
        name: string
        latitude: number | null
        longitude: number | null
        imageUrl: string | null
      }
    }>
    weather: WeatherSummaryDto | null
  }) {
    draftId.value = draft.draftId
    draftVersion.value = draft.version
    course.value = {
      title: draft.title,
      places: draft.places.map((item) => item.place.name),
      coords: draft.places.flatMap((item) =>
        item.place.latitude !== null && item.place.longitude !== null
          ? [[item.place.latitude, item.place.longitude] as [number, number]]
          : [],
      ),
      images: draft.places.map((item) => item.place.imageUrl),
      weather: draft.weather,
    }
  }

  function applyActiveCourse(active: DateCourseDto) {
    course.value = {
      title: active.title,
      places: active.places.map((item) => item.place.name),
      coords: active.places.flatMap((item) =>
        item.place.latitude !== null && item.place.longitude !== null
          ? [[item.place.latitude, item.place.longitude] as [number, number]]
          : [],
      ),
      images: active.places.map((item) => item.place.imageUrl),
      weather: active.weather,
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
        ? await identityService.createProfile({
            nickname: nickname.trim(),
            password: inputPassword,
          })
        : await identityService.verifyProfile({
            nickname: nickname.trim(),
            password: inputPassword,
          })
      syncServerClock(response.timestamp)
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
    } finally {
      loading.value = false
    }
  }

  const register = (nickname: string, inputPassword: string) =>
    authenticate(nickname, inputPassword, true)
  const login = (nickname: string, inputPassword: string) =>
    authenticate(nickname, inputPassword, false)

  function logout() {
    name.value = ''
    profileId.value = null
    password.value = null
    surveyDone.value = false
    sessionId.value = null
    draftId.value = null
    draftVersion.value = null
    course.value = { title: '', places: [], coords: [], images: [], weather: null }
    todayWeather.value = null
    messages.value = []
    activeCourse.value = null
    authMode.value = 'enter'
    serverClockOffsetMs.value = 0
    refreshServerDateBoundaries()
    triggerToast('로그아웃 되었습니다 👋')
  }

  async function fetchChatSession() {
    if (!sessionId.value) return
    try {
      const response = await chatService.getSession(sessionId.value, authHeaders())
      if (!response.data.draft) return
      messages.value = response.data.messages.map((message) => ({
        role: message.role === 'ASSISTANT' ? 'bot' : 'user',
        content: message.content,
      }))
      applyDraft(response.data.draft)
    } catch (error) {
      if (error instanceof Error) triggerToast(error.message)
    }
  }

  function toggleSurveyOption(key: SurveyKey, option: string) {
    const step = surveyStepsList[surveyStep.value]!
    if (step.single) surveyAnswers.value[key] = [option]
    else
      surveyAnswers.value[key] = surveyAnswers.value[key].includes(option)
        ? surveyAnswers.value[key].filter((item) => item !== option)
        : [...surveyAnswers.value[key], option]
  }

  function selectTimeSlot(value: CreateChatSessionRequestDto['timeSlot']) {
    if (isTimeSlotUnavailable(value)) return false
    timeSlot.value = value
    startTime.value = timeBySlot[value]
    return true
  }

  async function createChatSession() {
    const activities = [
      ...new Set(
        surveyAnswers.value.pref
          .map((value) => activityByOption[value])
          .filter((value): value is NonNullable<typeof value> => value !== undefined),
      ),
    ]
    const moods = [
      ...new Set(
        surveyAnswers.value.mood
          .map((value) => moodByOption[value])
          .filter((value): value is NonNullable<typeof value> => value !== undefined),
      ),
    ]
    const transportation = transportationByOption[surveyAnswers.value.move[0] ?? '']
    const scheduleDensity = densityByOption[surveyAnswers.value.density[0] ?? '']
    const selectedTimeSlot = timeSlot.value
    if (
      !activities.length ||
      !moods.length ||
      !transportation ||
      !scheduleDensity ||
      !selectedTimeSlot
    )
      throw new Error('설문 항목을 모두 선택해 주세요.')

    refreshServerDateBoundaries()
    if (courseDate.value < minimumCourseDate.value || isTimeSlotUnavailable(selectedTimeSlot)) {
      timeSlot.value = null
      startTime.value = ''
      surveyStep.value = 0
      throw new Error('선택한 시간대가 지났어요. 날짜와 시간대를 다시 선택해 주세요.')
    }

    const response = await chatService.createSession(
      {
        date: courseDate.value,
        timeSlot: selectedTimeSlot,
        startTime: startTime.value,
        district: district.value,
        spaceType: spaceType.value,
        moods,
        activities,
        scheduleDensity,
        transportation,
      },
      authHeaders(),
    )
    sessionId.value = response.data.id
    messages.value = [{ role: 'bot', content: response.data.assistantMessage.content }]
    applyDraft(response.data.draft)
    if (!response.data.draft.weather?.available) {
      const weather = await weatherService.getWeatherWithRetry({
        date: courseDate.value,
        district: district.value,
        timeSlot: 'AFTERNOON',
      })
      if (weather) course.value.weather = weather
    }
  }

  async function nextSurveyStep() {
    const step = surveyStepsList[surveyStep.value]!

    if (step.kind === 'datetime') {
      refreshServerDateBoundaries()
      if (!courseDate.value || !timeSlot.value || !startTime.value)
        return triggerToast('날짜와 이용 가능한 시간대를 선택해 주세요.')
      if (courseDate.value < minimumCourseDate.value)
        return triggerToast('데이트 날짜는 오늘부터 선택할 수 있어요.')
      if (isTimeSlotUnavailable(timeSlot.value)) {
        timeSlot.value = null
        startTime.value = ''
        return triggerToast('서버 시간 기준 이미 지난 시간대예요. 다른 시간대를 선택해 주세요.')
      }
    }
    if (step.key && !surveyAnswers.value[step.key].length)
      return triggerToast('하나 이상 선택해 주세요.')
    if (surveyStep.value < surveyStepsList.length - 1) {
      surveyStep.value += 1
      return
    }
    loading.value = true
    try {
      await createChatSession()
      surveyDone.value = true
      showSurvey.value = false
      triggerToast('취향을 반영한 첫 코스를 만들었어요.')
    } catch (error) {
      triggerToast(error instanceof Error ? error.message : '코스 생성에 실패했습니다.')
    } finally {
      loading.value = false
    }
  }
  function prevSurveyStep() {
    if (surveyStep.value > 0) surveyStep.value -= 1
  }

  function startNewCourseSetup() {
    surveyStep.value = 0
    surveyDone.value = false
    surveyAnswers.value = { pref: [], mood: [], density: [], move: [] }
    refreshServerDateBoundaries()
    timeSlot.value = 'FULL_DAY'
    startTime.value = timeBySlot.FULL_DAY
    selectCourseDate(minimumCourseDate.value)
    sessionId.value = null
    draftId.value = null
    draftVersion.value = null
    course.value = { title: '', places: [], coords: [], images: [], weather: null }
    messages.value = []
    showSurvey.value = true
  }

  function closeSurvey() {
    showSurvey.value = false
    surveyStep.value = 0
  }

  async function sendChatMessage(message: string) {
    if (!message.trim() || chatLoading.value) return
    if (!sessionId.value || !draftVersion.value) {
      triggerToast('먼저 성향 조사를 완료하고 AI 코스를 만들어 주세요.')
      return
    }
    chatLoading.value = true
    try {
      const response = await chatService.sendMessage(
        sessionId.value,
        { message, expectedDraftVersion: draftVersion.value },
        authHeaders(),
      )
      messages.value.push(
        { role: 'user', content: response.data.userMessage.content },
        { role: 'bot', content: response.data.assistantMessage.content },
      )
      applyDraft(response.data.draft)
    } catch (error) {
      triggerToast(error instanceof Error ? error.message : '메시지 전송에 실패했습니다.')
    } finally {
      chatLoading.value = false
    }
  }

  async function sendQuickAction(quickAction: CourseEditAction) {
    if (chatLoading.value) return
    if (!sessionId.value || !draftVersion.value) {
      triggerToast('먼저 성향 조사를 완료하고 AI 코스를 만들어 주세요.')
      return
    }
    chatLoading.value = true
    try {
      const response = await chatService.sendMessage(
        sessionId.value,
        { quickAction, expectedDraftVersion: draftVersion.value },
        authHeaders(),
      )
      messages.value.push(
        { role: 'user', content: response.data.userMessage.content },
        { role: 'bot', content: response.data.assistantMessage.content },
      )
      applyDraft(response.data.draft)
      if (!response.data.changed)
        triggerToast(response.data.warnings[0] ?? '현재 코스를 유지했어요.')
    } catch (error) {
      triggerToast(error instanceof Error ? error.message : '코스 수정에 실패했습니다.')
    } finally {
      chatLoading.value = false
    }
  }

  async function decideCourse() {
    if (!sessionId.value || !draftId.value || !draftVersion.value) return
    loading.value = true
    try {
      const response = await chatService.confirmSession(
        sessionId.value,
        { draftId: draftId.value, expectedVersion: draftVersion.value },
        authHeaders(),
      )
      activeCourse.value = response.data
      triggerToast('오늘의 데이트 코스로 등록했어요 💗')
      return true
    } catch (error) {
      triggerToast(error instanceof Error ? error.message : '코스 확정에 실패했습니다.')
      return false
    } finally {
      loading.value = false
    }
  }

  async function loadCurrentCourse() {
    try {
      const currentCourse = (await courseService.getCurrentCourse(authHeaders())).data
      activeCourse.value = currentCourse
      if (currentCourse) applyActiveCourse(currentCourse)
    } catch (error) {
      if (error instanceof Error && !error.message.includes('다시 로그인'))
        triggerToast(error.message)
    }
  }
  async function loadTodayWeather() {
    if (weatherLoading.value) return
    weatherLoading.value = true
    try {
      todayWeather.value = await weatherService.getWeatherWithRetry({
        date: todayInSeoul(),
        district: 'ANY',
        timeSlot: 'FULL_DAY',
      })
    } catch {
      todayWeather.value = null
    } finally {
      weatherLoading.value = false
    }
  }
  async function togglePlaceLike(coursePlaceId: string, hearted: boolean) {
    try {
      const response = hearted
        ? await courseService.unheartCoursePlace(coursePlaceId, authHeaders())
        : await courseService.heartCoursePlace(coursePlaceId, authHeaders())
      if (activeCourse.value && response.data)
        activeCourse.value.places = activeCourse.value.places.map((place) =>
          place.coursePlaceId === coursePlaceId
            ? {
                ...place,
                heartedByMe: response.data!.heartedByMe,
                heartCount: response.data!.heartCount,
              }
            : place,
        )
    } catch (error) {
      triggerToast(error instanceof Error ? error.message : '좋아요 처리에 실패했습니다.')
    }
  }
  async function nextPlace(coursePlaceId: string) {
    try {
      await courseService.completeCoursePlace(coursePlaceId, authHeaders())
      await loadCurrentCourse()
    } catch (error) {
      triggerToast(error instanceof Error ? error.message : '장소 완료 처리에 실패했습니다.')
    }
  }
  async function submitReview(oneLineComment: string) {
    try {
      await courseService.completeCurrentCourse({ oneLineComment }, authHeaders())
      activeCourse.value = null
      sessionId.value = null
      draftId.value = null
      draftVersion.value = null
      course.value = { title: '', places: [], coords: [], images: [], weather: null }
      messages.value = []
      surveyDone.value = false
      showCommentModal.value = false
      triggerToast('데이트가 추억으로 저장됐어요 💌')
      return true
    } catch (error) {
      triggerToast(error instanceof Error ? error.message : '데이트 종료에 실패했습니다.')
      return false
    }
  }
  async function loadRankings(page?: number, sort: 'POPULAR' | 'LATEST' = 'POPULAR') {
    try {
      const headers = profileId.value && password.value ? authHeaders() : undefined
      const params = page === undefined ? { sort, page: 1, size: 50 } : { sort, page, size: 5 }
      const response = await communityService.listPosts(params, headers)
      rankings.value = response.data ?? []
      rankingMeta.value = response.meta
    } catch (error) {
      triggerToast(error instanceof Error ? error.message : '랭킹을 불러오지 못했습니다.')
    }
  }
  async function loadFeaturedRankings() {
    try {
      const headers = profileId.value && password.value ? authHeaders() : undefined
      const response = await communityService.listPosts(
        { sort: 'POPULAR', page: 1, size: 3 },
        headers,
      )
      featuredRankings.value = [...(response.data ?? [])].sort(
        (a, b) =>
          b.courseLikeCount - a.courseLikeCount ||
          b.publishedAt.localeCompare(a.publishedAt) ||
          a.postId.localeCompare(b.postId),
      )
    } catch (error) {
      triggerToast(
        error instanceof Error ? error.message : '실시간 인기 코스를 불러오지 못했습니다.',
      )
    }
  }
  async function likeRankItem(postId: string, liked: boolean, page = 1) {
    try {
      await (liked
        ? communityService.unlikePost(postId, authHeaders())
        : communityService.likePost(postId, authHeaders()))
      await loadRankings(page)
      await loadFeaturedRankings()
    } catch (error) {
      triggerToast(error instanceof Error ? error.message : '좋아요 처리에 실패했습니다.')
    }
  }
  async function updateCommunityPost(postId: string, oneLineComment: string) {
    if (!oneLineComment.trim()) return false
    try {
      await communityService.updatePost(
        postId,
        { oneLineComment: oneLineComment.trim() },
        authHeaders(),
      )
      rankings.value = rankings.value.map((item) =>
        item.postId === postId ? { ...item, oneLineComment: oneLineComment.trim() } : item,
      )
      triggerToast('한 줄 코멘트를 수정했어요.')
      return true
    } catch (error) {
      triggerToast(error instanceof Error ? error.message : '게시글 수정에 실패했습니다.')
      return false
    }
  }
  async function deleteCommunityPost(postId: string) {
    try {
      await communityService.deletePost(postId, authHeaders())
      rankings.value = rankings.value.filter((item) => item.postId !== postId)
      triggerToast('랭킹보드에서 게시글을 삭제했어요.')
      return true
    } catch (error) {
      triggerToast(error instanceof Error ? error.message : '게시글 삭제에 실패했습니다.')
      return false
    }
  }
  async function startCommunityCourse(postId: string) {
    loading.value = true
    try {
      const response = await communityService.startPost(
        postId,
        { date: courseDate.value, startTime: startTime.value },
        authHeaders(),
      )
      if (!response.data) throw new Error('시작한 코스 정보를 받지 못했습니다.')
      activeCourse.value = response.data.activeCourse
      triggerToast('선택한 코스를 현재 데이트로 시작했어요.')
      return true
    } catch (error) {
      triggerToast(error instanceof Error ? error.message : '코스 시작에 실패했습니다.')
      return false
    } finally {
      loading.value = false
    }
  }
  async function loadCommunityCourse(postId: string) {
    try {
      selectedCommunityCourse.value = (await communityService.getPost(postId)).data
    } catch (error) {
      triggerToast(error instanceof Error ? error.message : '코스 경로를 불러오지 못했습니다.')
    }
  }
  async function loadHistory(params?: {
    year?: number
    month?: number
    page?: number
    size?: number
  }) {
    try {
      history.value = (await historyService.listMyDateCourses(authHeaders(), params)).data ?? []
    } catch (error) {
      if (error instanceof Error && !error.message.includes('다시 로그인'))
        triggerToast(error.message)
    }
  }
  async function loadMasters() {
    try {
      masters.value = (await rankingService.getMasters(50)).data?.masters ?? []
    } catch (error) {
      triggerToast(error instanceof Error ? error.message : '마스터 랭킹을 불러오지 못했습니다.')
    }
  }

  return {
    authMode,
    name,
    profileId,
    surveyDone,
    surveyStep,
    surveyAnswers,
    surveyStepsList,
    courseDate,
    startTime,
    timeSlot,
    minimumCourseDate,
    refreshServerDateBoundaries,
    isTimeSlotUnavailable,
    selectCourseDate,

    district,
    spaceType,
    showSurvey,
    showCommentModal,
    toastMessage,
    toastVisible,
    loading,
    chatLoading,
    course,
    messages,
    activeCourse,
    todayWeather,
    weatherLoading,
    rankings,
    featuredRankings,
    rankingMeta,
    masters,
    selectedCommunityCourse,
    history,
    register,
    login,
    logout,
    fetchChatSession,
    toggleSurveyOption,
    selectTimeSlot,
    nextSurveyStep,
    prevSurveyStep,
    startNewCourseSetup,
    closeSurvey,
    sendChatMessage,
    sendQuickAction,
    decideCourse,
    loadCurrentCourse,
    loadTodayWeather,
    togglePlaceLike,
    nextPlace,
    submitReview,
    loadRankings,
    loadFeaturedRankings,
    likeRankItem,
    updateCommunityPost,
    deleteCommunityPost,
    startCommunityCourse,
    loadCommunityCourse,
    loadHistory,
    loadMasters,
    triggerToast,
  }
})
