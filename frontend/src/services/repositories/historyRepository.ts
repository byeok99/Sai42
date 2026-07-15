import { apiClient } from '@/services/api/client'
import { apiEndpoints } from '@/services/api/endpoints'
import type { BaseDto } from '@/types/api/common'
import type { CurrentCourseDto } from '@/types/api/course'

export interface HistoryRepository {
  listMyDateCourses(headers: { 'X-Profile-Id': string; 'X-User-Password': string }): Promise<BaseDto<CurrentCourseDto[]>>
  getMyDateCourseDetail(courseId: string, headers: { 'X-Profile-Id': string; 'X-User-Password': string }): Promise<BaseDto<CurrentCourseDto>>
  restartCourse(courseId: string, headers: { 'X-Profile-Id': string; 'X-User-Password': string }): Promise<BaseDto<CurrentCourseDto>>
}

export class HistoryRepositoryImpl implements HistoryRepository {
  async listMyDateCourses(headers: any) {
    return apiClient.get<CurrentCourseDto[]>(apiEndpoints.myDateCourses, { headers })
  }

  async getMyDateCourseDetail(courseId: string, headers: any) {
    return apiClient.get<CurrentCourseDto>(apiEndpoints.myDateCourseDetail(courseId), { headers })
  }

  async restartCourse(courseId: string, headers: any) {
    return apiClient.post<CurrentCourseDto>(apiEndpoints.restartDateCourse(courseId), undefined, { headers })
  }

  async deleteMyDateCourse(courseId: string, headers: any) {
    return apiClient.delete<void>(`${apiEndpoints.myDateCourses}/${courseId}`, { headers })
  }
}

export const historyRepository = new HistoryRepositoryImpl()
