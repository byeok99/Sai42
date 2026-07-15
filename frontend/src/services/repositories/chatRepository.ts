import { apiClient } from '@/services/api/client'
import { apiEndpoints } from '@/services/api/endpoints'
import type { BaseDto } from '@/types/api/common'
import type { ChatSessionCreateRequestDto, ChatSessionDto } from '@/types/api/chat'

export interface ChatRepository {
  createSession(payload: ChatSessionCreateRequestDto, headers: { 'X-Profile-Id': string; 'X-User-Password': string }): Promise<BaseDto<ChatSessionDto>>
  getSession(sessionId: string, headers: { 'X-Profile-Id': string; 'X-User-Password': string }): Promise<BaseDto<ChatSessionDto>>
  sendMessage(sessionId: string, payload: { content: string }, headers: { 'X-Profile-Id': string; 'X-User-Password': string }): Promise<BaseDto<ChatSessionDto>>
  confirmSession(sessionId: string, headers: { 'X-Profile-Id': string; 'X-User-Password': string }): Promise<BaseDto<ChatSessionDto>>
  discardSession(sessionId: string, headers: { 'X-Profile-Id': string; 'X-User-Password': string }): Promise<BaseDto<unknown>>
}

export class ChatRepositoryImpl implements ChatRepository {
  async createSession(payload, headers) {
    return apiClient.post<ChatSessionDto>(apiEndpoints.chatSessions, payload, { headers })
  }

  async getSession(sessionId, headers) {
    return apiClient.get<ChatSessionDto>(apiEndpoints.chatSessionDetail(sessionId), { headers })
  }

  async sendMessage(sessionId, payload, headers) {
    return apiClient.post<ChatSessionDto>(apiEndpoints.chatSessionMessages(sessionId), payload, { headers })
  }

  async confirmSession(sessionId, headers) {
    return apiClient.post<ChatSessionDto>(apiEndpoints.chatSessionConfirm(sessionId), undefined, { headers })
  }

  async discardSession(sessionId, headers) {
    return apiClient.delete(apiEndpoints.chatSessionDetail(sessionId), { headers })
  }
}

export const chatRepository = new ChatRepositoryImpl()
