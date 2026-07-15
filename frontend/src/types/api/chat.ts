export interface ChatSessionCreateRequestDto {
  date: string
  timeSlot: string
  startTime: string
  district: string
  spaceType: string
  moods: string[]
  activities: string[]
  scheduleDensity: string
  transportation: string
}

export interface ChatSessionDto {
  id: string
  status: string
  conditions: ChatSessionCreateRequestDto
  messages: Array<{
    role: 'user' | 'assistant'
    content: string
  }>
  draft?: unknown
  draftVersion: number
}
