// src/hooks/useChat.ts
import { useState, useCallback, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { ChatService } from '@/services/chatService';
import type { ChatMessage, ChatState, Conversation } from '@/types/chat';

export function useChat() {
  const [state, setState] = useState<ChatState>({
    messages: [],
    currentConversationId: undefined,
    isLoading: false,
    error: undefined
  });

  const [conversations, setConversations] = useState<Conversation[]>([]);

  // Créer une nouvelle conversation
  const startNewConversation = useCallback(() => {
    const newConversationId = uuidv4();
    
    setState(prev => ({
      ...prev,
      messages: [],
      currentConversationId: newConversationId,
      error: undefined
    }));

    // Ajouter à la liste des conversations
    const newConversation: Conversation = {
      id: newConversationId,
      title: 'Nouvelle consultation',
      createdAt: new Date(),
      updatedAt: new Date(),
      messageCount: 0
    };

    setConversations(prev => [newConversation, ...prev]);
    
    return newConversationId;
  }, []);

  // Envoyer un message
  const sendMessage = useCallback(async (message: string) => {
    if (!message.trim()) return;

    // Obtenir ou créer un ID de conversation
    let conversationId = state.currentConversationId;
    if (!conversationId) {
      conversationId = startNewConversation();
    }

    // Commencer le chargement
    setState(prev => ({ 
      ...prev, 
      isLoading: true, 
      error: undefined 
    }));

    try {
      // Appel du service
      const { messages: newMessages } = await ChatService.sendMessage(
        message, 
        conversationId,
        'user_001' // Vous pouvez adapter selon votre système d'auth
      );

      // Mise à jour des messages
      setState(prev => ({
        ...prev,
        messages: [...prev.messages, ...newMessages],
        isLoading: false,
        currentConversationId: conversationId
      }));

      // Mise à jour de la conversation
      setConversations(prev => 
        prev.map(conv => 
          conv.id === conversationId 
            ? {
                ...conv,
                updatedAt: new Date(),
                messageCount: conv.messageCount + 2,
                lastMessage: message.length > 50 ? message.substring(0, 50) + '...' : message,
                title: conv.messageCount === 0 ? (message.length > 30 ? message.substring(0, 30) + '...' : message) : conv.title
              }
            : conv
        )
      );

    } catch (error: any) {
      console.error('Error sending message:', error);
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error.message || 'Erreur lors de l\'envoi du message'
      }));
    }
  }, [state.currentConversationId, startNewConversation]);

  // Charger une conversation existante
  const loadConversation = useCallback((conversationId: string) => {
    // Pour l'instant, on charge depuis le state local
    // Vous pouvez étendre cela pour charger depuis l'API
    setState(prev => ({
      ...prev,
      currentConversationId: conversationId,
      messages: [], // Ici vous pourriez charger les messages sauvegardés
      error: undefined
    }));
  }, []);

  // Effacer l'erreur
  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: undefined }));
  }, []);

  // Initialisation avec une conversation par défaut
  useEffect(() => {
    if (conversations.length === 0) {
      startNewConversation();
    }
  }, [conversations.length, startNewConversation]);

  return {
    // État
    messages: state.messages,
    conversations,
    currentConversationId: state.currentConversationId,
    isLoading: state.isLoading,
    error: state.error,
    
    // Actions
    sendMessage,
    startNewConversation,
    loadConversation,
    clearError
  };
}
