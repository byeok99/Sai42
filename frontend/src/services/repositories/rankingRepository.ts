import { apiClient } from '@/services/api/client'
import { apiEndpoints } from '@/services/api/endpoints'
import type { BaseDto } from '@/types/api/common'
import type { DateMastersDto } from '@/types/api/community'

export interface RankingRepository {
  getMasters(limit?: number): Promise<BaseDto<DateMastersDto>>
}

export class RankingRepositoryImpl implements RankingRepository {
  async getMasters(limit = 50) {
    return apiClient.get<DateMastersDto>(apiEndpoints.rankingsMasters, { params: { limit } })
  }
}

export const rankingRepository = new RankingRepositoryImpl()
