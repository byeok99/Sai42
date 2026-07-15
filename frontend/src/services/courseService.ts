import { courseRepository } from '@/services/repositories/courseRepository'

export const courseService = {
  getCurrentCourse: (headers: { 'X-Profile-Id': string; 'X-User-Password': string }) => courseRepository.getCurrentCourse(headers),
  completeCoursePlace: (coursePlaceId: string, headers: { 'X-Profile-Id': string; 'X-User-Password': string }) => courseRepository.completeCoursePlace(coursePlaceId, headers),
  heartCoursePlace: (coursePlaceId: string, headers: { 'X-Profile-Id': string; 'X-User-Password': string }) => courseRepository.heartCoursePlace(coursePlaceId, headers),
  unheartCoursePlace: (coursePlaceId: string, headers: { 'X-Profile-Id': string; 'X-User-Password': string }) => courseRepository.unheartCoursePlace(coursePlaceId, headers),
  completeCurrentCourse: (payload: { oneLineComment: string }, headers: { 'X-Profile-Id': string; 'X-User-Password': string }) => courseRepository.completeCurrentCourse(payload, headers),
}
