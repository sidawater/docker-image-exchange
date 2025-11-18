// src/types/index.ts
export interface User {
  id: string;
  username: string;
  email?: string;
  created_at?: string;
}

export interface Client {
  client_id: string;
  client_name: string;
  redirect_uris: string[];
  scopes: string[];
  created_at: string;
}

export interface Metrics {
  user_metrics?: {
    total_users: number;
    active_users: number;
  };
  client_metrics?: {
    total_clients: number;
    active_clients: number;
  };
  token_metrics?: {
    active_tokens: number;
    issued_today: number;
  };
}