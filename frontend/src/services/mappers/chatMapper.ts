import type {
  ChatMessageDto,
  ChatSessionDto,
  ChatSessionStatus,
  CourseDraftDto,
  CreateChatSessionDto,
  SendChatMessageDto,
} from '@/types/api/chat'
import type { BaseDto } from '@/types/api/common'
import type {
  ActivityType,
  CourseConditionDto,
  CourseMapDto,
  CoursePlaceDto,
  CoursePlaceSnapshotDto,
  DateCourseDto,
  District,
  Mood,
  PlaceCategory,
  ScheduleDensity,
  SpaceType,
  TimeSlot,
  Transportation,
  WeatherCondition,
  WeatherSummaryDto,
} from '@/types/api/course'

type ContractRecord = Record<string, unknown>

export type ChatServiceResponse<T> = Omit<BaseDto<T>, 'data'> & { data: T }

export interface CreatedChatSession {
  id: string
  status: ChatSessionStatus
  assistantMessage: ChatMessageDto
  draft: CourseDraftDto
  draftVersion: number
}

export interface ChatSessionSnapshot {
  id: string
  status: ChatSessionStatus
  conditions: CourseConditionDto
  messages: ChatMessageDto[]
  draft: CourseDraftDto | null
  draftVersion: number | null
}

export interface ChatDraftUpdate {
  userMessage: ChatMessageDto
  assistantMessage: ChatMessageDto
  changed: boolean
  warnings: string[]
  draft: CourseDraftDto
  draftVersion: number
}

const CHAT_SESSION_STATUSES = ['ACTIVE', 'CONFIRMED', 'DISCARDED', 'EXPIRED'] as const
const CHAT_MESSAGE_ROLES = ['USER', 'ASSISTANT'] as const
const TIME_SLOTS = ['MORNING', 'AFTERNOON', 'FULL_DAY'] as const
const DISTRICTS = ['DONG_GU', 'JUNG_GU', 'SEO_GU', 'YUSEONG_GU', 'DAEDEOK_GU', 'ANY'] as const
const SPACE_TYPES = ['INDOOR', 'OUTDOOR', 'ANY'] as const
const MOODS = ['QUIET', 'EMOTIONAL', 'LIVELY', 'SPECIAL'] as const
const ACTIVITIES = ['TOURISM', 'CULTURE_EXHIBITION', 'FOOD', 'SHOPPING', 'WALK', 'LEPORTS'] as const
const SCHEDULE_DENSITIES = ['RELAXED', 'NORMAL', 'TIGHT'] as const
const TRANSPORTATIONS = ['WALK', 'PUBLIC_TRANSIT', 'CAR', 'FLEXIBLE'] as const
const PLACE_CATEGORIES = [
  'ATTRACTION',
  'CULTURAL_FACILITY',
  'TRAVEL_COURSE',
  'LEPORTS',
  'ACCOMMODATION',
  'SHOPPING',
  'RESTAURANT',
] as const
const WEATHER_CONDITIONS = [
  'CLEAR',
  'CLOUDY',
  'OVERCAST',
  'LIGHT_RAIN',
  'RAIN',
  'RAIN_SNOW',
  'SNOW',
] as const
const DATE_COURSE_STATUSES = ['ACTIVE', 'COMPLETED'] as const
const DATE_COURSE_SOURCE_TYPES = ['AI_CHAT', 'RANKING_COPY', 'HISTORY_RESTART'] as const

function contractError(path: string, expected: string, value: unknown): never {
  const actual = value === null ? 'null' : Array.isArray(value) ? 'array' : typeof value
  throw new TypeError(`[chatMapper] ${path}: expected ${expected}, received ${actual}`)
}

function asRecord(value: unknown, path: string): ContractRecord {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    return contractError(path, 'object', value)
  }
  return value as ContractRecord
}

function assertExactKeys(value: ContractRecord, expected: readonly string[], path: string): void {
  const actualKeys = Object.keys(value).sort()
  const expectedKeys = [...expected].sort()
  if (
    actualKeys.length !== expectedKeys.length ||
    actualKeys.some((key, index) => key !== expectedKeys[index])
  ) {
    throw new TypeError(
      `[chatMapper] ${path}: expected keys ${expectedKeys.join(', ')}, received ${actualKeys.join(', ')}`,
    )
  }
}

