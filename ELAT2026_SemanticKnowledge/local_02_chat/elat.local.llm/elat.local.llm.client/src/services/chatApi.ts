import axios from 'axios';
import type { ChatSession, CreateChatSessionRequest, SendMessageRequest } from '../types/chat';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5227/api';

// Token provider function that will be set by the app
let tokenProvider: (() => Promise<string | null>) | null = null;

export const setTokenProvider = (provider: () => Promise<string | null>) => {
  tokenProvider = provider;
};

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
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

export const chatApi = {
  // Get all chat sessions
  getChatSessions: async (): Promise<ChatSession[]> => {
    const response = await api.get<ChatSession[]>('/chat/sessions');
    return response.data;
  },

  // Create a new chat session
  createChatSession: async (request: CreateChatSessionRequest): Promise<ChatSession> => {
    const response = await api.post<ChatSession>('/chat/sessions', request);
    return response.data;
  },

  // Get a specific chat session
  getChatSession: async (sessionId: string): Promise<ChatSession> => {
    const response = await api.get<ChatSession>(`/chat/sessions/${sessionId}`);
    return response.data;
  },

  // Update a chat session
  updateChatSession: async (sessionId: string, request: { title: string }): Promise<ChatSession> => {
    const response = await api.put<ChatSession>(`/chat/sessions/${sessionId}`, request);
    return response.data;
  },

  // Delete a chat session
  deleteChatSession: async (sessionId: string): Promise<void> => {
    await api.delete(`/chat/sessions/${sessionId}`);
  },

  // Send a message with optional files
  sendMessage: async (sessionId: string, request: SendMessageRequest): Promise<ReadableStream> => {
    const formData = new FormData();
    formData.append('content', request.content);
    
    if (request.files) {
      request.files.forEach((file) => {
        formData.append('files', file);
      });
    }

    // Get token for fetch request
    const token = tokenProvider ? await tokenProvider() : null;
    const headers: HeadersInit = {};
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/messages`, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!response.ok) {
      throw new Error('Failed to send message');
    }

    return response.body!;
  },

  // Get attachment
  getAttachment: async (attachmentId: string): Promise<Blob> => {
    const response = await api.get(`/chat/attachments/${attachmentId}`, {
      responseType: 'blob',
    });
    return response.data;
  },
};
