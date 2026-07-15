export interface CommunityPostSummaryDto {
  postId: string
  courseId: string
  courseTitle: string
  mainDistrict: string
  authorNickname: string
  oneLineComment: string
  courseLikeCount: number
  placeHeartCount: number
  likedByMe: boolean
  tags: string[]
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

export interface CommunityPostLikeDto {
  postId: string
  likedByMe: boolean
  likeCount: number
}
