import { historyRepository } from '@/services/repositories/historyRepository'

export const historyService = {
  listMyDateCourses: (headers: { 'X-Profile-Id': string; 'X-User-Password': string }) => historyRepository.listMyDateCourses(headers),
  getMyDateCourseDetail: (courseId: string, headers: { 'X-Profile-Id': string; 'X-User-Password': string }) => historyRepository.getMyDateCourseDetail(courseId, headers),
  restartCourse: (courseId: string, headers: { 'X-Profile-Id': string; 'X-User-Password': string }) => historyRepository.restartCourse(courseId, headers),
}
