// src/services/chatService.ts - Version corrigée
import { v4 as uuidv4 } from 'uuid';
import { ApiService } from './api';
import type { ChatMessage, ChatState, Source } from '@/types/chat';
import type { ApiChatRequest } from '@/types/api';

export class ChatService {
  
  static createMessageFromApi(response: any, userMessage: string): ChatMessage[] {
    const userMsg: ChatMessage = {
      id: uuidv4(),
      role: 'user',
      content: userMessage,
      timestamp: new Date(),
      conversationId: response.conversation_id
    };

    const assistantMsg: ChatMessage = {
      id: uuidv4(),
      role: 'assistant', 
      content: response.message,
      timestamp: new Date(response.timestamp),
      conversationId: response.conversation_id,
      sources: this.processApiSources(response.sources) 
    };

    return [userMsg, assistantMsg];
  }

  static processApiSources(apiSources: any[]): Source[] {
    if (!apiSources || !Array.isArray(apiSources)) {
      return [];
    }

    console.log(' Sources reçues de l\'API:', apiSources);

    return apiSources
      .filter(source => source && typeof source === 'object')
      .map((source, index) => {
        console.log(` Traitement source ${index}:`, source);

        const processedSource: Source = {
          title: source.title || source.document_name || source.filename,
          document_name: source.document_name || source.title,
          page: source.page || source.page_number,
          source: source.source || source.file_path,
          relevance_score: source.relevance_score || source.similarity || source.score,
          chunk_id: source.chunk_id || source.id,
          metadata: source.metadata || {}
        };

        if (source.document_name) {
          let documentName = source.document_name;
          
          if (documentName.includes('__')) {
            documentName = documentName.replace(/__/g, '_');
            console.log('  Nom corrigé:', documentName);
          }
          
          const encodedName = documentName.includes('%') ? documentName : encodeURIComponent(documentName);
          processedSource.url = `/api/backend/v1/documents/${encodedName}`;
          
          console.log(' URL générée:', processedSource.url);
        }

        if (source.url) {
          console.log('📎 URL fournie par l\'API:', source.url);
          
          if (source.url.includes('/api/v1/documents/')) {
            const documentPath = source.url.split('/api/v1/documents/')[1];
            processedSource.url = `/api/backend/v1/documents/${documentPath}`;
          } else {
            processedSource.url = source.url.replace('http://127.0.0.1:8000', '/api/backend');
          }
          
          console.log(' URL finale:', processedSource.url);
        }

        return processedSource;
      })
      .slice(0, 5); 
  }

  static async sendMessage(
    message: string, 
    conversationId?: string,
    userId?: string
  ): Promise<{ messages: ChatMessage[], conversationId: string }> {
    
    if (!message.trim()) {
      throw new Error('Le message ne peut pas être vide');
    }

    if (message.length > 5000) {
      throw new Error('Message trop long (maximum 5000 caractères)');
    }

    const request: ApiChatRequest = {
      message: message.trim(),
      conversation_id: conversationId,
      user_id: userId || 'anonymous'
    };

    try {
      const response = await ApiService.sendChatMessage(request);
      
      console.log(' Réponse API complète:', response);
      
      const messages = this.createMessageFromApi(response, message);
      
      return {
        messages,
        conversationId: response.conversation_id
      };
      
    } catch (error: any) {
      console.error('ChatService sendMessage error:', error);
      throw error; 
    }
  }

  static async testBackendConnection(): Promise<boolean> {
    try {
      const isHealthy = await ApiService.testConnection();
      const health = await ApiService.healthCheck();
      
      console.log('Backend health:', health);
      return isHealthy && health.status === 'healthy';
      
    } catch (error) {
      console.error('Backend connection test failed:', error);
      return false;
    }
  }
}