function assertString(value: unknown, path: string): asserts value is string {
  if (typeof value !== 'string') {
    contractError(path, 'string', value)
  }
}

function assertStringOrNull(value: unknown, path: string): asserts value is string | null {
  if (value !== null) {
    assertString(value, path)
  }
}

function assertBoolean(value: unknown, path: string): asserts value is boolean {
  if (typeof value !== 'boolean') {
    contractError(path, 'boolean', value)
  }
}

function assertNumber(value: unknown, path: string): asserts value is number {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    contractError(path, 'finite number', value)
  }
}

function assertNumberOrNull(value: unknown, path: string): asserts value is number | null {
  if (value !== null) {
    assertNumber(value, path)
  }
}

function assertInteger(value: unknown, path: string): asserts value is number {
  assertNumber(value, path)
  if (!Number.isInteger(value)) {
    contractError(path, 'integer', value)
  }
}

function assertArray(value: unknown, path: string): asserts value is unknown[] {
  if (!Array.isArray(value)) {
    contractError(path, 'array', value)
  }
}

function assertStringArray(value: unknown, path: string): asserts value is string[] {
  assertArray(value, path)
  value.forEach((item, index) => assertString(item, `${path}[${index}]`))
}

function assertEnum<T extends string>(
  value: unknown,
  allowed: readonly T[],
  path: string,
): asserts value is T {
  if (typeof value !== 'string' || !allowed.includes(value as T)) {
    contractError(path, allowed.join(' | '), value)
  }
}

function assertEnumArray<T extends string>(
  value: unknown,
  allowed: readonly T[],
  path: string,
): asserts value is T[] {
  assertArray(value, path)
  value.forEach((item, index) => assertEnum(item, allowed, `${path}[${index}]`))
}

function assertDate(value: unknown, path: string): asserts value is string {
  assertString(value, path)
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    contractError(path, 'YYYY-MM-DD string', value)
  }
}

function assertTime(value: unknown, path: string): asserts value is string {
  assertString(value, path)
  if (!/^\d{2}:\d{2}(?::\d{2}(?:\.\d{1,6})?)?$/.test(value)) {
    contractError(path, 'HH:mm or HH:mm:ss string', value)
  }
}

function assertDateTime(value: unknown, path: string): asserts value is string {
  assertString(value, path)
  if (!value.includes('T')) {
    contractError(path, 'ISO-8601 datetime string', value)
  }
}

function assertDateTimeOrNull(value: unknown, path: string): asserts value is string | null {
  if (value !== null) {
    assertDateTime(value, path)
  }
}

function assertCourseConditionDto(
  value: unknown,
  path: string,
): asserts value is CourseConditionDto {
  const dto = asRecord(value, path)
  assertExactKeys(
    dto,
    [
      'date',
      'timeSlot',
      'startTime',
      'district',
      'spaceType',
      'moods',
      'activities',
      'scheduleDensity',
      'transportation',
    ],
    path,
  )
  assertDate(dto.date, `${path}.date`)
  assertEnum<TimeSlot>(dto.timeSlot, TIME_SLOTS, `${path}.timeSlot`)
  assertTime(dto.startTime, `${path}.startTime`)
  assertEnum<District>(dto.district, DISTRICTS, `${path}.district`)
  assertEnum<SpaceType>(dto.spaceType, SPACE_TYPES, `${path}.spaceType`)
  assertEnumArray<Mood>(dto.moods, MOODS, `${path}.moods`)
  assertEnumArray<ActivityType>(dto.activities, ACTIVITIES, `${path}.activities`)
  assertEnum<ScheduleDensity>(dto.scheduleDensity, SCHEDULE_DENSITIES, `${path}.scheduleDensity`)
  if (dto.transportation !== null) {
    assertEnum<Transportation>(dto.transportation, TRANSPORTATIONS, `${path}.transportation`)
  }
}

