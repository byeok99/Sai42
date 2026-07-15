import { placeRepository } from '@/services/repositories/placeRepository'

export const placeService = {
  listPlaces: (params?: { district?: string; spaceType?: string; mood?: string; activity?: string }) => placeRepository.listPlaces(params),
  getPlaceDetail: (contentId: string) => placeRepository.getPlaceDetail(contentId),
  getNearbyPlaces: (contentId: string) => placeRepository.getNearbyPlaces(contentId),
}
