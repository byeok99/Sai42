import { weatherRepository, type WeatherQuery } from '@/services/repositories/weatherRepository'
import type { ApiHeaders } from '@/types/api/common'

export const weatherService = {
  getWeather: (query: WeatherQuery, headers?: ApiHeaders) =>
    weatherRepository.getWeather(query, headers),
}
