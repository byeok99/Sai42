import { apiClient } from '@/services/api/client'
import { apiEndpoints } from '@/services/api/endpoints'
import type { BaseDto } from '@/types/api/common'
import type {
  CommunityPostCreateRequestDto,
  CommunityPostDetailDto,
  CommunityPostLikeDto,
  CommunityPostSummaryDto,
  CommunityPostUpdateRequestDto,
  StartCommunityCourseDto,
} from '@/types/api/community'

export interface CommunityRepository {
  listPosts(params?: { sort?: 'POPULAR' | 'LATEST' }): Promise<BaseDto<CommunityPostSummaryDto[]>>
  getPost(postId: string): Promise<BaseDto<CommunityPostDetailDto>>
  createPost(
    payload: CommunityPostCreateRequestDto,
    headers: { 'X-Profile-Id': string; 'X-User-Password': string },
  ): Promise<BaseDto<CommunityPostDetailDto>>
  updatePost(
    postId: string,
    payload: CommunityPostUpdateRequestDto,
    headers: { 'X-Profile-Id': string; 'X-User-Password': string },
  ): Promise<BaseDto<CommunityPostDetailDto>>
  deletePost(
    postId: string,
    headers: { 'X-Profile-Id': string; 'X-User-Password': string },
  ): Promise<BaseDto<unknown>>
  likePost(
    postId: string,
    headers: { 'X-Profile-Id': string; 'X-User-Password': string },
  ): Promise<BaseDto<CommunityPostLikeDto>>
  unlikePost(
    postId: string,
    headers: { 'X-Profile-Id': string; 'X-User-Password': string },
  ): Promise<BaseDto<CommunityPostLikeDto>>
  startPost(
    postId: string,
    payload: { date: string; startTime: string },
    headers: { 'X-Profile-Id': string; 'X-User-Password': string },
  ): Promise<BaseDto<StartCommunityCourseDto>>
}

export class CommunityRepositoryImpl implements CommunityRepository {
  async listPosts(params?: { sort?: 'POPULAR' | 'LATEST' }) {
    return apiClient.get<CommunityPostSummaryDto[]>(apiEndpoints.communityPosts, { params })
  }

  async getPost(postId: string) {
    return apiClient.get<CommunityPostDetailDto>(apiEndpoints.communityPostDetail(postId))
  }

  async createPost(
    payload: CommunityPostCreateRequestDto,
    headers: { 'X-Profile-Id': string; 'X-User-Password': string },
  ) {
    return apiClient.post<CommunityPostDetailDto>(apiEndpoints.communityPosts, payload, { headers })
  }

  async updatePost(
    postId: string,
    payload: CommunityPostUpdateRequestDto,
    headers: { 'X-Profile-Id': string; 'X-User-Password': string },
  ) {
    return apiClient.patch<CommunityPostDetailDto>(
      apiEndpoints.communityPostDetail(postId),
      payload,
      { headers },
    )
  }

  async deletePost(postId: string, headers: { 'X-Profile-Id': string; 'X-User-Password': string }) {
    return apiClient.delete(apiEndpoints.communityPostDetail(postId), { headers })
  }

  async likePost(postId: string, headers: { 'X-Profile-Id': string; 'X-User-Password': string }) {
    return apiClient.put<CommunityPostLikeDto>(apiEndpoints.communityPostLike(postId), undefined, {
      headers,
    })
  }

  async unlikePost(postId: string, headers: { 'X-Profile-Id': string; 'X-User-Password': string }) {
    return apiClient.delete<CommunityPostLikeDto>(apiEndpoints.communityPostLike(postId), {
      headers,
    })
  }

  async startPost(
    postId: string,
    payload: { date: string; startTime: string },
    headers: { 'X-Profile-Id': string; 'X-User-Password': string },
  ) {
    return apiClient.post<StartCommunityCourseDto>(
      apiEndpoints.communityPostStart(postId),
      payload,
      { headers },
    )
  }
}

export const communityRepository = new CommunityRepositoryImpl()
