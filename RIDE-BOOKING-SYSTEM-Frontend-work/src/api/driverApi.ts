import { client } from './client';

const DRIVER_PREFIX = '/api/driver';

export const driverApi = {
  // POST /drivers/register
  register: (data: { vehicle: object; license_number: string; documents: object }) =>
    client.post(`${DRIVER_PREFIX}/register`, data),

  // GET /drivers/{id}
  getById: (id: string) =>
    client.get(`${DRIVER_PREFIX}/${id}`),

  // PUT /drivers/{id}/status
  setStatus: (id: string, status: 'online' | 'offline' | 'busy') =>
    client.put(`${DRIVER_PREFIX}/${id}/status`, { status }),

  // PATCH /api/driver/status — set driver availability (online/offline)
  setAvailability: (is_available: boolean) =>
    client.patch(`${DRIVER_PREFIX}/status`, { is_available }),

  // DELETE /api/driver/locations — clear stored driver locations
  deleteLocations: () => client.delete(`${DRIVER_PREFIX}/locations`),

  // POST /api/driver/save-location — stores current driver coordinates
  updateLocation: (lat: number, lng: number) =>
    client.post(`${DRIVER_PREFIX}/save-location`, { latitude: lat, longitude: lng }),

  // GET /drivers/nearby — input for Workflow A ranking payload
  nearby: (lat: number, lng: number, radius_km = 5) =>
    client.get(`${DRIVER_PREFIX}/nearby`, { params: { lat, lng, radius_km } }),

  // GET /drivers/{id}/earnings
  earnings: (id: string, params?: { from?: string; to?: string }) =>
    client.get(`${DRIVER_PREFIX}/${id}/earnings`, { params }),

  // GET /api/driver/active-request
  activeRequest: () => client.get(`${DRIVER_PREFIX}/active-request`),
};
