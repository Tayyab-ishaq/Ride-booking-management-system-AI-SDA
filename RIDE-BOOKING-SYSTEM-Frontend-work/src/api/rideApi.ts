import { client } from './client';
import { matchingApi } from './matchingApi';
const API_PREFIX = '/api';
const RIDE_PREFIX = `${API_PREFIX}/rides`;
export const rideApi = {
  // POST /api/rides/create
  create: (data: { origin: string; destination: string; ride_type?: string; pickup_latitude?: number; pickup_longitude?: number; estimated_fare?: number }) =>
    client.post(`${RIDE_PREFIX}/create`, data),

  // Backward-compatible alias for existing callers
  request: (data: { origin: string; destination: string; ride_type?: string; pickup_latitude?: number; pickup_longitude?: number; estimated_fare?: number }) =>
    client.post(`${RIDE_PREFIX}/create`, data),

  // Trigger driver assignment immediately after a ride is created.
  findMatch: (rideId: string) => matchingApi.find(rideId),

  // GET /rides/{id}
  getById: (id: string) =>
    client.get(`${RIDE_PREFIX}/${id}`),

  // POST /rides/{id}/cancel
  cancel: (id: string) =>
    client.post(`${RIDE_PREFIX}/${id}/cancel`),

  // PATCH /rides/{id}/accept|start|complete
  updateStatus: (id: string, status: string) =>
    status === 'accepted'
      ? client.patch(`${RIDE_PREFIX}/${id}/accept`)
      : status === 'in_progress'
        ? client.patch(`${RIDE_PREFIX}/${id}/start`)
        : status === 'completed'
          ? client.patch(`${RIDE_PREFIX}/${id}/complete`)
          : Promise.reject(new Error(`Unsupported ride status: ${status}`)),

  accept: (id: string) =>
    client.patch(`${RIDE_PREFIX}/${id}/accept`),

  start: (id: string) =>
    client.patch(`${RIDE_PREFIX}/${id}/start`),

  complete: (id: string) =>
    client.patch(`${RIDE_PREFIX}/${id}/complete`),

  // POST /rides/{id}/rating
  rate: (id: string, data: { rating: number; comment?: string }) =>
    client.post(`${RIDE_PREFIX}/${id}/rating`, { rating: data.rating }),

  // GET /rides/history?page=1&page_size=20
  history: (params?: { page?: number; page_size?: number }) =>
    client.get(`${RIDE_PREFIX}/history`, { params }),
};
