// src/api.ts
import { getToken, removeToken } from './utils/auth';

const API_BASE = '/oauth/api/v1';

interface ApiError extends Error {
  status?: number;
}

const request = async <T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> => {
  const url = `${API_BASE}${endpoint}`;
  const token = getToken();

  const config: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  };

  if (token) {
    config.headers = {
      ...config.headers,
      Authorization: `Bearer ${token}`,
    };
  }

  try {
    const response = await fetch(url, config);

    if (response.status === 401) {
      removeToken();
      window.location.href = '/oauth/static/login.html';
      throw new Error('Unauthorized');
    }

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}`;
      try {
        const errorData = await response.json();
        errorMessage = errorData.error_description || errorMessage;
      } catch {
        // fallback to text
        errorMessage = await response.text() || errorMessage;
      }
      const error: ApiError = new Error(errorMessage);
      error.status = response.status;
      throw error;
    }

    return (await response.json()) as T;
  } catch (error) {
    console.error('API 请求失败:', error);
    throw error;
  }
};

export const api = {
  get: <T>(endpoint: string): Promise<T> => request<T>(endpoint, { method: 'GET' }),
  post: <T>(endpoint: string, data: unknown): Promise<T> =>
    request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
};