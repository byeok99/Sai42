import { rankingRepository } from '@/services/repositories/rankingRepository'

export const rankingService = {
  getMasters: (limit?: number) => rankingRepository.getMasters(limit),
}
