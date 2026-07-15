import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface Course {
  title: string
  places: string[]
  coords: [number, number][]
  fest: boolean
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
  const isDemo = ref(false)

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

  // Current Working Course (in chatbot)
  const course = ref<Course>({
    title: '한양대 부근 가을바람 산책 데이트',
    places: ['한양대학교 서울캠퍼스', '왕십리역 엔터식스', '성수동 감성 카페거리', '서울숲 산책로'],
    coords: [
      [37.5564, 127.0445],
      [37.5615, 127.0375],
      [37.5445, 127.056],
      [37.5443, 127.0374],
    ],
    fest: false,
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

  // Rankings Seed
  const initialRankings: RankItem[] = [
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
    },
    {
      id: 'c2',
      title: '노을까지 완벽한 한밭수목원 코스',
      places: ['한밭수목원', '엑스포다리', '도룡동 카페'],
      comment: '사진도 잘 나오고 걷기 좋아요. 편한 신발은 필수!',
      creator: '토끼와 곰',
      use: 96,
      likes: 277,
      rating: 4.8,
      theme: '산책 · 야경',
    },
    {
      id: 'c3',
      title: '대전역에서 시작하는 소제동 감성 코스',
      places: ['철도관사촌', '소제동 카페', '대동하늘공원'],
      comment: '짧게 만나도 꽉 찬 느낌. 마지막 야경이 진짜 좋아요.',
      creator: '복숭아와 호두',
      use: 84,
      likes: 221,
      rating: 4.7,
      theme: '감성 · 사진',
    },
    {
      id: 'c4',
      title: '아무거나 금지! 유성 랜덤 데이트',
      places: ['지질박물관', '유성온천공원', '봉명동 맛집'],
      comment: '룰렛으로 골랐는데 평소 안 가던 곳이라 더 재밌었어요.',
      creator: '감자와 고구마',
      use: 72,
      likes: 194,
      rating: 4.6,
      theme: '이색 · 랜덤',
    },
  ]
  const rankings = ref<RankItem[]>(
    localStorage.getItem('sai42_ranking')
      ? JSON.parse(localStorage.getItem('sai42_ranking')!)
      : initialRankings,
  )

  // History Seed
  const initialHistory: HistoryItem[] = [
    {
      date: '12',
      title: '한밭수목원 노을 산책',
      comment: '사진 백 장 찍고 최종 선택은 세 장!',
      rating: 5,
      places: ['한밭수목원', '엑스포다리', '도룡동 카페'],
    },
    {
      date: '06',
      title: '대전역 소제동 감성 코스',
      comment: '비가 살짝 와서 더 분위기 있었던 날.',
      rating: 4,
      places: ['철도관사촌', '볕', '대동하늘공원'],
    },
    {
      date: '01',
      title: '우리의 과학 데이트',
      comment: '생각보다 볼 게 많아서 시간이 순식간!',
      rating: 5,
      places: ['국립중앙과학관', '지질박물관', '유성온천공원'],
    },
  ]
  const history = ref<HistoryItem[]>(
    localStorage.getItem('sai42_history')
      ? JSON.parse(localStorage.getItem('sai42_history')!)
      : initialHistory,
  )

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
    localStorage.setItem('sai42_survey', surveyDone.value ? '1' : '0')
    localStorage.setItem(
      'sai42_active',
      activeCourse.value ? JSON.stringify(activeCourse.value) : '',
    )
    localStorage.setItem('sai42_progress', activeProgress.value.toString())
    localStorage.setItem('sai42_ranking', JSON.stringify(rankings.value))
    localStorage.setItem('sai42_history', JSON.stringify(history.value))
  }

  // Auth Operations
  function register(username: string, pw: string) {
    if (!username || pw.length !== 4) {
      triggerToast('닉네임과 숫자 4자리 비밀번호를 입력해 주세요.')
      return false
    }
    name.value = username
    localStorage.setItem('sai42_name', username)
    localStorage.setItem('sai42_pw', pw)
    saveToStorage()
    triggerToast('두 분의 사이42가 등록됐어요 💞')
    return true
  }

  function login(username: string, pw: string) {
    if (!username || pw.length !== 4) {
      triggerToast('닉네임과 숫자 4자리 비밀번호를 입력해 주세요.')
      return false
    }
    const storedName = localStorage.getItem('sai42_name')
    const storedPw = localStorage.getItem('sai42_pw')

    if (
      (username === '복숭아와호두' && pw === '0420') ||
      (storedName === username && storedPw === pw)
    ) {
      name.value = username
      saveToStorage()
      triggerToast('입장했습니다 💞')
      return true
    } else {
      triggerToast('등록 정보가 없어요. 처음 등록을 눌러 주세요.')
      return false
    }
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

  function nextSurveyStep() {
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
      messages.value.push({
        role: 'bot',
        content:
          '취향 저장 완료! 두 분은 <b>조용한 문화 데이트</b>와 <b>사진이 잘 나오는 장소</b>를 좋아하네요 💞',
      })
      triggerToast('데이트 취향을 저장했어요')
    }
  }

  function prevSurveyStep() {
    if (surveyStep.value > 0) {
      surveyStep.value--
    }
  }

  // Chat Processing (Simulated Bot Response)
  function sendChatMessage(text: string) {
    if (!text.trim()) return
    messages.value.push({ role: 'user', content: text })

    let botResponse = '좋아요. 현재 동선을 유지하면서 조금 더 잘 어울리게 조정했어요.'
    const search = text.toLowerCase()

    if (search.includes('카페')) {
      course.value.places[2] = '성수동 블루보틀 카페'
      course.value.coords[2] = [37.548, 127.044]
      course.value.title = '한양대 산책과 향기로운 커피 데이트'
      botResponse =
        '세 번째 장소를 <b>성수동 블루보틀 카페</b>로 바꿨어요. 대화할 시간이 더 길어집니다 ☕'
    } else if (search.includes('야경')) {
      if (!course.value.places.some((p) => p.includes('응봉산'))) {
        course.value.places.push('응봉산 팔각정 야경')
        course.value.coords.push([37.5488, 127.0315])
      }
      course.value.title = '서울숲부터 야경까지, 로맨틱 데이트'
      botResponse = '마지막에 <b>응봉산 팔각정 야경</b>을 추가했어요 🌙'
    } else if (search.includes('거리') || search.includes('동선')) {
      course.value = {
        title: '짧게 이동하고 오래 머무는 사근동 코스',
        places: ['한양대학교 서울캠퍼스', '사근동 벽화골목', '왕십리역 맛집거리'],
        coords: [
          [37.5564, 127.0445],
          [37.56, 127.0475],
          [37.5615, 127.0375],
        ],
        fest: false,
      }
      botResponse =
        '장소를 <b>사근동 및 왕십리 주변</b>으로 모았어요. 이동보다 대화에 시간을 써보세요.'
    } else if (search.includes('비') || search.includes('실내')) {
      course.value = {
        title: '우산을 덜 펴는 완전 실내 한양대 코스',
        places: ['왕십리 CGV', '엔터식스 몰', '한양대 백남학술정보관'],
        coords: [
          [37.5615, 127.0375],
          [37.561, 127.038],
          [37.5564, 127.0445],
        ],
        fest: false,
      }
      botResponse = '실내 90% 코스로 바꿨어요. 우산을 펴는 시간보다 손잡는 시간이 더 길어집니다 ☂️'
    }

    setTimeout(() => {
      messages.value.push({ role: 'bot', content: botResponse })
    }, 350)
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
  function decideCourse() {
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
  function togglePlaceLike(idx: number) {
    if (!activeCourse.value) return
    activeCourse.value.likes[idx] = !activeCourse.value.likes[idx]
    saveToStorage()
    triggerToast(
      activeCourse.value.likes[idx] ? '이 장소가 마음에 들었군요 💗' : '좋아요를 취소했어요',
    )
  }

  function nextPlace() {
    if (!activeCourse.value) return
    if (activeProgress.value < activeCourse.value.places.length - 1) {
      activeProgress.value++
      saveToStorage()
      triggerToast('다음 장소로 이동해 볼까요? 🚌')
    }
  }

  function submitReview(comment: string, rating: number) {
    if (!activeCourse.value) return
    const finalComment = comment.trim() || '오늘도 우리 사이에 좋은 기억 하나 추가!'

    // Add to history
    history.value.unshift({
      date: '15',
      title: activeCourse.value.title,
      comment: finalComment,
      rating,
      places: [...activeCourse.value.places],
    })

    // Add to rankings list
    rankings.value.unshift({
      id: 'u' + Date.now(),
      title: activeCourse.value.title,
      places: [...activeCourse.value.places],
      comment: finalComment,
      creator: name.value || '익명 커플',
      use: 1,
      likes: 0,
      rating,
      theme: '방금 등록된 코',
    })

    activeCourse.value = null
    activeProgress.value = 0
    showCommentModal.value = false
    saveToStorage()
    triggerToast('데이트가 추억으로 저장됐어요 💌')
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

  function likeRankItem(id: string) {
    const item = rankings.value.find((r) => r.id === id)
    if (item) {
      item.likes++
      saveToStorage()
      triggerToast('좋아요가 전해졌어요 💗')
    }
  }

  function deleteRankItem(id: string) {
    rankings.value = rankings.value.filter((r) => r.id !== id)
    saveToStorage()
    triggerToast('코스가 삭제되었습니다. 🗑️')
  }

  function updateRankComment(id: string, newComment: string) {
    const item = rankings.value.find((r) => r.id === id)
    if (item) {
      item.comment = newComment
      saveToStorage()
      triggerToast('한줄 코멘트가 수정되었습니다. ✏️')
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
