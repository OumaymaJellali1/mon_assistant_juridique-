export interface Source {
  title?: string;
  document_name?: string;
  url?: string;
  page?: number;
  source?: string;
  relevance_score?: number;
  chunk_id?: string;
  metadata?: Record<string, any>;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  conversationId?: string;
  sources?: Source[]; 
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