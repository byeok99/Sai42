import { communityRepository } from '@/services/repositories/communityRepository'
import type { ApiHeaders } from '@/types/api/common'

export const communityService = {
  listPosts: (
    params?: { sort?: 'POPULAR' | 'LATEST'; page?: number; size?: number },
    headers?: ApiHeaders,
  ) => communityRepository.listPosts(params, headers),
  getPost: (postId: string) => communityRepository.getPost(postId),
  createPost: (
    payload: { courseId: string; oneLineComment: string },
    headers: { 'X-Profile-Id': string; 'X-User-Password': string },
  ) => communityRepository.createPost(payload, headers),
  updatePost: (
    postId: string,
    payload: { oneLineComment: string },
    headers: { 'X-Profile-Id': string; 'X-User-Password': string },
  ) => communityRepository.updatePost(postId, payload, headers),
  deletePost: (postId: string, headers: { 'X-Profile-Id': string; 'X-User-Password': string }) =>
    communityRepository.deletePost(postId, headers),
  likePost: (postId: string, headers: { 'X-Profile-Id': string; 'X-User-Password': string }) =>
    communityRepository.likePost(postId, headers),
  unlikePost: (postId: string, headers: { 'X-Profile-Id': string; 'X-User-Password': string }) =>
    communityRepository.unlikePost(postId, headers),
  startPost: (
    postId: string,
    payload: { date: string; startTime: string },
    headers: { 'X-Profile-Id': string; 'X-User-Password': string },
  ) => communityRepository.startPost(postId, payload, headers),
}
