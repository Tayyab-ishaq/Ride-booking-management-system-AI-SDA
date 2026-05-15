import { client } from './client';
import { tokenStorage } from '../utils/tokenStorage';

const AUTH_ROUTE_PREFIX = '/api/auth';

export const authApi = {
  // POST ${AUTH_ROUTE_PREFIX}/register
  register: (data: {
    email: string;
    password: string;
    confirm_password: string;
    first_name?: string;
    last_name?: string;
    full_name?: string;
    role?: string;
  }) =>
    client.post(`${AUTH_ROUTE_PREFIX}/register`, data),

  // POST /api/driver/register
  registerDriver: (data: {
    email: string;
    password: string;
    confirm_password: string;
    first_name?: string;
    last_name?: string;
    full_name?: string;
    license_number: string;
    vehicle_number: string;
    vehicle_type: string;
    vehicle_make_model?: string;
    vehicle_color?: string;
  }) =>
    client.post('/api/driver/register', data),

  // POST ${AUTH_ROUTE_PREFIX}/login
  login: (data: { email?: string; phone?: string; password: string }) =>
    client.post(`${AUTH_ROUTE_PREFIX}/login`, data),
 
  // POST ${AUTH_ROUTE_PREFIX}/refresh
  refreshToken: (refresh_token: string) =>
    client.post(`${AUTH_ROUTE_PREFIX}/refresh`, { refresh_token }),

  // GET ${AUTH_ROUTE_PREFIX}/me
  me: () =>
    client.get(`${AUTH_ROUTE_PREFIX}/me`),

  // POST ${AUTH_ROUTE_PREFIX}/logout
  logout: () =>
    client.post(`${AUTH_ROUTE_PREFIX}/logout`, { refresh_token: tokenStorage.getRefresh() ?? '' }),
};
