import {
  mapChatSessionResponse,
  mapConfirmChatSessionResponse,
  mapCreateChatSessionResponse,
  mapSendChatMessageResponse,
  validateDiscardChatSessionResponse,
} from '@/services/mappers/chatMapper'
import { chatRepository } from '@/services/repositories/chatRepository'
import type {
  ConfirmChatSessionRequestDto,
  CreateChatSessionRequestDto,
  SendChatMessageRequestDto,
} from '@/types/api/chat'
import type { AuthenticatedApiHeaders } from '@/types/api/common'

export const chatService = {
  async createSession(payload: CreateChatSessionRequestDto, headers: AuthenticatedApiHeaders) {
    return mapCreateChatSessionResponse(await chatRepository.createSession(payload, headers))
  },

  async getSession(sessionId: string, headers: AuthenticatedApiHeaders) {
    return mapChatSessionResponse(await chatRepository.getSession(sessionId, headers))
  },

  async sendMessage(
    sessionId: string,
    payload: SendChatMessageRequestDto,
    headers: AuthenticatedApiHeaders,
  ) {
    return mapSendChatMessageResponse(await chatRepository.sendMessage(sessionId, payload, headers))
  },

  async confirmSession(
    sessionId: string,
    payload: ConfirmChatSessionRequestDto,
    headers: AuthenticatedApiHeaders,
  ) {
    return mapConfirmChatSessionResponse(
      await chatRepository.confirmSession(sessionId, payload, headers),
    )
  },

  async discardSession(sessionId: string, headers: AuthenticatedApiHeaders) {
    return validateDiscardChatSessionResponse(
      await chatRepository.discardSession(sessionId, headers),
    )
  },
}
