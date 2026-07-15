import { apiClient } from '@/services/api/client'
import { apiEndpoints } from '@/services/api/endpoints'
import type { BaseDto } from '@/types/api/common'
import type { CompleteCourseRequestDto, CurrentCourseDto } from '@/types/api/course'

export interface CourseRepository {
  getCurrentCourse(headers: { 'X-Profile-Id': string; 'X-User-Password': string }): Promise<BaseDto<CurrentCourseDto>>
  completeCoursePlace(coursePlaceId: string, headers: { 'X-Profile-Id': string; 'X-User-Password': string }): Promise<BaseDto<CurrentCourseDto>>
  heartCoursePlace(coursePlaceId: string, headers: { 'X-Profile-Id': string; 'X-User-Password': string }): Promise<BaseDto<CurrentCourseDto>>
  unheartCoursePlace(coursePlaceId: string, headers: { 'X-Profile-Id': string; 'X-User-Password': string }): Promise<BaseDto<CurrentCourseDto>>
  completeCurrentCourse(payload: CompleteCourseRequestDto, headers: { 'X-Profile-Id': string; 'X-User-Password': string }): Promise<BaseDto<CurrentCourseDto>>
}

export class CourseRepositoryImpl implements CourseRepository {
  async getCurrentCourse(headers) {
    return apiClient.get<CurrentCourseDto>(apiEndpoints.currentCourse, { headers })
  }

  async completeCoursePlace(coursePlaceId, headers) {
    return apiClient.put<CurrentCourseDto>(apiEndpoints.completeCoursePlace(coursePlaceId), undefined, { headers })
  }

  async heartCoursePlace(coursePlaceId, headers) {
    return apiClient.put<CurrentCourseDto>(apiEndpoints.heartCoursePlace(coursePlaceId), undefined, { headers })
  }

  async unheartCoursePlace(coursePlaceId, headers) {
    return apiClient.delete<CurrentCourseDto>(apiEndpoints.heartCoursePlace(coursePlaceId), { headers })
  }

  async completeCurrentCourse(payload, headers) {
    return apiClient.post<CurrentCourseDto>(apiEndpoints.completeCurrentCourse, payload, { headers })
  }
}

export const courseRepository = new CourseRepositoryImpl()
