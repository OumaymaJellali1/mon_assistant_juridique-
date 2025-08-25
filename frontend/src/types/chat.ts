// src/types/chat.ts
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  conversationId?: string;
}

export interface Conversation {
  id: string;
  title: string;
  createdAt: Date;
  updatedAt: Date;
  messageCount: number;
  lastMessage?: string;
}

export interface ChatState {
  messages: ChatMessage[];
  currentConversationId?: string;
  isLoading: boolean;
  error?: string;
}