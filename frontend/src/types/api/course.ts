export interface CourseDraftPlaceDto {
  contentId: string
  orderNo: number
  scheduledAt: string
  estimatedStayMinutes: number
  sweetComment: string
  titleSnapshot: string
  addressSnapshot?: string
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
}

export interface CompleteCourseRequestDto {
  completionComment: string
}
