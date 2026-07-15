import { apiClient } from '@/services/api/client'
import { apiEndpoints } from '@/services/api/endpoints'
import type {
  ChatSessionDto,
  ConfirmChatSessionRequestDto,
  CreateChatSessionDto,
  CreateChatSessionRequestDto,
  SendChatMessageDto,
  SendChatMessageRequestDto,
} from '@/types/api/chat'
import type { AuthenticatedApiHeaders, BaseDto } from '@/types/api/common'
import type { DateCourseDto } from '@/types/api/course'

export interface ChatRepository {
  createSession(
    payload: CreateChatSessionRequestDto,
    headers: AuthenticatedApiHeaders,
  ): Promise<BaseDto<CreateChatSessionDto>>
  getSession(sessionId: string, headers: AuthenticatedApiHeaders): Promise<BaseDto<ChatSessionDto>>
  sendMessage(
    sessionId: string,
    payload: SendChatMessageRequestDto,
    headers: AuthenticatedApiHeaders,
  ): Promise<BaseDto<SendChatMessageDto>>
  confirmSession(
    sessionId: string,
    payload: ConfirmChatSessionRequestDto,
    headers: AuthenticatedApiHeaders,
  ): Promise<BaseDto<DateCourseDto>>
  discardSession(sessionId: string, headers: AuthenticatedApiHeaders): Promise<BaseDto<null>>
}

export class ChatRepositoryImpl implements ChatRepository {
  async createSession(
    payload: CreateChatSessionRequestDto,
    headers: AuthenticatedApiHeaders,
  ): Promise<BaseDto<CreateChatSessionDto>> {
    return apiClient.post<CreateChatSessionDto>(apiEndpoints.chatSessions, payload, { headers })
  }

  async getSession(
    sessionId: string,
    headers: AuthenticatedApiHeaders,
  ): Promise<BaseDto<ChatSessionDto>> {
    return apiClient.get<ChatSessionDto>(apiEndpoints.chatSessionDetail(sessionId), { headers })
  }

  async sendMessage(
    sessionId: string,
    payload: SendChatMessageRequestDto,
    headers: AuthenticatedApiHeaders,
  ): Promise<BaseDto<SendChatMessageDto>> {
    return apiClient.post<SendChatMessageDto>(
      apiEndpoints.chatSessionMessages(sessionId),
      payload,
      { headers },
    )
  }

  async confirmSession(
    sessionId: string,
    payload: ConfirmChatSessionRequestDto,
    headers: AuthenticatedApiHeaders,
  ): Promise<BaseDto<DateCourseDto>> {
    return apiClient.post<DateCourseDto>(apiEndpoints.chatSessionConfirm(sessionId), payload, {
      headers,
    })
  }

  async discardSession(
    sessionId: string,
    headers: AuthenticatedApiHeaders,
  ): Promise<BaseDto<null>> {
    return apiClient.delete<null>(apiEndpoints.chatSessionDetail(sessionId), { headers })
  }
}

export const chatRepository = new ChatRepositoryImpl()