function assertWeatherSummaryDto(value: unknown, path: string): asserts value is WeatherSummaryDto {
  const dto = asRecord(value, path)
  assertExactKeys(
    dto,
    [
      'available',
      'district',
      'date',
      'timeSlot',
      'summary',
      'temperatureMin',
      'temperatureMax',
      'precipitationProbability',
      'condition',
      'recommendation',
      'provider',
      'observedAt',
    ],
    path,
  )
  assertBoolean(dto.available, `${path}.available`)
  assertEnum<District>(dto.district, DISTRICTS, `${path}.district`)
  assertDate(dto.date, `${path}.date`)
  assertEnum<TimeSlot>(dto.timeSlot, TIME_SLOTS, `${path}.timeSlot`)
  assertStringOrNull(dto.summary, `${path}.summary`)
  assertNumberOrNull(dto.temperatureMin, `${path}.temperatureMin`)
  assertNumberOrNull(dto.temperatureMax, `${path}.temperatureMax`)
  assertNumberOrNull(dto.precipitationProbability, `${path}.precipitationProbability`)
  if (dto.precipitationProbability !== null && !Number.isInteger(dto.precipitationProbability)) {
    contractError(
      `${path}.precipitationProbability`,
      'integer or null',
      dto.precipitationProbability,
    )
  }
  if (dto.condition !== null) {
    assertEnum<WeatherCondition>(dto.condition, WEATHER_CONDITIONS, `${path}.condition`)
  }

  const recommendation = asRecord(dto.recommendation, `${path}.recommendation`)
  assertExactKeys(
    recommendation,
    ['preferredSpaceType', 'indoorRatio', 'message'],
    `${path}.recommendation`,
  )
  assertEnum<SpaceType>(
    recommendation.preferredSpaceType,
    SPACE_TYPES,
    `${path}.recommendation.preferredSpaceType`,
  )
  assertNumberOrNull(recommendation.indoorRatio, `${path}.recommendation.indoorRatio`)
  assertString(recommendation.message, `${path}.recommendation.message`)
  assertString(dto.provider, `${path}.provider`)
  assertDateTimeOrNull(dto.observedAt, `${path}.observedAt`)
}

function assertCoursePlaceSnapshotDto(
  value: unknown,
  path: string,
): asserts value is CoursePlaceSnapshotDto {
  const dto = asRecord(value, path)
  assertExactKeys(
    dto,
    [
      'contentId',
      'name',
      'category',
      'district',
      'address',
      'addressDetail',
      'latitude',
      'longitude',
      'imageUrl',
      'indoorOutdoor',
    ],
    path,
  )
  assertStringOrNull(dto.contentId, `${path}.contentId`)
  assertString(dto.name, `${path}.name`)
  assertEnum<PlaceCategory>(dto.category, PLACE_CATEGORIES, `${path}.category`)
  if (dto.district !== null) {
    assertEnum<District>(dto.district, DISTRICTS, `${path}.district`)
  }
  assertStringOrNull(dto.address, `${path}.address`)
  assertStringOrNull(dto.addressDetail, `${path}.addressDetail`)
  assertNumberOrNull(dto.latitude, `${path}.latitude`)
  assertNumberOrNull(dto.longitude, `${path}.longitude`)
  assertStringOrNull(dto.imageUrl, `${path}.imageUrl`)
  assertEnum<SpaceType>(dto.indoorOutdoor, SPACE_TYPES, `${path}.indoorOutdoor`)
}

function assertCourseMapDto(value: unknown, path: string): asserts value is CourseMapDto {
  const dto = asRecord(value, path)
  assertExactKeys(dto, ['centerLatitude', 'centerLongitude', 'polyline'], path)
  assertNumberOrNull(dto.centerLatitude, `${path}.centerLatitude`)
  assertNumberOrNull(dto.centerLongitude, `${path}.centerLongitude`)
  assertArray(dto.polyline, `${path}.polyline`)
  dto.polyline.forEach((item, index) => {
    const coordinatePath = `${path}.polyline[${index}]`
    const coordinate = asRecord(item, coordinatePath)
    assertExactKeys(coordinate, ['latitude', 'longitude'], coordinatePath)
    assertNumber(coordinate.latitude, `${coordinatePath}.latitude`)
    assertNumber(coordinate.longitude, `${coordinatePath}.longitude`)
  })
}

