export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export const API_ENDPOINTS = {
  CHAT: '/api/v1/chat',
  HEALTH: '/api/v1/health',
  CONVERSATIONS: '/api/v1/chat/conversations',
  TEST: '/api/v1/chat/test'
} as const;

export const UI_CONSTANTS = {
  MAX_MESSAGE_LENGTH: 5000,
  TYPING_DELAY: 1000,
  AUTO_SCROLL_DELAY: 100
} as const;