import type {
  ActivityType,
  CourseConditionDto,
  CourseMapDto,
  CoursePlaceSnapshotDto,
  District,
  Mood,
  ScheduleDensity,
  SpaceType,
  TimeSlot,
  Transportation,
  WeatherSummaryDto,
} from '@/types/api/course'

export type ChatSessionStatus = 'ACTIVE' | 'CONFIRMED' | 'DISCARDED' | 'EXPIRED'

export type ChatMessageRole = 'USER' | 'ASSISTANT'

export type CourseEditAction =
  | 'CHANGE_CAFE'
  | 'ADD_NIGHT_VIEW'
  | 'REDUCE_ROUTE'
  | 'INCREASE_INDOOR'
  | 'REGENERATE'

export interface CreateChatSessionRequestDto {
  date: string
  timeSlot: TimeSlot
  startTime: string
  district: District
  spaceType: SpaceType
  moods: Mood[]
  activities: ActivityType[]
  scheduleDensity: ScheduleDensity
  transportation: Transportation
  initialMessage?: string | null
}

export type ChatSessionCreateRequestDto = CreateChatSessionRequestDto

export interface ChatMessageDto {
  messageId: string
  role: ChatMessageRole
  content: string
  createdAt: string
}

export interface CourseDraftPlaceDto {
  coursePlaceId: string
  order: number
  scheduledAt: string
  estimatedStayMinutes: number
  place: CoursePlaceSnapshotDto
  sweetComment: string
}

export interface CourseDraftDto {
  draftId: string
  version: number
  title: string
  date: string
  timeSlot: TimeSlot
  overallComment: string
  estimatedTotalMinutes: number
  conditions: CourseConditionDto
  tags: string[]
  weather: WeatherSummaryDto | null
  places: CourseDraftPlaceDto[]
  map: CourseMapDto
}

export interface CreateChatSessionDto {
  sessionId: string
  status: ChatSessionStatus
  assistantMessage: ChatMessageDto
  courseDraft: CourseDraftDto
}

export interface ChatSessionDto {
  sessionId: string
  status: ChatSessionStatus
  conditions: CourseConditionDto
  messages: ChatMessageDto[]
  courseDraft: CourseDraftDto | null
}

export type SendChatMessageRequestDto =
  | {
      message: string
      quickAction?: null
      expectedDraftVersion: number
    }
  | {
      message?: null
      quickAction: CourseEditAction
      expectedDraftVersion: number
    }

export interface CourseDraftChangeSummaryDto {
  changed: boolean
  warnings: string[]
}

export interface SendChatMessageDto {
  userMessage: ChatMessageDto
  assistantMessage: ChatMessageDto
  changeSummary: CourseDraftChangeSummaryDto
  courseDraft: CourseDraftDto
}

export interface ConfirmChatSessionRequestDto {
  draftId: string
  expectedVersion: number
}
