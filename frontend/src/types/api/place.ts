export interface PlaceSummaryDto {
  contentId: string
  name: string
  address: string
  addressDetail?: string
  latitude?: number
  longitude?: number
  imageUrl?: string
  category?: string
  district?: string
  spaceType?: string
  mood?: string[]
}

export interface PlaceDetailDto extends PlaceSummaryDto {
  description?: string
  estimatedStayMinutes?: number
  estimatedCost?: number
}
