import { apiClient } from '@/services/api/client'
import { apiEndpoints } from '@/services/api/endpoints'
import type { BaseDto } from '@/types/api/common'
import type {
  CompleteCourseRequestDto,
  CompleteDateCourseDto,
  CoursePlaceHeartDto,
  DateCourseDto,
  DateCourseProgressDto,
} from '@/types/api/course'

export interface CourseRepository {
  getCurrentCourse(headers: { 'X-Profile-Id': string; 'X-User-Password': string }): Promise<BaseDto<DateCourseDto>>
  completeCoursePlace(coursePlaceId: string, headers: { 'X-Profile-Id': string; 'X-User-Password': string }): Promise<BaseDto<DateCourseProgressDto>>
  heartCoursePlace(coursePlaceId: string, headers: { 'X-Profile-Id': string; 'X-User-Password': string }): Promise<BaseDto<CoursePlaceHeartDto>>
  unheartCoursePlace(coursePlaceId: string, headers: { 'X-Profile-Id': string; 'X-User-Password': string }): Promise<BaseDto<CoursePlaceHeartDto>>
  completeCurrentCourse(payload: CompleteCourseRequestDto, headers: { 'X-Profile-Id': string; 'X-User-Password': string }): Promise<BaseDto<CompleteDateCourseDto>>
}

export class CourseRepositoryImpl implements CourseRepository {
  async getCurrentCourse(headers: { 'X-Profile-Id': string; 'X-User-Password': string }) {
    return apiClient.get<DateCourseDto>(apiEndpoints.currentCourse, { headers })
  }

  async completeCoursePlace(coursePlaceId: string, headers: { 'X-Profile-Id': string; 'X-User-Password': string }) {
    return apiClient.put<DateCourseProgressDto>(apiEndpoints.completeCoursePlace(coursePlaceId), undefined, { headers })
  }

  async heartCoursePlace(coursePlaceId: string, headers: { 'X-Profile-Id': string; 'X-User-Password': string }) {
    return apiClient.put<CoursePlaceHeartDto>(apiEndpoints.heartCoursePlace(coursePlaceId), undefined, { headers })
  }

  async unheartCoursePlace(coursePlaceId: string, headers: { 'X-Profile-Id': string; 'X-User-Password': string }) {
    return apiClient.delete<CoursePlaceHeartDto>(apiEndpoints.heartCoursePlace(coursePlaceId), { headers })
  }

  async completeCurrentCourse(payload: CompleteCourseRequestDto, headers: { 'X-Profile-Id': string; 'X-User-Password': string }) {
    return apiClient.post<CompleteDateCourseDto>(apiEndpoints.completeCurrentCourse, payload, { headers })
  }
}

export const courseRepository = new CourseRepositoryImpl()
