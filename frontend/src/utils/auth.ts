// src/utils/auth.ts

export interface UserSession {
  username: string;
  role: string;
  name: string;
}

export const setSession = (token: string, user: UserSession) => {
  localStorage.setItem('siddhi_token', token);
  localStorage.setItem('siddhi_user', json.stringify(user));
};

export const getSessionToken = (): string | null => {
  return localStorage.getItem('siddhi_token');
};

export const getSessionUser = (): UserSession | null => {
  const user = localStorage.getItem('siddhi_user');
  if (user) {
    try {
      return JSON.parse(user);
    } catch {
      return null;
    }
  }
  return null;
};

export const clearSession = () => {
  localStorage.removeItem('siddhi_token');
  localStorage.removeItem('siddhi_user');
};

export const isAuthenticated = (): boolean => {
  return !!getSessionToken();
};

// Simple mock JSON helper for file imports since we run in TS node/bundler
const json = {
  stringify: JSON.stringify,
  parse: JSON.parse
};
