import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';
const API_KEY = import.meta.env.VITE_API_KEY || 'dev-test-key-12345';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY,
  },
});

// Append Auth token and handle 401s globally
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      // Optional: dispatch event so UI knows to show login modal
      window.dispatchEvent(new Event('auth:unauthorized'));
    }
    return Promise.reject(error);
  }
);

export interface Source {
  document_id: string;
  filename: string;
  chunk_index: number;
  content: string;
  relevance_score: number;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  sources?: Source[];
  confidence?: number;
  chart_id?: string;
  chart_data?: any;
}

export interface Document {
  id: string;
  filename: string;
  original_filename: string;
  file_size: number;
  file_type: string;
  status: 'processing' | 'ready' | 'failed';
  created_at: string;
  metadata?: Record<string, any>;
}

export interface Conversation {
  id: string;
  title: string;
  is_favorite?: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  token: string;
  user: {
    id: string;
    email: string;
  };
}

export interface ChatResponse {
  message: Message;
  sources?: Source[];
  chart_data?: Record<string, any>;
}

// Upload document
export const uploadDocument = async (file: File, sessionId: string): Promise<Document> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('session_id', sessionId);

  const response = await api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

// Send chat message
export const sendMessage = async (
  message: string,
  conversationId: string,
  sessionId: string
): Promise<ChatResponse> => {
  const response = await api.post('/chat', {
    message,
    conversation_id: conversationId,
    session_id: sessionId,
  });

  return response.data;
};

// Get conversation history
export const getConversationHistory = async (conversationId: string): Promise<Message[]> => {
  const response = await api.get(`/conversations/${conversationId}/messages`);
  return response.data;
};

// Get user documents
export const getDocuments = async (sessionId: string): Promise<Document[]> => {
  const response = await api.get(`/documents/${sessionId}`);
  return response.data;
};

// Create new conversation
export const createConversation = async (sessionId: string): Promise<Conversation> => {
  const response = await api.post(`/conversations?session_id=${encodeURIComponent(sessionId)}`);
  return response.data;
};

// Get all conversations
export const getConversations = async (sessionId: string): Promise<Conversation[]> => {
  const response = await api.get(`/sessions/${sessionId}/conversations`);
  return response.data;
};

// Delete conversation
export const deleteConversation = async (conversationId: string): Promise<void> => {
  await api.delete(`/conversations/${conversationId}`);
};

// Delete document
export const deleteDocument = async (documentId: string): Promise<void> => {
  await api.delete(`/documents/${documentId}`);
};

// ── Auth & User Endpoints ──

export const login = async (email: string, password: string): Promise<AuthResponse> => {
  const response = await api.post('/auth/login', { email, password });
  if (response.data.token) {
    localStorage.setItem('auth_token', response.data.token);
  }
  return response.data;
};

export const register = async (email: string, password: string): Promise<AuthResponse> => {
  const response = await api.post('/auth/register', { email, password });
  if (response.data.token) {
    localStorage.setItem('auth_token', response.data.token);
  }
  return response.data;
};

export const toggleFavorite = async (conversationId: string): Promise<{ is_favorite: boolean }> => {
  const response = await api.patch(`/conversations/${conversationId}/favorite`);
  return response.data;
};

// Delete session (all data)
export const deleteSession = async (sessionId: string): Promise<void> => {
  await api.delete(`/sessions/${sessionId}`);
};

export default api;
