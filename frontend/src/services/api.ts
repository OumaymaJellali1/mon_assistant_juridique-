import type { ApiChatRequest, ApiChatResponse, ApiHealthCheck } from '@/types/api';

const API_BASE_URL = '/api/backend';

export class ApiService {
  private static readonly BASE_URL = API_BASE_URL;

  private static async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Erreur inconnue');
      throw new Error(`Erreur ${response.status}: ${errorText}`);
    }
    
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return response.json();
    }
    
    throw new Error('Réponse non-JSON reçue du serveur');
  }

  static async sendChatMessage(request: ApiChatRequest): Promise<ApiChatResponse> {
    const response = await fetch(`${this.BASE_URL}/v1/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    return this.handleResponse<ApiChatResponse>(response);
  }

  static async testConnection(): Promise<boolean> {
    try {
      const response = await fetch(`${this.BASE_URL}/v1/chat/test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: "Test de connexion",
          user_id: "test_user"
        }),
      });

      return response.ok;
    } catch (error) {
      console.error('Erreur test de connexion:', error);
      return false;
    }
  }

  static async healthCheck(): Promise<ApiHealthCheck> {
    const response = await fetch(`${this.BASE_URL}/v1/health`, {
      method: 'GET',
    });

    return this.handleResponse<ApiHealthCheck>(response);
  }

  static async getDocuments(): Promise<{available_documents: string[], total_count: number}> {
    const response = await fetch(`${this.BASE_URL}/v1/documents`, {
      method: 'GET',
    });

    return this.handleResponse<{available_documents: string[], total_count: number}>(response);
  }

  static getDocumentUrl(documentName: string): string {
    const encodedName = encodeURIComponent(documentName);
    return `${this.BASE_URL}/v1/documents/${encodedName}`;
  }
}