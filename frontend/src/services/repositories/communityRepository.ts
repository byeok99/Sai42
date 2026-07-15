import { apiClient } from '@/services/api/client'
import { apiEndpoints } from '@/services/api/endpoints'
import type { BaseDto } from '@/types/api/common'
import type { CommunityPostCreateRequestDto, CommunityPostDetailDto, CommunityPostLikeDto, CommunityPostSummaryDto, CommunityPostUpdateRequestDto } from '@/types/api/community'

export interface CommunityRepository {
  listPosts(params?: { sort?: 'POPULAR' | 'LATEST' }): Promise<BaseDto<CommunityPostSummaryDto[]>>
  getPost(postId: string): Promise<BaseDto<CommunityPostDetailDto>>
  createPost(payload: CommunityPostCreateRequestDto, headers: { 'X-Profile-Id': string; 'X-User-Password': string }): Promise<BaseDto<CommunityPostDetailDto>>
  updatePost(postId: string, payload: CommunityPostUpdateRequestDto, headers: { 'X-Profile-Id': string; 'X-User-Password': string }): Promise<BaseDto<CommunityPostDetailDto>>
  deletePost(postId: string, headers: { 'X-Profile-Id': string; 'X-User-Password': string }): Promise<BaseDto<unknown>>
  likePost(postId: string, headers: { 'X-Profile-Id': string; 'X-User-Password': string }): Promise<BaseDto<CommunityPostLikeDto>>
  unlikePost(postId: string, headers: { 'X-Profile-Id': string; 'X-User-Password': string }): Promise<BaseDto<CommunityPostLikeDto>>
  startPost(postId: string, headers: { 'X-Profile-Id': string; 'X-User-Password': string }): Promise<BaseDto<unknown>>
}

export class CommunityRepositoryImpl implements CommunityRepository {
  async listPosts(params) {
    return apiClient.get<CommunityPostSummaryDto[]>(apiEndpoints.communityPosts, { params })
  }

  async getPost(postId) {
    return apiClient.get<CommunityPostDetailDto>(apiEndpoints.communityPostDetail(postId))
  }

  async createPost(payload, headers) {
    return apiClient.post<CommunityPostDetailDto>(apiEndpoints.communityPosts, payload, { headers })
  }

  async updatePost(postId, payload, headers) {
    return apiClient.patch<CommunityPostDetailDto>(apiEndpoints.communityPostDetail(postId), payload, { headers })
  }

  async deletePost(postId, headers) {
    return apiClient.delete(apiEndpoints.communityPostDetail(postId), { headers })
  }

  async likePost(postId, headers) {
    return apiClient.put<CommunityPostLikeDto>(apiEndpoints.communityPostLike(postId), undefined, { headers })
  }

  async unlikePost(postId, headers) {
    return apiClient.delete<CommunityPostLikeDto>(apiEndpoints.communityPostLike(postId), { headers })
  }

  async startPost(postId, headers) {
    return apiClient.post(apiEndpoints.communityPostStart(postId), undefined, { headers })
  }
}

export const communityRepository = new CommunityRepositoryImpl()