function assertCourseDraftDto(value: unknown, path: string): asserts value is CourseDraftDto {
  const dto = asRecord(value, path)
  assertExactKeys(
    dto,
    [
      'draftId',
      'version',
      'title',
      'date',
      'timeSlot',
      'overallComment',
      'estimatedTotalMinutes',
      'conditions',
      'tags',
      'weather',
      'places',
      'map',
    ],
    path,
  )
  assertString(dto.draftId, `${path}.draftId`)
  assertInteger(dto.version, `${path}.version`)
  assertString(dto.title, `${path}.title`)
  assertDate(dto.date, `${path}.date`)
  assertEnum<TimeSlot>(dto.timeSlot, TIME_SLOTS, `${path}.timeSlot`)
  assertString(dto.overallComment, `${path}.overallComment`)
  assertInteger(dto.estimatedTotalMinutes, `${path}.estimatedTotalMinutes`)
  assertCourseConditionDto(dto.conditions, `${path}.conditions`)
  assertStringArray(dto.tags, `${path}.tags`)
  if (dto.weather !== null) {
    assertWeatherSummaryDto(dto.weather, `${path}.weather`)
  }
  assertArray(dto.places, `${path}.places`)
  if (dto.places.length < 2 || dto.places.length > 4) {
    contractError(`${path}.places`, 'array with 2 to 4 items', dto.places)
  }
  dto.places.forEach((item, index) => {
    const placePath = `${path}.places[${index}]`
    const place = asRecord(item, placePath)
    assertExactKeys(
      place,
      ['coursePlaceId', 'order', 'scheduledAt', 'estimatedStayMinutes', 'place', 'sweetComment'],
      placePath,
    )
    assertString(place.coursePlaceId, `${placePath}.coursePlaceId`)
    assertInteger(place.order, `${placePath}.order`)
    assertDateTime(place.scheduledAt, `${placePath}.scheduledAt`)
    assertInteger(place.estimatedStayMinutes, `${placePath}.estimatedStayMinutes`)
    assertCoursePlaceSnapshotDto(place.place, `${placePath}.place`)
    assertString(place.sweetComment, `${placePath}.sweetComment`)
  })
  assertCourseMapDto(dto.map, `${path}.map`)
}

function assertChatMessageDto(value: unknown, path: string): asserts value is ChatMessageDto {
  const dto = asRecord(value, path)
  assertExactKeys(dto, ['messageId', 'role', 'content', 'createdAt'], path)
  assertString(dto.messageId, `${path}.messageId`)
  assertEnum(dto.role, CHAT_MESSAGE_ROLES, `${path}.role`)
  assertString(dto.content, `${path}.content`)
  assertDateTime(dto.createdAt, `${path}.createdAt`)
}

function assertCreateChatSessionDto(
  value: unknown,
  path: string,
): asserts value is CreateChatSessionDto {
  const dto = asRecord(value, path)
  assertExactKeys(dto, ['sessionId', 'status', 'assistantMessage', 'courseDraft'], path)
  assertString(dto.sessionId, `${path}.sessionId`)
  assertEnum(dto.status, CHAT_SESSION_STATUSES, `${path}.status`)
  assertChatMessageDto(dto.assistantMessage, `${path}.assistantMessage`)
  assertCourseDraftDto(dto.courseDraft, `${path}.courseDraft`)
}

function assertChatSessionDto(value: unknown, path: string): asserts value is ChatSessionDto {
  const dto = asRecord(value, path)
  assertExactKeys(dto, ['sessionId', 'status', 'conditions', 'messages', 'courseDraft'], path)
  assertString(dto.sessionId, `${path}.sessionId`)
  assertEnum(dto.status, CHAT_SESSION_STATUSES, `${path}.status`)
  assertCourseConditionDto(dto.conditions, `${path}.conditions`)
  assertArray(dto.messages, `${path}.messages`)
  dto.messages.forEach((message, index) =>
    assertChatMessageDto(message, `${path}.messages[${index}]`),
  )
  if (dto.courseDraft !== null) {
    assertCourseDraftDto(dto.courseDraft, `${path}.courseDraft`)
  }
}

function assertSendChatMessageDto(
  value: unknown,
  path: string,
): asserts value is SendChatMessageDto {
  const dto = asRecord(value, path)
  assertExactKeys(dto, ['userMessage', 'assistantMessage', 'changeSummary', 'courseDraft'], path)
  assertChatMessageDto(dto.userMessage, `${path}.userMessage`)
  assertChatMessageDto(dto.assistantMessage, `${path}.assistantMessage`)
  const summary = asRecord(dto.changeSummary, `${path}.changeSummary`)
  assertExactKeys(summary, ['changed', 'warnings'], `${path}.changeSummary`)
  assertBoolean(summary.changed, `${path}.changeSummary.changed`)
  assertStringArray(summary.warnings, `${path}.changeSummary.warnings`)
  assertCourseDraftDto(dto.courseDraft, `${path}.courseDraft`)
}

