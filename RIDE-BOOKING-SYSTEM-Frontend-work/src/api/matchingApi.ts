import { client } from './client';

const API_PREFIX = '/api';
const MATCHING_PREFIX = `${API_PREFIX}/matching`;

export const matchingApi = {
  // POST /api/matching/find — triggers driver matching for a ride
  find: (ride_id: string) =>
    client.post(`${MATCHING_PREFIX}/find`, { ride_id }),

  // POST /api/matching/accept
  accept: (ride_id: string) =>
    client.post(`${MATCHING_PREFIX}/accept`, { ride_id }),

  // POST /api/matching/reject — retries matching with the next driver
  reject: (ride_id: string) =>
    client.post(`${MATCHING_PREFIX}/reject`, { ride_id }),

  // GET /api/matching/status/{ride_id} — polling fallback
  status: (ride_id: string) =>
    client.get(`${MATCHING_PREFIX}/status/${ride_id}`),
};
