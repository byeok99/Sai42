import { chatRepository } from '@/services/repositories/chatRepository'

export const chatService = {
  createSession: (payload: { date: string; timeSlot: string; startTime: string; district: string; spaceType: string; moods: string[]; activities: string[]; scheduleDensity: string; transportation: string }, headers: { 'X-Profile-Id': string; 'X-User-Password': string }) => chatRepository.createSession(payload, headers),
  getSession: (sessionId: string, headers: { 'X-Profile-Id': string; 'X-User-Password': string }) => chatRepository.getSession(sessionId, headers),
  sendMessage: (sessionId: string, payload: { content: string }, headers: { 'X-Profile-Id': string; 'X-User-Password': string }) => chatRepository.sendMessage(sessionId, payload, headers),
  confirmSession: (sessionId: string, headers: { 'X-Profile-Id': string; 'X-User-Password': string }) => chatRepository.confirmSession(sessionId, headers),
  discardSession: (sessionId: string, headers: { 'X-Profile-Id': string; 'X-User-Password': string }) => chatRepository.discardSession(sessionId, headers),
}
