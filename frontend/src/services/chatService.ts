// src/services/chatService.ts
import { v4 as uuidv4 } from 'uuid';
import { ApiService } from './api';
import type { ChatMessage, ChatState } from '@/types/chat';
import type { ApiChatRequest } from '@/types/api';

export class ChatService {
  
  // Convertit une réponse API en message de chat
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
      conversationId: response.conversation_id
    };

    return [userMsg, assistantMsg];
  }

  // Envoie un message et retourne les nouveaux messages
  static async sendMessage(
    message: string, 
    conversationId?: string,
    userId?: string
  ): Promise<{ messages: ChatMessage[], conversationId: string }> {
    
    // Validation locale
    if (!message.trim()) {
      throw new Error('Le message ne peut pas être vide');
    }

    if (message.length > 5000) {
      throw new Error('Message trop long (maximum 5000 caractères)');
    }

    // Préparation de la requête
    const request: ApiChatRequest = {
      message: message.trim(),
      conversation_id: conversationId,
      user_id: userId || 'anonymous'
    };

    try {
      // Appel à votre API
      const response = await ApiService.sendChatMessage(request);
      
      // Création des messages pour l'interface
      const messages = this.createMessageFromApi(response, message);
      
      return {
        messages,
        conversationId: response.conversation_id
      };
      
    } catch (error: any) {
      console.error('ChatService sendMessage error:', error);
      throw error; // Re-lancer pour gestion dans le composant
    }
  }

  // Test de connexion avec le backend
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