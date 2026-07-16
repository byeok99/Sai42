import { historyRepository } from '@/services/repositories/historyRepository'
import type { HistoryListParams } from '@/services/repositories/historyRepository'

export const historyService = {
  listMyDateCourses: (
    headers: { 'X-Profile-Id': string; 'X-User-Password': string },
    params?: HistoryListParams,
  ) => historyRepository.listMyDateCourses(headers, params),
  getMyDateCourseDetail: (
    courseId: string,
    headers: { 'X-Profile-Id': string; 'X-User-Password': string },
  ) => historyRepository.getMyDateCourseDetail(courseId, headers),
  restartCourse: (
    courseId: string,
    headers: { 'X-Profile-Id': string; 'X-User-Password': string },
  ) => historyRepository.restartCourse(courseId, headers),
}
