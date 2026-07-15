export interface PlaceSummaryDto {
  contentId: string
  title: string
  address: string
  district?: string
  category?: string
  spaceType?: string
  mood?: string[]
  imageUrl?: string
  latitude?: number
  longitude?: number
  source?: string
}

export interface PlaceDetailDto extends PlaceSummaryDto {
  description?: string
  estimatedStayMinutes?: number
  estimatedCost?: number
  tags?: string[]
}
