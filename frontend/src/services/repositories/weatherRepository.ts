import { apiClient } from '@/services/api/client'
import { apiEndpoints } from '@/services/api/endpoints'
import type { ApiHeaders, BaseDto } from '@/types/api/common'
import type { District, TimeSlot, WeatherSummaryDto } from '@/types/api/course'

export interface WeatherQuery {
  date: string
  district: District
  timeSlot: TimeSlot
}

export interface WeatherRepository {
  getWeather(query: WeatherQuery, headers?: ApiHeaders): Promise<BaseDto<WeatherSummaryDto>>
}

export class WeatherRepositoryImpl implements WeatherRepository {
  async getWeather(query: WeatherQuery, headers?: ApiHeaders) {
    return apiClient.get<WeatherSummaryDto>(apiEndpoints.weather, {
      params: {
        date: query.date,
        district: query.district,
        timeSlot: query.timeSlot,
      },
      headers,
    })
  }
}

export const weatherRepository = new WeatherRepositoryImpl()
