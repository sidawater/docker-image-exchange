// src/utils/auth.ts
export const getToken = (): string | null => localStorage.getItem('access_token');

export const setToken = (token: string): void => {
  localStorage.setItem('access_token', token);
};

export const removeToken = (): void => {
  localStorage.removeItem('access_token');
};