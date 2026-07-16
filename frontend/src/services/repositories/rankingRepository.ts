import { apiClient } from '@/services/api/client'
import { apiEndpoints } from '@/services/api/endpoints'
import type { BaseDto } from '@/types/api/common'
import type { DateMastersDto } from '@/types/api/community'

export interface RankingRepository {
  getMasters(): Promise<BaseDto<DateMastersDto>>
}

export class RankingRepositoryImpl implements RankingRepository {
  async getMasters() {
    return apiClient.get<DateMastersDto>(apiEndpoints.rankingsMasters)
  }
}

export const rankingRepository = new RankingRepositoryImpl()
