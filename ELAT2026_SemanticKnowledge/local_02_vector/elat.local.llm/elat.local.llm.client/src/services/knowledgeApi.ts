import axios from 'axios';
import type { 
  KnowledgeSearchResult, 
  AddDocumentRequest, 
  AddDocumentResponse, 
  SearchRequest, 
  SearchResponse 
} from '../types/knowledge';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5227/api';

// Token provider function that will be set by the app
let tokenProvider: (() => Promise<string | null>) | null = null;

export const setKnowledgeTokenProvider = (provider: () => Promise<string | null>) => {
  tokenProvider = provider;
};

// Create axios instance with default config
const api = axios.create({
  baseURL: `${API_BASE_URL}/knowledgebase`,
  timeout: 30000,
});

// Add request interceptor to add auth token
api.interceptors.request.use(
  async (config) => {
    if (tokenProvider) {
      const token = await tokenProvider();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export const knowledgeApi = {
  // Search the knowledge base
  search: async (request: SearchRequest): Promise<SearchResponse> => {
    const response = await api.post<SearchResponse>('/search', request);
    return response.data;
  },

  // Add a document to the knowledge base
  addDocument: async (request: AddDocumentRequest): Promise<AddDocumentResponse> => {
    const response = await api.post<AddDocumentResponse>('/documents', request);
    return response.data;
  },

  // Upload a file to the knowledge base
  uploadFile: async (file: File, category?: string): Promise<AddDocumentResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    if (category) {
      formData.append('category', category);
    }

    // Get token for fetch request
    const token = tokenProvider ? await tokenProvider() : null;
    const headers: HeadersInit = {};
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/knowledgebase/upload`, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!response.ok) {
      throw new Error('Failed to upload file');
    }

    return response.json();
  },

  // Delete a document from the knowledge base
  deleteDocument: async (documentId: string): Promise<void> => {
    await api.delete(`/documents/${documentId}`);
  },

  // Get all documents (using search with empty query to get all)
  getAllDocuments: async (): Promise<KnowledgeSearchResult[]> => {
    try {
      // Try the new GET endpoint first
      const response = await api.get<SearchResponse>('/documents?maxResults=100');
      return response.data.results;
    } catch {
      // Fallback to search method if GET endpoint is not available
      try {
        const response = await api.post<SearchResponse>('/search', {
          query: '*', // Try wildcard first
          maxResults: 100
        });
        return response.data.results;
      } catch {
        // If wildcard doesn't work, try common terms
        try {
          const response = await api.post<SearchResponse>('/search', {
            query: 'document text content', // Common terms that might match most documents
            maxResults: 100
          });
          return response.data.results;
        } catch (finalError) {
          console.warn('Could not retrieve all documents:', finalError);
          return [];
        }
      }
    }
  }
};
