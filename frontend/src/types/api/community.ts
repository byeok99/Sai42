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

export interface DateMasterDto {
  rank: number
  profileId: string
  nickname: string
  publishedCourseCount: number
  receivedLikeCount: number
}

export interface DateMastersDto {
  masters: DateMasterDto[]
}

import type { CourseMapDto, CoursePlaceDto } from '@/types/api/course'

export interface CommunityPostDetailDto {
  postId: string
  owner: boolean
  courseId: string
  courseTitle: string
  authorNickname: string
  oneLineComment: string
  date: string
  timeSlot: string
  overallComment: string
  conditions: unknown
  tags: string[]
  places: CoursePlaceDto[]
  map: CourseMapDto
  courseLikeCount: number
  placeHeartCount: number
  likedByMe: boolean
  publishedAt: string
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

export interface StartCommunityCourseDto {
  activeCourse: import('@/types/api/course').DateCourseDto
  copyResult: { sourcePostId: string; warnings: string[] }
}
