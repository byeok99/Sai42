import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

import { identityService } from '@/services/identityService'
import { communityService } from '@/services/communityService'
import { courseService } from '@/services/courseService'
import { chatService } from '@/services/chatService'
import { historyService } from '@/services/historyService'

export interface Course {
  title: string
  places: string[]
  coords: [number, number][]
  fest: boolean
  weather?: any
}

export interface ActiveCourse {
  title: string
  places: string[]
  coords: [number, number][]
  likes: Record<number, boolean>
}

export interface RankItem {
  id: string
  title: string
  places: string[]
  comment: string
  creator: string
  use: number
  likes: number
  rating: number
  theme?: string
}

export interface HistoryItem {
  date: string
  title: string
  comment: string
  rating: number
  places: string[]
}

export const useDateStore = defineStore('dateStore', () => {
  // Authentication & Profile
  const authMode = ref<'enter' | 'register'>('enter')
  const name = ref(localStorage.getItem('sai42_name') || '')
  const profileId = ref(localStorage.getItem('sai42_profileId') || '')
  const profilePw = ref(localStorage.getItem('sai42_pw') || '')
  const isDemo = ref(false)

  const authHeaders = computed(() => ({
    'X-Profile-Id': profileId.value,
    'X-User-Password': profilePw.value,
  }))

  // Survey
  const surveyDone = ref(localStorage.getItem('sai42_survey') === '1')
  const surveyStep = ref(0)
  const surveyAnswers = ref<{
    pref: string[]
    mood: string[]
    move: string[]
  }>({
    pref: [],
    mood: [],
    move: [],
  })

  // Chat Session
  const sessionId = ref<string>(localStorage.getItem('sai42_sessionId') ?? '')
  const expectedDraftVersion = ref<number>(0)

  // Current Working Course (in chatbot)
  const course = ref<Course>({
    title: '데이트 코스 생성 중...',
    places: [],
    coords: [],
    fest: false,
    weather: null
  })

  // Chat Messages
  const messages = ref<Array<{ role: 'bot' | 'user'; content: string }>>([
    {
      role: 'bot',
      content:
        '두 분 취향과 오늘 날씨를 반영해 첫 코스를 만들었어요. 마음에 안 드는 장소는 자연어로 바꿔보세요!',
    },
  ])

  // Active Date
  const activeCourse = ref<ActiveCourse | null>(
    localStorage.getItem('sai42_active') ? JSON.parse(localStorage.getItem('sai42_active')!) : null,
  )
  const activeProgress = ref(Number(localStorage.getItem('sai42_progress') || '0'))
  const activeCourseId = ref(localStorage.getItem('sai42_activeCourseId') || '')

  // Rankings
  const rankings = ref<RankItem[]>([])

  // History
  const history = ref<HistoryItem[]>([])

  // Modals & Overlays Visibility
  const showSurvey = ref(false)
  const showCommentModal = ref(false)
  const toastMessage = ref('')
  const toastVisible = ref(false)

  // Toast Trigger Helper
  function triggerToast(msg: string) {
    toastMessage.value = msg
    toastVisible.value = true
    setTimeout(() => {
      toastVisible.value = false
    }, 2200)
  }

  // Save state to localStorage
  function saveToStorage() {
    localStorage.setItem('sai42_name', name.value)
    localStorage.setItem('sai42_profileId', profileId.value)
    localStorage.setItem('sai42_pw', profilePw.value)
    localStorage.setItem('sai42_survey', surveyDone.value ? '1' : '0')
    localStorage.setItem(
      'sai42_active',
      activeCourse.value ? JSON.stringify(activeCourse.value) : '',
    )
    localStorage.setItem('sai42_progress', activeProgress.value.toString())
    localStorage.setItem('sai42_activeCourseId', activeCourseId.value)
    localStorage.setItem('sai42_sessionId', sessionId.value)
  }

  // Auth Operations
  async function register(username: string, pw: string) {
    if (!username || pw.length !== 4) {
      triggerToast('닉네임과 숫자 4자리 비밀번호를 입력해 주세요.')
      return false
    }
    try {
      const res = await identityService.createProfile({ nickname: username, password: pw })
      if (res.success && res.data) {
        name.value = res.data.nickname
        profileId.value = res.data.id
        profilePw.value = pw
        saveToStorage()
        triggerToast('두 분의 사이42가 등록됐어요 💞')
        return true
      }
    } catch (e: any) {
      triggerToast(e?.message || '등록 중 오류가 발생했습니다.')
      return false
    }
    return false
  }

  async function login(username: string, pw: string) {
    if (!username || pw.length !== 4) {
      triggerToast('닉네임과 숫자 4자리 비밀번호를 입력해 주세요.')
      return false
    }

    try {
      const res = await identityService.verifyProfile({ nickname: username, password: pw })
      if (res.success && res.data) {
        name.value = res.data.nickname
        profileId.value = res.data.id
        profilePw.value = pw
        saveToStorage()
        triggerToast('입장했습니다 💞')
        // Load real data
        fetchRankings()
        fetchHistory()
        return true
      }
    } catch (e: any) {
      // Mock logic fallback for demo account
      if (username === '복숭아와호두' && pw === '0420') {
        name.value = username
        profileId.value = 'demo-id'
        profilePw.value = '0420'
        saveToStorage()
        triggerToast('데모 계정으로 입장했습니다 💞')
        fetchRankings()
        fetchHistory()
        return true
      }
      triggerToast(e?.message || '등록 정보가 없거나 오류가 발생했습니다.')
      return false
    }
    return false
  }

  function logout() {
    name.value = ''
    profileId.value = ''
    profilePw.value = ''
    sessionId.value = ''
    localStorage.removeItem('sai42_name')
    localStorage.removeItem('sai42_profileId')
    localStorage.removeItem('sai42_pw')
    localStorage.removeItem('sai42_sessionId')
    authMode.value = 'enter'
    triggerToast('로그아웃 되었습니다 👋')
  }

  // Survey Operations
  const surveyStepsList = [
    {
      emoji: '🎨',
      title: '내가 선호하는 데이트는?',
      desc: '여러 개 골라도 괜찮아요.',
      key: 'pref' as const,
      opts: [
        '☕ 감성 카페',
        '🌳 산책과 자연',
        '🖼️ 전시와 문화',
        '🍜 맛집 탐방',
        '🎳 활동적인 체험',
        '🌙 야경과 드라이브',
      ],
    },
    {
      emoji: '💭',
      title: '평소 좋아하는 분위기는?',
      desc: '둘 사이의 공통점을 찾아볼게요.',
      key: 'mood' as const,
      opts: [
        '🌷 설레고 아기자기',
        '🤎 조용하고 편안',
        '📸 사진이 잘 나오는',
        '✨ 새로운 자극',
        '😆 웃기고 활동적',
        '🫧 아무 계획 없는 여유',
      ],
    },
    {
      emoji: '🚌',
      title: '주로 어떻게 이동하나요?',
      desc: '장소 사이의 거리를 조절해요.',
      key: 'move' as const,
      single: true,
      opts: ['🚶 도보 중심', '🚌 대중교통', '🚗 자가용', '🎲 그날그날 달라요'],
    },
  ]

  function toggleSurveyOption(key: 'pref' | 'mood' | 'move', opt: string) {
    const list = surveyStepsList[surveyStep.value]!
    if (list.single) {
      surveyAnswers.value[key] = [opt]
    } else {
      const idx = surveyAnswers.value[key].indexOf(opt)
      if (idx >= 0) {
        surveyAnswers.value[key].splice(idx, 1)
      } else {
        surveyAnswers.value[key].push(opt)
      }
    }
  }

  async function nextSurveyStep() {
    const step = surveyStepsList[surveyStep.value]!
    const key = step.key
    if (!surveyAnswers.value[key].length) {
      triggerToast('하나 이상 선택해 주세요.')
      return
    }
    if (surveyStep.value < 2) {
      surveyStep.value++
    } else {
      surveyDone.value = true
      showSurvey.value = false
      saveToStorage()
      triggerToast('데이트 취향을 저장했어요')

      // Create initial chat session
      if (!sessionId.value) {
        try {
          const res = await chatService.createSession({
            date: new Date().toISOString().split('T')[0] || '',
            timeSlot: 'AFTERNOON',
            startTime: '13:00',
            district: 'YUSEONG_GU',
            spaceType: 'ANY',
            moods: ['QUIET'],
            activities: ['FOOD', 'WALK'],
            scheduleDensity: 'NORMAL',
            transportation: 'PUBLIC_TRANSIT'
          }, authHeaders.value as any)

          if (res.success && res.data) {
            sessionId.value = res.data.id
            expectedDraftVersion.value = res.data.draftVersion
            saveToStorage()
            updateCourseFromDraft(res.data.draft)
            messages.value.push({
              role: 'bot',
              content: res.data.assistantMessage.content || '취향을 반영해 첫 코스를 만들었어요!'
            })
          }
        } catch (e: any) {
          triggerToast('초기 코스 생성에 실패했습니다 (Mock 표시)')
        }
      }
    }
  }

  function prevSurveyStep() {
    if (surveyStep.value > 0) {
      surveyStep.value--
    }
  }

  async function fetchChatSession() {
    if (!sessionId.value || sessionId.value === 'demo-id') return
    try {
      const res = await chatService.getSession(sessionId.value, authHeaders.value as any)
      if (res.success && res.data && res.data.draft) {
        updateCourseFromDraft(res.data.draft)
        expectedDraftVersion.value = res.data.draftVersion || 0
      }
    } catch (e: any) {
      console.error(e)
    }
  }

  // Map backend draft to frontend model
  function updateCourseFromDraft(draft: any) {
    if (!draft) return
    try {
      course.value = {
        title: draft.title || '새로운 코스',
        places: draft.places ? draft.places.map((p: any) => p.place?.name || p.titleSnapshot || '알 수 없는 장소') : [],
        coords: draft.places ? draft.places.map((p: any) => [p.place?.latitude || 36.35, p.place?.longitude || 127.38]) : [],
        fest: course.value.fest,
        weather: draft.weather || null
      }
    } catch(e) {
      console.error('Draft mapping error:', e)
    }
  }

  // Chat Processing
  async function sendChatMessage(text: string) {
    if (!text.trim()) return
    messages.value.push({ role: 'user', content: text })

    if (profileId.value === 'demo-id' || !sessionId.value) {
      // Fallback to Mock if demo account or no session
      let botResponse = '좋아요. 현재 동선을 유지하면서 조금 더 잘 어울리게 조정했어요.'
      setTimeout(() => {
        messages.value.push({ role: 'bot', content: botResponse })
        // mock map update
        course.value = {
          ...course.value,
          places: [...course.value.places, '새로운 모의 장소'],
          coords: [...course.value.coords, [36.35 + Math.random()*0.01, 127.38 + Math.random()*0.01]]
        }
      }, 350)
      return
    }

    try {
      const res = await chatService.sendMessage(
        sessionId.value,
        { message: text, expectedDraftVersion: expectedDraftVersion.value },
        authHeaders.value as any
      )
      if (res.success && res.data) {
        expectedDraftVersion.value = res.data.draftVersion
        updateCourseFromDraft(res.data.draft)
        messages.value.push({ role: 'bot', content: res.data.assistantMessage.content })
      } else {
        triggerToast('사이봇 응답을 처리할 수 없습니다.')
      }
    } catch (e: any) {
      triggerToast(e?.message || '메시지 전송에 실패했습니다.')
    }
  }

  function addFestivalToCourse() {
    if (course.value.fest) {
      triggerToast('이미 코스에 들어 있어요.')
      return
    }
    course.value.fest = true
    course.value.places.push('뚝섬한강공원 드론라이트쇼')
    course.value.coords.push([37.529, 127.068])
    messages.value.push({
      role: 'bot',
      content: '오늘 열리는 <b>뚝섬한강공원 드론라이트쇼</b>를 마지막 코스에 넣었어요 🎉',
    })
    triggerToast('축제를 코스에 추가했어요')
  }

  // Course Decide
  async function decideCourse() {
    if (sessionId.value && profileId.value !== 'demo-id') {
      try {
        const res = await chatService.confirmSession(sessionId.value, {
          draftId: 'fake-draft-id', // We don't store draftId currently, would need it in a real setup
          expectedVersion: expectedDraftVersion.value
        }, authHeaders.value as any)
        
        if (res.success && res.data) {
          activeCourseId.value = res.data.courseId
        }
      } catch (e: any) {
        // Ignore error for simple integration
      }
    }

    activeCourse.value = {
      title: course.value.title,
      places: [...course.value.places],
      coords: [...course.value.coords],
      likes: {},
    }
    activeProgress.value = 0
    saveToStorage()
    triggerToast('오늘의 데이트 코스로 등록했어요 💗')
  }

  // Active Date operations
  async function togglePlaceLike(idx: number) {
    if (!activeCourse.value) return
    activeCourse.value.likes[idx] = !activeCourse.value.likes[idx]
    saveToStorage()
    
    if (activeCourseId.value && profileId.value !== 'demo-id') {
      try {
        const coursePlaceId = 'fake-place-id-' + idx
        if (activeCourse.value.likes[idx]) {
          await courseService.heartCoursePlace(coursePlaceId, authHeaders.value as any)
        } else {
          await courseService.unheartCoursePlace(coursePlaceId, authHeaders.value as any)
        }
      } catch (e) {
        // ignore
      }
    }

    triggerToast(
      activeCourse.value.likes[idx] ? '이 장소가 마음에 들었군요 💗' : '좋아요를 취소했어요',
    )
  }

  async function nextPlace() {
    if (!activeCourse.value) return
    if (activeProgress.value < activeCourse.value.places.length - 1) {
      activeProgress.value++
      saveToStorage()

      if (activeCourseId.value && profileId.value !== 'demo-id') {
        try {
          const coursePlaceId = 'fake-place-id-' + activeProgress.value
          await courseService.completeCoursePlace(coursePlaceId, authHeaders.value as any)
        } catch (e) {
          // ignore
        }
      }

      triggerToast('다음 장소로 이동해 볼까요? 🚌')
    }
  }

  async function submitReview(comment: string, rating: number) {
    if (!activeCourse.value) return
    const finalComment = comment.trim() || '오늘도 우리 사이에 좋은 기억 하나 추가!'

    if (activeCourseId.value && profileId.value !== 'demo-id') {
      try {
        await courseService.completeCurrentCourse({ completionComment: finalComment }, authHeaders.value as any)
        await communityService.createPost({ courseId: activeCourseId.value, oneLineComment: finalComment }, authHeaders.value as any)
      } catch (e) {
        // ignore
      }
    }

    history.value.unshift({
      date: '15',
      title: activeCourse.value.title,
      comment: finalComment,
      rating,
      places: [...activeCourse.value.places],
    })

    rankings.value.unshift({
      id: 'u' + Date.now(),
      title: activeCourse.value.title,
      places: [...activeCourse.value.places],
      comment: finalComment,
      creator: name.value || '익명 커플',
      use: 1,
      likes: 0,
      rating,
      theme: '방금 등록된 코스',
    })

    activeCourse.value = null
    activeProgress.value = 0
    showCommentModal.value = false
    saveToStorage()
    fetchRankings() // refresh
    triggerToast('데이트가 추억으로 저장됐어요 💌')
  }

  // Community
  async function fetchRankings() {
    if (profileId.value === 'demo-id') return
    try {
      const res = await communityService.listPosts({ sort: 'POPULAR' })
      if (res.success && res.data) {
        rankings.value = res.data.map((p: any) => ({
          id: p.postId,
          title: p.courseTitle,
          places: p.courseTitle.split(' '), // mock place mapping
          comment: p.oneLineComment,
          creator: p.authorNickname,
          use: p.placeHeartCount,
          likes: p.courseLikeCount,
          rating: 4.5,
          theme: '커플 추천'
        }))
      }
    } catch (e) {
      // Mock fallback
      if (rankings.value.length === 0) {
        rankings.value = [
          {
            id: 'c1',
            title: '비 오는 날, 포근한 문화 데이트',
            places: ['국립중앙과학관', '대전시립미술관', '만년동 저녁식사'],
            comment: '비 오는 날에도 이동이 편해서 대화에 집중하기 좋았어요.',
            creator: '구름이와 몽글이',
            use: 128,
            likes: 342,
            rating: 4.9,
            theme: '실내 · 문화',
          }
        ]
      }
    }
  }

  async function fetchHistory() {
    if (profileId.value === 'demo-id') return
    try {
      const res = await historyService.listMyDateCourses(authHeaders.value as any)
      if (res.success && res.data) {
        history.value = res.data.map((h: any) => ({
          date: h.date,
          title: h.title,
          comment: h.overallComment,
          rating: 5,
          places: []
        }))
      }
    } catch (e) {
      // fallback
      if (history.value.length === 0) {
        history.value = [
          {
            date: '12',
            title: '한밭수목원 노을 산책',
            comment: '사진 백 장 찍고 최종 선택은 세 장!',
            rating: 5,
            places: ['한밭수목원', '엑스포다리', '도룡동 카페'],
          }
        ]
      }
    }
  }

  function importRankedCourse(item: RankItem) {
    course.value = {
      title: item.title,
      places: [...item.places],
      coords: item.places.map((_, i) => [37.5564 + i * 0.003, 127.0445 + i * 0.003]),
      fest: false,
    }
    triggerToast('이 코스를 사이봇으로 가져왔어요')
  }

  async function likeRankItem(id: string) {
    const item = rankings.value.find((r) => r.id === id)
    if (item) {
      item.likes++
      saveToStorage()
      triggerToast('좋아요가 전해졌어요 💗')

      if (profileId.value !== 'demo-id') {
        try {
          await communityService.likePost(id, authHeaders.value as any)
        } catch (e) {}
      }
    }
  }

  async function deleteRankItem(id: string) {
    rankings.value = rankings.value.filter((r) => r.id !== id)
    saveToStorage()
    triggerToast('코스가 삭제되었습니다. 🗑️')

    if (profileId.value !== 'demo-id') {
      try {
        await communityService.deletePost(id, authHeaders.value as any)
      } catch (e) {}
    }
  }

  async function updateRankComment(id: string, newComment: string) {
    const item = rankings.value.find((r) => r.id === id)
    if (item) {
      item.comment = newComment
      saveToStorage()
      triggerToast('한줄 코멘트가 수정되었습니다. ✏️')

      if (profileId.value !== 'demo-id') {
        try {
          await communityService.updatePost(id, { oneLineComment: newComment }, authHeaders.value as any)
        } catch (e) {}
      }
    }
  }

  return {
    authMode,
    name,
    isDemo,
    surveyDone,
    surveyStep,
    surveyAnswers,
    course,
    messages,
    activeCourse,
    activeProgress,
    rankings,
    history,
    showSurvey,
    showCommentModal,
    toastMessage,
    toastVisible,
    surveyStepsList,
    triggerToast,
    register,
    login,
    logout,
    fetchRankings,
    fetchHistory,
    fetchChatSession,
    toggleSurveyOption,
    nextSurveyStep,
    prevSurveyStep,
    sendChatMessage,
    addFestivalToCourse,
    decideCourse,
    togglePlaceLike,
    nextPlace,
    submitReview,
    importRankedCourse,
    likeRankItem,
    deleteRankItem,
    updateRankComment,
  }
})
