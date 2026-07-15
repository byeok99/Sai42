import { apiClient } from '@/services/api/client'
import { apiEndpoints } from '@/services/api/endpoints'
import type { BaseDto } from '@/types/api/common'
import type { ProfileCreateRequestDto, ProfileMeDto, ProfileVerifyRequestDto, NicknameSuggestionDto } from '@/types/api/identity'

export interface IdentityRepository {
  getNicknameSuggestions(): Promise<BaseDto<NicknameSuggestionDto[]>>
  createProfile(payload: ProfileCreateRequestDto): Promise<BaseDto<ProfileMeDto>>
  verifyProfile(payload: ProfileVerifyRequestDto): Promise<BaseDto<ProfileMeDto>>
  getMe(headers?: { 'X-Profile-Id': string; 'X-User-Password': string }): Promise<BaseDto<ProfileMeDto>>
}

export class IdentityRepositoryImpl implements IdentityRepository {
  async getNicknameSuggestions() {
    return apiClient.get<NicknameSuggestionDto[]>(apiEndpoints.nicknameSuggestions)
  }

  async createProfile(payload: any) {
    return apiClient.post<ProfileMeDto>(apiEndpoints.profiles, payload)
  }

  async verifyProfile(payload: any) {
    return apiClient.post<ProfileMeDto>(apiEndpoints.verify, payload)
  }

  async getMe(headers: any) {
    return apiClient.get<ProfileMeDto>(apiEndpoints.me, { headers })
  }
}

export const identityRepository = new IdentityRepositoryImpl()
