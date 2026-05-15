import axios from 'axios';
import { tokenStorage } from '../utils/tokenStorage';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export const client = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
});

// Inject access token on every request
client.interceptors.request.use((config) => {
  const token = tokenStorage.getAccess();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auto-refresh on 401
client.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    const requestUrl = original?.url ?? '';
    const isAuthEndpoint = requestUrl.includes('/auth/login') || requestUrl.includes('/auth/refresh') || requestUrl.includes('/auth/register');
    if (error.response?.status === 401 && !original._retry && !isAuthEndpoint) {
      original._retry = true;
      try {
        const refresh = tokenStorage.getRefresh();
        const { data } = await axios.post(`${BASE_URL}/api/auth/refresh`, { refresh_token: refresh });
        tokenStorage.setAccess(data.access_token);
        original.headers.Authorization = `Bearer ${data.access_token}`;
        return client(original);
      } catch {
        tokenStorage.clear();
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);
