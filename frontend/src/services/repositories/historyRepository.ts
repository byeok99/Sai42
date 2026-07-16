import { apiClient } from '@/services/api/client'
import { apiEndpoints } from '@/services/api/endpoints'
import type { BaseDto } from '@/types/api/common'
import type { DateCourseDto, HistoryCourseSummaryDto } from '@/types/api/course'

export interface HistoryListParams {
  year?: number
  month?: number
  page?: number
  size?: number
}

export interface HistoryRepository {
  listMyDateCourses(
    headers: { 'X-Profile-Id': string; 'X-User-Password': string },
    params?: HistoryListParams,
  ): Promise<BaseDto<HistoryCourseSummaryDto[]>>
  getMyDateCourseDetail(
    courseId: string,
    headers: { 'X-Profile-Id': string; 'X-User-Password': string },
  ): Promise<BaseDto<DateCourseDto>>
  restartCourse(
    courseId: string,
    headers: { 'X-Profile-Id': string; 'X-User-Password': string },
  ): Promise<BaseDto<DateCourseDto>>
  deleteMyDateCourse(
    courseId: string,
    headers: { 'X-Profile-Id': string; 'X-User-Password': string },
  ): Promise<BaseDto<void>>
}

export class HistoryRepositoryImpl implements HistoryRepository {
  async listMyDateCourses(
    headers: { 'X-Profile-Id': string; 'X-User-Password': string },
    params?: HistoryListParams,
  ) {
    return apiClient.get<HistoryCourseSummaryDto[]>(apiEndpoints.myDateCourses, {
      headers,
      params: {
        year: params?.year,
        month: params?.month,
        page: params?.page,
        size: params?.size,
      },
    })
  }

  async getMyDateCourseDetail(
    courseId: string,
    headers: { 'X-Profile-Id': string; 'X-User-Password': string },
  ) {
    return apiClient.get<DateCourseDto>(apiEndpoints.myDateCourseDetail(courseId), { headers })
  }

  async restartCourse(
    courseId: string,
    headers: { 'X-Profile-Id': string; 'X-User-Password': string },
  ) {
    return apiClient.post<DateCourseDto>(apiEndpoints.restartDateCourse(courseId), undefined, {
      headers,
    })
  }

  async deleteMyDateCourse(
    courseId: string,
    headers: { 'X-Profile-Id': string; 'X-User-Password': string },
  ) {
    return apiClient.delete<void>(`${apiEndpoints.myDateCourses}/${courseId}`, { headers })
  }
}

export const historyRepository = new HistoryRepositoryImpl()
