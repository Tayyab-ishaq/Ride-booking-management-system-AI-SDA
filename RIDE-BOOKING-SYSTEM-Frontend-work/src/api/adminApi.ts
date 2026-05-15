import { client } from './client';

const ADMIN_PREFIX = '/api/admin';

export const adminApi = {
  dashboard: () => client.get(`${ADMIN_PREFIX}/dashboard`),
  rides: (limit = 50) => client.get(`${ADMIN_PREFIX}/rides`, { params: { limit } }),
  users: (limit = 50) => client.get(`${ADMIN_PREFIX}/users`, { params: { limit } }),
};
