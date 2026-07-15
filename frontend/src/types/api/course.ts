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
