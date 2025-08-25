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

  // Fonction utilitaire pour sauvegarder dans localStorage
  const saveToLocalStorage = useCallback((conversationId: string, messages: ChatMessage[]) => {
    try {
      if (typeof window !== 'undefined') {
        localStorage.setItem(`conversation_${conversationId}`, JSON.stringify(messages));
      }
    } catch (error) {
      console.error('Error saving to localStorage:', error);
    }
  }, []);

  // Fonction utilitaire pour charger depuis localStorage
  const loadFromLocalStorage = useCallback((conversationId: string): ChatMessage[] => {
    try {
      if (typeof window !== 'undefined') {
        const stored = localStorage.getItem(`conversation_${conversationId}`);
        if (stored) {
          const messages = JSON.parse(stored);
          // Reconvertir les timestamps depuis les chaînes JSON
          return messages.map((msg: any) => ({
            ...msg,
            timestamp: new Date(msg.timestamp)
          }));
        }
      }
    } catch (error) {
      console.error('Error loading from localStorage:', error);
    }
    return [];
  }, []);

  // Sauvegarder les conversations
  const saveConversationsToStorage = useCallback((conversations: Conversation[]) => {
    try {
      if (typeof window !== 'undefined') {
        localStorage.setItem('conversations_list', JSON.stringify(conversations));
      }
    } catch (error) {
      console.error('Error saving conversations:', error);
    }
  }, []);

  // Charger les conversations
  const loadConversationsFromStorage = useCallback((): Conversation[] => {
    try {
      if (typeof window !== 'undefined') {
        const stored = localStorage.getItem('conversations_list');
        if (stored) {
          const conversations = JSON.parse(stored);
          // Reconvertir les dates depuis les chaînes JSON
          return conversations.map((conv: any) => ({
            ...conv,
            createdAt: new Date(conv.createdAt),
            updatedAt: new Date(conv.updatedAt)
          }));
        }
      }
    } catch (error) {
      console.error('Error loading conversations:', error);
    }
    return [];
  }, []);

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

    setConversations(prev => {
      const updated = [newConversation, ...prev];
      saveConversationsToStorage(updated);
      return updated;
    });
    
    return newConversationId;
  }, [saveConversationsToStorage]);

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
        'user_001'
      );

      // Mise à jour des messages
      const allMessages = [...state.messages, ...newMessages];
      setState(prev => ({
        ...prev,
        messages: allMessages,
        isLoading: false,
        currentConversationId: conversationId
      }));

      // Sauvegarder les messages dans localStorage
      saveToLocalStorage(conversationId!, allMessages);

      // Mise à jour de la conversation
      setConversations(prev => {
        const updated = prev.map(conv => 
          conv.id === conversationId 
            ? {
                ...conv,
                updatedAt: new Date(),
                messageCount: conv.messageCount + 2,
                lastMessage: message.length > 50 ? message.substring(0, 50) + '...' : message,
                title: conv.messageCount === 0 ? (message.length > 30 ? message.substring(0, 30) + '...' : message) : conv.title
              }
            : conv
        );
        saveConversationsToStorage(updated);
        return updated;
      });

    } catch (error: any) {
      console.error('Error sending message:', error);
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error.message || 'Erreur lors de l\'envoi du message'
      }));
    }
  }, [state.currentConversationId, state.messages, conversations, startNewConversation, saveToLocalStorage, saveConversationsToStorage]);

  // Charger une conversation existante - CORRECTION PRINCIPALE
  const loadConversation = useCallback((conversationId: string) => {
    // Charger les messages de cette conversation depuis localStorage
    const conversationMessages = loadFromLocalStorage(conversationId);
    
    setState(prev => ({
      ...prev,
      currentConversationId: conversationId,
      messages: conversationMessages, // Charger les vrais messages
      error: undefined,
      isLoading: false
    }));
  }, [loadFromLocalStorage]);

  // Supprimer une conversation
  const deleteConversation = useCallback((conversationId: string) => {
    // Supprimer de localStorage
    try {
      if (typeof window !== 'undefined') {
        localStorage.removeItem(`conversation_${conversationId}`);
      }
    } catch (error) {
      console.error('Error deleting conversation from localStorage:', error);
    }

    // Supprimer de la liste
    setConversations(prev => {
      const updated = prev.filter(conv => conv.id !== conversationId);
      saveConversationsToStorage(updated);
      return updated;
    });

    // Si c'était la conversation courante, en créer une nouvelle
    if (state.currentConversationId === conversationId) {
      const newConversationId = uuidv4();
      
      setState(prev => ({
        ...prev,
        messages: [],
        currentConversationId: newConversationId,
        error: undefined
      }));

      const newConversation = {
        id: newConversationId,
        title: 'Nouvelle consultation',
        createdAt: new Date(),
        updatedAt: new Date(),
        messageCount: 0
      };

      setConversations(prev => {
        const updated = [newConversation, ...prev];
        saveConversationsToStorage(updated);
        return updated;
      });
    }
  }, [state.currentConversationId, saveConversationsToStorage]);

  // Effacer l'erreur
  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: undefined }));
  }, []);

  // Initialisation au chargement du composant
  useEffect(() => {
    // Charger les conversations existantes
    const savedConversations = loadConversationsFromStorage();
    
    if (savedConversations.length > 0) {
      setConversations(savedConversations);
      // Charger la conversation la plus récente
      const mostRecent = savedConversations[0];
      const conversationMessages = loadFromLocalStorage(mostRecent.id);
      
      setState(prev => ({
        ...prev,
        currentConversationId: mostRecent.id,
        messages: conversationMessages,
        error: undefined,
        isLoading: false
      }));
    } else {
      // Créer une nouvelle conversation si aucune n'existe
      const newConversationId = uuidv4();
      
      setState(prev => ({
        ...prev,
        messages: [],
        currentConversationId: newConversationId,
        error: undefined
      }));

      const newConversation = {
        id: newConversationId,
        title: 'Nouvelle consultation',
        createdAt: new Date(),
        updatedAt: new Date(),
        messageCount: 0
      };

      setConversations([newConversation]);
      saveConversationsToStorage([newConversation]);
    }
  }, []); // Dépendances vides pour ne s'exécuter qu'une fois

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
    deleteConversation,
    clearError
  };
}