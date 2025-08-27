// src/types/api.ts
import type { Source } from './chat';

export interface ApiChatRequest {
  message: string;
  conversation_id?: string;
  user_id?: string;
}

export interface ApiChatResponse {
  message: string;
  conversation_id: string;
  timestamp: string;
  sources: Source[]; 
}

export interface ApiHealthCheck {
  status: string;
  timestamp: string;
  version: string;
}

export interface ApiError {
  error: string;
  detail?: string;
  timestamp: string;
}