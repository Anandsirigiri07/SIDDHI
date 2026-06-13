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

export interface ForecastFeature {
  type: string;
  geometry: {
    type: string;
    coordinates: [number, number]; // [lng, lat]
  };
  properties: {
    cluster_id: number;
    location_name: string;
    dominant_crime: string;
    historical_weekly_avg: number;
    predicted_weekly_incidents: number;
    predicted_risk_score: number;
    trend: 'Rising' | 'Stable' | 'Declining';
    observation_weeks: number;
  };
}

export interface ForecastData {
  type: string;
  features: ForecastFeature[];
  generated_at: string;
  horizon_days: number;
}

export const fetchForecast = async (): Promise<ForecastData> => {
  const response = await api.get<ForecastData>('/api/forecast');
  return response.data;
};

export interface EntityField<T> {
  value: T;
  confidence: number;
}

export interface FIRData {
  fir_number: EntityField<string>;
  date: EntityField<string>;
  crime_type: EntityField<string>;
  description: EntityField<string>;
  status: EntityField<string>;
  location_name: EntityField<string>;
  station_area: EntityField<string>;
  district: EntityField<string>;
}

export interface AccusedData {
  name: EntityField<string>;
  age: EntityField<number>;
  gender: EntityField<string>;
  occupation: EntityField<string>;
  address: EntityField<string>;
  role: EntityField<string>;
}

export interface VictimData {
  name: EntityField<string>;
  age: EntityField<number>;
  gender: EntityField<string>;
}

export interface IngestDraft {
  fir: FIRData;
  accused: AccusedData[];
  victims: VictimData[];
}

export interface IngestDraftResponse {
  success: boolean;
  metadata: {
    timestamp: string;
    operator: string;
    filename: string;
    file_size_bytes: number;
    mime_type: string;
  };
  draft: IngestDraft;
}

export interface ConfirmIngestPayload {
  fir: {
    fir_number: string;
    date: string;
    crime_type: string;
    description: string;
    status: string;
    location_name: string;
    station_area: string;
    district: string;
  };
  accused: Array<{
    name: string;
    age: number;
    gender: string;
    occupation: string;
    address: string;
    role: string;
  }>;
  victims: Array<{
    name: string;
    age: number;
    gender: string;
  }>;
  document_reference: string;
}

export interface DossierResponse {
  success: boolean;
  query: string;
  dossier: string;
  execution_mode: string;
}

export const generateDossier = async (query: string, sessionId: string): Promise<DossierResponse> => {
  const response = await api.post<DossierResponse>('/api/dossier', { query, session_id: sessionId });
  return response.data;
};

export const parseDocument = async (file: File): Promise<IngestDraftResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post<IngestDraftResponse>('/api/ingest/parse', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const confirmIngestion = async (payload: ConfirmIngestPayload): Promise<{ success: boolean; fir_id: number; fir_number: string }> => {
  const response = await api.post<{ success: boolean; fir_id: number; fir_number: string }>('/api/ingest/confirm', payload);
  return response.data;
};
