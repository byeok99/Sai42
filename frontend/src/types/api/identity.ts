export interface NicknameSuggestionsDto {
  suggestions: string[]
}

export interface ProfileCreateRequestDto {
  nickname: string
  password: string
}

export interface ProfileVerifyRequestDto {
  nickname: string
  password: string
}

export interface ProfileCreatedDto {
  profileId: string
  nickname: string
  hasActiveDateCourse: boolean
  completedDateCourseCount: number
  createdAt: string
}

export interface ProfileVerifiedDto {
  profileId: string
  nickname: string
  hasActiveDateCourse: boolean
  completedDateCourseCount: number
  verifiedAt: string
}

export interface MyProfileDto {
  profileId: string
  nickname: string
  hasActiveDateCourse: boolean
  completedDateCourseCount: number
  publishedCourseCount: number
  createdAt: string
}