function assertCoursePlaceDto(value: unknown, path: string): asserts value is CoursePlaceDto {
  const dto = asRecord(value, path)
  assertExactKeys(
    dto,
    [
      'coursePlaceId',
      'order',
      'scheduledAt',
      'estimatedStayMinutes',
      'place',
      'sweetComment',
      'heartedByMe',
      'heartCount',
    ],
    path,
  )
  assertString(dto.coursePlaceId, `${path}.coursePlaceId`)
  assertInteger(dto.order, `${path}.order`)
  assertDateTime(dto.scheduledAt, `${path}.scheduledAt`)
  assertInteger(dto.estimatedStayMinutes, `${path}.estimatedStayMinutes`)
  assertCoursePlaceSnapshotDto(dto.place, `${path}.place`)
  assertString(dto.sweetComment, `${path}.sweetComment`)
  assertBoolean(dto.heartedByMe, `${path}.heartedByMe`)
  assertInteger(dto.heartCount, `${path}.heartCount`)
}

function assertDateCourseDto(value: unknown, path: string): asserts value is DateCourseDto {
  const dto = asRecord(value, path)
  assertExactKeys(
    dto,
    [
      'courseId',
      'status',
      'sourceType',
      'title',
      'date',
      'timeSlot',
      'overallComment',
      'estimatedTotalMinutes',
      'conditions',
      'tags',
      'weather',
      'places',
      'map',
      'progress',
      'oneLineComment',
      'createdAt',
      'completedAt',
    ],
    path,
  )
  assertString(dto.courseId, `${path}.courseId`)
  assertEnum(dto.status, DATE_COURSE_STATUSES, `${path}.status`)
  assertEnum(dto.sourceType, DATE_COURSE_SOURCE_TYPES, `${path}.sourceType`)
  assertString(dto.title, `${path}.title`)
  assertDate(dto.date, `${path}.date`)
  assertEnum<TimeSlot>(dto.timeSlot, TIME_SLOTS, `${path}.timeSlot`)
  assertString(dto.overallComment, `${path}.overallComment`)
  assertInteger(dto.estimatedTotalMinutes, `${path}.estimatedTotalMinutes`)
  assertCourseConditionDto(dto.conditions, `${path}.conditions`)
  assertStringArray(dto.tags, `${path}.tags`)
  if (dto.weather !== null) {
    assertWeatherSummaryDto(dto.weather, `${path}.weather`)
  }
  assertArray(dto.places, `${path}.places`)
  if (dto.places.length < 2 || dto.places.length > 4) {
    contractError(`${path}.places`, 'array with 2 to 4 items', dto.places)
  }
  dto.places.forEach((place, index) => assertCoursePlaceDto(place, `${path}.places[${index}]`))
  assertCourseMapDto(dto.map, `${path}.map`)

  const progress = asRecord(dto.progress, `${path}.progress`)
  assertExactKeys(
    progress,
    [
      'currentOrderNo',
      'completedPlaceCount',
      'totalPlaceCount',
      'progressPercent',
      'allPlacesCompleted',
    ],
    `${path}.progress`,
  )
  assertInteger(progress.currentOrderNo, `${path}.progress.currentOrderNo`)
  assertInteger(progress.completedPlaceCount, `${path}.progress.completedPlaceCount`)
  assertInteger(progress.totalPlaceCount, `${path}.progress.totalPlaceCount`)
  assertInteger(progress.progressPercent, `${path}.progress.progressPercent`)
  assertBoolean(progress.allPlacesCompleted, `${path}.progress.allPlacesCompleted`)
  assertStringOrNull(dto.oneLineComment, `${path}.oneLineComment`)
  assertDateTime(dto.createdAt, `${path}.createdAt`)
  assertDateTimeOrNull(dto.completedAt, `${path}.completedAt`)
}

