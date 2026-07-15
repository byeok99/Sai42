export interface CommunityPostSummaryDto {
  postId: string
  courseId: string
  courseTitle: string
  authorNickname: string
  oneLineComment: string
  courseLikeCount: number
  placeHeartCount: number
  likedByMe: boolean
  publishedAt: string
  rank?: number
}

export interface CommunityPostDetailDto extends CommunityPostSummaryDto {
  mainDistrict: string
  timeSlot: string
  overallComment: string
  tags: string[]
  places: Array<{
    contentId: string
    title: string
    orderNo: number
    sweetComment: string
  }>
}

export interface CommunityPostCreateRequestDto {
  courseId: string
  oneLineComment: string
}

export interface CommunityPostUpdateRequestDto {
  oneLineComment: string
}
