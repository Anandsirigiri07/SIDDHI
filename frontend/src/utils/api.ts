import axios from 'axios';
import { getSessionToken, clearSession } from './auth';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to automatically attach JWT tokens
api.interceptors.request.use(
  (config) => {
    const token = getSessionToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle unauthorized access
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      clearSession();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export interface QueryPayload {
  query: string;
  role: string;
  session_id: string;
}

export interface QueryResponse {
  answer: string;
  graph: {
    nodes: any[];
    links: any[];
    communities: Record<string, number>;
    centrality_scores: Record<string, number>;
    seed_node: string | null;
    community_count: number;
    node_count: number;
    edge_count: number;
    top_central_nodes: any[];
  };
  heatmap: {
    type: string;
    features: any[];
  };
  alerts: Array<{
    type: string;
    message: string;
    severity: string;
  }>;
  citations: string[];
  fir_ids: number[];
  evidence: {
    sql_executed: string;
    explanation: string;
    total_rows_found?: number;
    rows_returned?: number;
  };
  execution_mode: 'gemini' | 'fallback';
  model_used?: string;
  tokens_used?: number;
  intent?: string;
  confidence?: number;
  total_rows_found: number;
  rows_returned: number;
  debug: {
    intent_prompt: string;
    sql_prompt: string;
    summary_prompt: string;
    model_used: string;
    tokens_used: number;
  };
}

export const executeQuery = async (payload: QueryPayload): Promise<QueryResponse> => {
  const response = await api.post<QueryResponse>('/api/query', payload);
  return response.data;
};

export const fetchFIRDetails = async (firId: number): Promise<any> => {
  const response = await api.get(`/api/fir/${firId}`);
  return response.data;
};

export const fetchAuditTrail = async (): Promise<any[]> => {
  const response = await api.get<any[]>('/api/audit');
  return response.data;
};
