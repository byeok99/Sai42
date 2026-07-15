import { apiClient } from '@/services/api/client'
import { apiEndpoints } from '@/services/api/endpoints'
import type { BaseDto } from '@/types/api/common'
import type {
  MyProfileDto,
  NicknameSuggestionsDto,
  ProfileCreatedDto,
  ProfileCreateRequestDto,
  ProfileVerifiedDto,
  ProfileVerifyRequestDto,
} from '@/types/api/identity'

export interface IdentityRepository {
  getNicknameSuggestions(): Promise<BaseDto<NicknameSuggestionsDto>>
  createProfile(payload: ProfileCreateRequestDto): Promise<BaseDto<ProfileCreatedDto>>
  verifyProfile(payload: ProfileVerifyRequestDto): Promise<BaseDto<ProfileVerifiedDto>>
  getMe(headers: { 'X-Profile-Id': string; 'X-User-Password': string }): Promise<BaseDto<MyProfileDto>>
}

export class IdentityRepositoryImpl implements IdentityRepository {
  async getNicknameSuggestions() {
    return apiClient.get<NicknameSuggestionsDto>(apiEndpoints.nicknameSuggestions)
  }

  async createProfile(payload: ProfileCreateRequestDto) {
    return apiClient.post<ProfileCreatedDto>(apiEndpoints.profiles, payload)
  }

  async verifyProfile(payload: ProfileVerifyRequestDto) {
    return apiClient.post<ProfileVerifiedDto>(apiEndpoints.verify, payload)
  }

  async getMe(headers: { 'X-Profile-Id': string; 'X-User-Password': string }) {
    return apiClient.get<MyProfileDto>(apiEndpoints.me, { headers })
  }
}

export const identityRepository = new IdentityRepositoryImpl()
