// src/services/api.ts
import axios, { AxiosResponse } from 'axios';
import { API_BASE_URL, API_ENDPOINTS } from '@/utils/constants';
import type { 
  ApiChatRequest, 
  ApiChatResponse, 
  ApiHealthCheck, 
  ApiError 
} from '@/types/api';

// Configuration axios avec interceptors
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 secondes pour laisser le temps à votre agent de traiter
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor pour les requêtes
apiClient.interceptors.request.use(
  (config) => {
    console.log(` API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error(' Request Error:', error);
    return Promise.reject(error);
  }
);

// Interceptor pour les réponses
apiClient.interceptors.response.use(
  (response) => {
    console.log(` API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error(' Response Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Service API principal
export class ApiService {
  
  // Méthode de health check
  static async healthCheck(): Promise<ApiHealthCheck> {
    try {
      const response: AxiosResponse<ApiHealthCheck> = await apiClient.get(API_ENDPOINTS.HEALTH);
      return response.data;
    } catch (error) {
      console.error('Health check failed:', error);
      throw new Error('Service indisponible');
    }
  }

  // Méthode pour envoyer un message de chat
  static async sendChatMessage(request: ApiChatRequest): Promise<ApiChatResponse> {
    try {
      const response: AxiosResponse<ApiChatResponse> = await apiClient.post(
        API_ENDPOINTS.CHAT, 
        request
      );
      return response.data;
    } catch (error: any) {
      console.error('Chat message failed:', error);
      
      // Gestion des erreurs spécifiques
      if (error.response?.status === 400) {
        throw new Error(error.response.data.detail || 'Requête invalide');
      } else if (error.response?.status === 500) {
        throw new Error('Erreur du serveur. Veuillez réessayer.');
      } else if (error.code === 'ECONNREFUSED') {
        throw new Error('Impossible de se connecter au serveur');
      } else {
        throw new Error('Erreur de communication avec le serveur');
      }
    }
  }

  // Méthode de test
  static async testConnection(): Promise<boolean> {
    try {
      const response = await apiClient.post(API_ENDPOINTS.TEST);
      return response.data.test_status === 'success';
    } catch (error) {
      console.error('Test connection failed:', error);
      return false;
    }
  }

  // Récupérer les conversations actives
  static async getConversations(): Promise<any> {
    try {
      const response = await apiClient.get(API_ENDPOINTS.CONVERSATIONS);
      return response.data;
    } catch (error) {
      console.error('Get conversations failed:', error);
      throw new Error('Impossible de récupérer les conversations');
    }
  }
}