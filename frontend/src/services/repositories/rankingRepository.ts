import { apiClient } from '@/services/api/client'
import { apiEndpoints } from '@/services/api/endpoints'
import type { BaseDto } from '@/types/api/common'
import type { CommunityPostSummaryDto } from '@/types/api/community'

export interface RankingRepository {
  getMasters(): Promise<BaseDto<CommunityPostSummaryDto[]>>
}

export class RankingRepositoryImpl implements RankingRepository {
  async getMasters() {
    return apiClient.get<CommunityPostSummaryDto[]>(apiEndpoints.rankingsMasters)
  }
}

export const rankingRepository = new RankingRepositoryImpl()
