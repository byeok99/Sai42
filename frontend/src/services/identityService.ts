import { identityRepository } from '@/services/repositories/identityRepository'

export const identityService = {
  getNicknameSuggestions: () => identityRepository.getNicknameSuggestions(),
  createProfile: (payload: { nickname: string; password: string }) => identityRepository.createProfile(payload),
  verifyProfile: (payload: { nickname: string; password: string }) => identityRepository.verifyProfile(payload),
  getMe: (headers: { 'X-Profile-Id': string; 'X-User-Password': string }) => identityRepository.getMe(headers),
}
