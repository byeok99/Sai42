import { communityRepository } from '@/services/repositories/communityRepository'

export const communityService = {
  listPosts: (params?: { sort?: 'POPULAR' | 'LATEST' }) => communityRepository.listPosts(params),
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
