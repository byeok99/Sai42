import { rankingRepository } from '@/services/repositories/rankingRepository'

export const rankingService = {
  getMasters: () => rankingRepository.getMasters(),
}
