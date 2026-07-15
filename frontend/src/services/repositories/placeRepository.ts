import { apiClient } from '@/services/api/client'
import { apiEndpoints } from '@/services/api/endpoints'
import type { BaseDto } from '@/types/api/common'
import type { PlaceDetailDto, PlaceSummaryDto } from '@/types/api/place'

export interface PlaceRepository {
  listPlaces(params?: { district?: string; spaceType?: string; mood?: string; activity?: string }): Promise<BaseDto<PlaceSummaryDto[]>>
  getPlaceDetail(contentId: string): Promise<BaseDto<PlaceDetailDto>>
  getNearbyPlaces(contentId: string): Promise<BaseDto<PlaceSummaryDto[]>>
}

export class PlaceRepositoryImpl implements PlaceRepository {
  async listPlaces(params: any) {
    return apiClient.get<PlaceSummaryDto[]>(apiEndpoints.places, { params })
  }

  async getPlaceDetail(contentId: string) {
    return apiClient.get<PlaceDetailDto>(apiEndpoints.placeDetail(contentId))
  }

  async getNearbyPlaces(contentId: string) {
    return apiClient.get<PlaceSummaryDto[]>(apiEndpoints.placeNearby(contentId))
  }
}

export const placeRepository = new PlaceRepositoryImpl()
