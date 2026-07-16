
import { ApiRequestError } from '@/services/api/client'
import { weatherRepository, type WeatherQuery } from '@/services/repositories/weatherRepository'
import type { WeatherSummaryDto } from '@/types/api/course'

const WEATHER_TIMEOUT_MS = 7_000
const WEATHER_RETRY_COUNT = 3

export const weatherService = {
  async getWeatherWithRetry(query: WeatherQuery): Promise<WeatherSummaryDto | null> {
    for (let attempt = 0; attempt <= WEATHER_RETRY_COUNT; attempt += 1) {
      try {
        const weather = (await weatherRepository.getWeather(query, WEATHER_TIMEOUT_MS)).data
        if (weather?.available) return weather
      } catch (error) {
        if (error instanceof ApiRequestError && error.status >= 400 && error.status < 500)
          return null
        // The weather endpoint is retried below without retrying chat-session creation.
      }
    }
    return null
  },

}