function assertSuccessEnvelope(response: unknown, code: string, endpoint: string): void {
  const envelope = asRecord(response, endpoint)
  assertExactKeys(
    envelope,
    ['success', 'code', 'message', 'data', 'meta', 'timestamp', 'traceId'],
    endpoint,
  )
  if (envelope.success !== true) {
    contractError(`${endpoint}.success`, 'true', envelope.success)
  }
  assertString(envelope.code, `${endpoint}.code`)
  if (envelope.code !== code) {
    throw new TypeError(
      `[chatMapper] ${endpoint}.code: expected ${code}, received ${envelope.code}`,
    )
  }
  assertString(envelope.message, `${endpoint}.message`)
  if (envelope.meta !== null) {
    contractError(`${endpoint}.meta`, 'null', envelope.meta)
  }
  assertDateTime(envelope.timestamp, `${endpoint}.timestamp`)
  assertString(envelope.traceId, `${endpoint}.traceId`)
}

function normalizeConditionTime(conditions: CourseConditionDto): CourseConditionDto {
  return {
    ...conditions,
    startTime: conditions.startTime.slice(0, 5),
  }
}

function normalizeDraft(draft: CourseDraftDto): CourseDraftDto {
  return {
    ...draft,
    conditions: normalizeConditionTime(draft.conditions),
  }
}

function normalizeDateCourse(course: DateCourseDto): DateCourseDto {
  return {
    ...course,
    conditions: normalizeConditionTime(course.conditions),
  }
}

export function mapCreateChatSessionResponse(
  response: BaseDto<CreateChatSessionDto>,
): ChatServiceResponse<CreatedChatSession> {
  const data: unknown = response.data
  assertSuccessEnvelope(response, 'CHAT_SESSION_CREATED', 'POST /chat/sessions')
  assertCreateChatSessionDto(data, 'POST /chat/sessions.data')
  const draft = normalizeDraft(data.courseDraft)
  return {
    ...response,
    data: {
      id: data.sessionId,
      status: data.status,
      assistantMessage: data.assistantMessage,
      draft,
      draftVersion: draft.version,
    },
  }
}

export function mapChatSessionResponse(
  response: BaseDto<ChatSessionDto>,
): ChatServiceResponse<ChatSessionSnapshot> {
  const data: unknown = response.data
  assertSuccessEnvelope(response, 'COMMON_OK', 'GET /chat/sessions/{sessionId}')
  assertChatSessionDto(data, 'GET /chat/sessions/{sessionId}.data')
  const draft = data.courseDraft ? normalizeDraft(data.courseDraft) : null
  return {
    ...response,
    data: {
      id: data.sessionId,
      status: data.status,
      conditions: normalizeConditionTime(data.conditions),
      messages: data.messages,
      draft,
      draftVersion: draft?.version ?? null,
    },
  }
}

export function mapSendChatMessageResponse(
  response: BaseDto<SendChatMessageDto>,
): ChatServiceResponse<ChatDraftUpdate> {
  const data: unknown = response.data
  assertSuccessEnvelope(response, 'CHAT_DRAFT_UPDATED', 'POST /chat/sessions/{sessionId}/messages')
  assertSendChatMessageDto(data, 'POST /chat/sessions/{sessionId}/messages.data')
  const draft = normalizeDraft(data.courseDraft)
  return {
    ...response,
    data: {
      userMessage: data.userMessage,
      assistantMessage: data.assistantMessage,
      changed: data.changeSummary.changed,
      warnings: data.changeSummary.warnings,
      draft,
      draftVersion: draft.version,
    },
  }
}

export function mapConfirmChatSessionResponse(
  response: BaseDto<DateCourseDto>,
): ChatServiceResponse<DateCourseDto> {
  const data: unknown = response.data
  assertSuccessEnvelope(
    response,
    'CHAT_SESSION_CONFIRMED',
    'POST /chat/sessions/{sessionId}/confirm',
  )
  assertDateCourseDto(data, 'POST /chat/sessions/{sessionId}/confirm.data')
  return {
    ...response,
    data: normalizeDateCourse(data),
  }
}

export function validateDiscardChatSessionResponse(response: BaseDto<null>): BaseDto<null> {
  assertSuccessEnvelope(response, 'CHAT_SESSION_DISCARDED', 'DELETE /chat/sessions/{sessionId}')
  if (response.data !== null) {
    contractError('DELETE /chat/sessions/{sessionId}.data', 'null', response.data)
  }
  return response
}
