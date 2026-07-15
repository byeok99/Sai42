export type TimeSlot = 'MORNING' | 'AFTERNOON' | 'FULL_DAY'

export type District = 'DONG_GU' | 'JUNG_GU' | 'SEO_GU' | 'YUSEONG_GU' | 'DAEDEOK_GU' | 'ANY'

export type SpaceType = 'INDOOR' | 'OUTDOOR' | 'ANY'

export type Mood = 'QUIET' | 'EMOTIONAL' | 'LIVELY' | 'SPECIAL'

export type ActivityType =
  | 'TOURISM'
  | 'CULTURE_EXHIBITION'
  | 'FOOD'
  | 'SHOPPING'
  | 'WALK'
  | 'LEPORTS'

export type ScheduleDensity = 'RELAXED' | 'NORMAL' | 'TIGHT'

export type Transportation = 'WALK' | 'PUBLIC_TRANSIT' | 'CAR' | 'FLEXIBLE'

export type PlaceCategory =
  | 'ATTRACTION'
  | 'CULTURAL_FACILITY'
  | 'TRAVEL_COURSE'
  | 'LEPORTS'
  | 'ACCOMMODATION'
  | 'SHOPPING'
  | 'RESTAURANT'

export type WeatherCondition =
  | 'CLEAR'
  | 'CLOUDY'
  | 'OVERCAST'
  | 'LIGHT_RAIN'
  | 'RAIN'
  | 'RAIN_SNOW'
  | 'SNOW'

export type DateCourseStatus = 'ACTIVE' | 'COMPLETED'

export type DateCourseSourceType = 'AI_CHAT' | 'RANKING_COPY' | 'HISTORY_RESTART'

export interface CourseConditionDto {
  date: string
  timeSlot: TimeSlot
  startTime: string
  district: District
  spaceType: SpaceType
  moods: Mood[]
  activities: ActivityType[]
  scheduleDensity: ScheduleDensity
  transportation: Transportation | null
}

export interface WeatherRecommendationDto {
  preferredSpaceType: SpaceType
  indoorRatio: number | null
  message: string
}

export interface WeatherSummaryDto {
  available: boolean
  district: District
  date: string
  timeSlot: TimeSlot
  summary: string | null
  temperatureMin: number | null
  temperatureMax: number | null
  precipitationProbability: number | null
  condition: WeatherCondition | null
  recommendation: WeatherRecommendationDto
  provider: string
  observedAt: string | null
}

export interface CoursePlaceSnapshotDto {
  contentId: string | null
  name: string
  category: PlaceCategory
  district: District | null
  address: string | null
  addressDetail: string | null
  latitude: number | null
  longitude: number | null
  imageUrl: string | null
  indoorOutdoor: SpaceType
}

export interface CoordinateDto {
  latitude: number
  longitude: number
}

export interface CourseMapDto {
  centerLatitude: number | null
  centerLongitude: number | null
  polyline: CoordinateDto[]
}

export interface CoursePlaceDto {
  coursePlaceId: string
  order: number
  scheduledAt: string
  estimatedStayMinutes: number
  place: CoursePlaceSnapshotDto
  sweetComment: string
  heartedByMe: boolean
  heartCount: number
}

export interface CourseProgressSummaryDto {
  currentOrderNo: number
  completedPlaceCount: number
  totalPlaceCount: number
  progressPercent: number
  allPlacesCompleted: boolean
}

export interface DateCourseDto {
  courseId: string
  status: DateCourseStatus
  sourceType: DateCourseSourceType
  title: string
  date: string
  timeSlot: TimeSlot
  overallComment: string
  estimatedTotalMinutes: number
  conditions: CourseConditionDto
  tags: string[]
  weather: WeatherSummaryDto | null
  places: CoursePlaceDto[]
  map: CourseMapDto
  progress: CourseProgressSummaryDto
  oneLineComment: string | null
  createdAt: string
  completedAt: string | null
}

export interface CourseDraftPlaceDto {
  coursePlaceId: string
  contentId: string
  orderNo: number
  scheduledAt: string
  estimatedStayMinutes: number
  sweetComment: string
  titleSnapshot: string
  addressSnapshot?: string
  heartedByMe?: boolean
}

export interface CurrentCourseDto {
  id: string
  title: string
  date: string
  startTime: string
  timeSlot: string
  overallComment: string
  places: CourseDraftPlaceDto[]
  currentOrderNo: number
  status: 'ACTIVE' | 'COMPLETED'
  progressPercent?: number
}

export interface CompleteCourseRequestDto {
  completionComment: string
}
