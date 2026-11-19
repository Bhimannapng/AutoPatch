/// <reference types="vite/client" />

const DEFAULT_BACKEND_URL: string = import.meta.env.VITE_API_BASE_URL || '';

export const getApiBaseUrl = (): string => {
  const stored = localStorage.getItem('autopatch_cloud_backend_url');
  if (stored && stored.trim()) {
    return stored.trim().replace(/\/+$/, '');
  }
  return DEFAULT_BACKEND_URL.replace(/\/+$/, '');
};

export const setApiBaseUrl = (url: string) => {
  if (url && url.trim()) {
    localStorage.setItem('autopatch_cloud_backend_url', url.trim().replace(/\/+$/, ''));
  } else {
    localStorage.removeItem('autopatch_cloud_backend_url');
  }
};

export const getApiUrl = (endpoint: string): string => {
  const base = getApiBaseUrl();
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return base ? `${base}${cleanEndpoint}` : cleanEndpoint;
};

export const apiFetch = (url: string, init?: RequestInit): Promise<Response> => {
  return fetch(getApiUrl(url), init);
};
