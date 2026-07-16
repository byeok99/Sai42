import { apiClient } from '@/services/api/client'
import { apiEndpoints } from '@/services/api/endpoints'
import type { BaseDto } from '@/types/api/common'
import type { District, TimeSlot, WeatherSummaryDto } from '@/types/api/course'

export interface WeatherQuery {
  date: string
  district: District
  timeSlot: TimeSlot
}

export interface WeatherRepository {
  getWeather(query: WeatherQuery, timeoutMs: number): Promise<BaseDto<WeatherSummaryDto>>
}

export class WeatherRepositoryImpl implements WeatherRepository {
  getWeather(query: WeatherQuery, timeoutMs: number): Promise<BaseDto<WeatherSummaryDto>> {
    return apiClient.get<WeatherSummaryDto>(apiEndpoints.weather, {
      params: { ...query },
      timeoutMs,
    })
  }
}

export const weatherRepository = new WeatherRepositoryImpl()
