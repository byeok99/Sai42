export interface NicknameSuggestionDto {
  nickname: string
}

export interface ProfileCreateRequestDto {
  nickname: string
  password: string
}

export interface ProfileVerifyRequestDto {
  nickname: string
  password: string
}

export interface ProfileMeDto {
  id: string
  nickname: string
  createdAt: string
  updatedAt: string
  profileImageUrl?: string | null
  status?: 'ACTIVE' | 'DELETED'
}
