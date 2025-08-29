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

  const saveToLocalStorage = useCallback((conversationId: string, messages: ChatMessage[]) => {
    try {
      if (typeof window !== 'undefined') {
        const serializedMessages = messages.map(msg => ({
          ...msg,
          timestamp: msg.timestamp.toISOString(), 
          sources: msg.sources || [] 
        }));
        localStorage.setItem(`conversation_${conversationId}`, JSON.stringify(serializedMessages));
      }
    } catch (error) {
      console.error('Error saving to localStorage:', error);
    }
  }, []);

  const loadFromLocalStorage = useCallback((conversationId: string): ChatMessage[] => {
    try {
      if (typeof window !== 'undefined') {
        const stored = localStorage.getItem(`conversation_${conversationId}`);
        if (stored) {
          const messages = JSON.parse(stored);
          return messages.map((msg: any) => ({
            ...msg,
            timestamp: new Date(msg.timestamp),
            sources: msg.sources || [] 
          }));
        }
      }
    } catch (error) {
      console.error('Error loading from localStorage:', error);
    }
    return [];
  }, []);

  const saveConversationsToStorage = useCallback((conversations: Conversation[]) => {
    try {
      if (typeof window !== 'undefined') {
        const serializedConversations = conversations.map(conv => ({
          ...conv,
          createdAt: conv.createdAt.toISOString(),
          updatedAt: conv.updatedAt.toISOString()
        }));
        localStorage.setItem('conversations_list', JSON.stringify(serializedConversations));
      }
    } catch (error) {
      console.error('Error saving conversations:', error);
    }
  }, []);

  const loadConversationsFromStorage = useCallback((): Conversation[] => {
    try {
      if (typeof window !== 'undefined') {
        const stored = localStorage.getItem('conversations_list');
        if (stored) {
          const conversations = JSON.parse(stored);
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

  const startNewConversation = useCallback(() => {
    const newConversationId = uuidv4();
    
    setState(prev => ({
      ...prev,
      messages: [],
      currentConversationId: newConversationId,
      error: undefined
    }));

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

  const sendMessage = useCallback(async (message: string) => {
    if (!message.trim()) return;

    let conversationId = state.currentConversationId;
    if (!conversationId) {
      conversationId = startNewConversation();
    }

    setState(prev => ({ 
      ...prev, 
      isLoading: true, 
      error: undefined 
    }));

    try {
      const { messages: newMessages } = await ChatService.sendMessage(
        message, 
        conversationId,
        'user_001'
      );

      const allMessages = [...state.messages, ...newMessages];
      setState(prev => ({
        ...prev,
        messages: allMessages,
        isLoading: false,
        currentConversationId: conversationId
      }));

      saveToLocalStorage(conversationId!, allMessages);

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

  const loadConversation = useCallback((conversationId: string) => {
    const conversationMessages = loadFromLocalStorage(conversationId);
    
    setState(prev => ({
      ...prev,
      currentConversationId: conversationId,
      messages: conversationMessages, 
      error: undefined,
      isLoading: false
    }));
  }, [loadFromLocalStorage]);

  const deleteConversation = useCallback((conversationId: string) => {
    try {
      if (typeof window !== 'undefined') {
        localStorage.removeItem(`conversation_${conversationId}`);
      }
    } catch (error) {
      console.error('Error deleting conversation from localStorage:', error);
    }

    setConversations(prev => {
      const updated = prev.filter(conv => conv.id !== conversationId);
      saveConversationsToStorage(updated);
      return updated;
    });

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

  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: undefined }));
  }, []);

  useEffect(() => {
    const savedConversations = loadConversationsFromStorage();
    
    if (savedConversations.length > 0) {
      setConversations(savedConversations);
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
  }, []); 

  return {
    messages: state.messages,
    conversations,
    currentConversationId: state.currentConversationId,
    isLoading: state.isLoading,
    error: state.error,
    
    sendMessage,
    startNewConversation,
    loadConversation,
    deleteConversation,
    clearError
  };
}