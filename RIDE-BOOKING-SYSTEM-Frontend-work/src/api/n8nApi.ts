import { client } from './client';

const API_PREFIX = '/api';

export const n8nApi = {
  // POST /webhooks/ride-requested — Workflow A: returns AI-ranked drivers
  rideRequested: (data: { ride_id: string; drivers: object[]; pickup: object }) =>
    client.post(`${API_PREFIX}/webhooks/ride-requested`, data),

  // POST /webhooks/fare-estimate — Workflow B: returns surge multiplier + fare
  fareEstimate: (data: { route: object; demand_signals: object }) =>
    client.post(`${API_PREFIX}/webhooks/fare-estimate`, data),

  // POST /webhooks/ride-completed — Workflow C: invoice + summary + analytics
  rideCompleted: (data: { ride_id: string }) =>
    client.post(`${API_PREFIX}/webhooks/ride-completed`, data),

  // POST /webhooks/payment-failed
  paymentFailed: (data: { payment_id: string; reason: string }) =>
    client.post(`${API_PREFIX}/webhooks/payment-failed`, data),

  // POST /webhooks/driver-signup
  driverSignup: (data: { driver_id: string }) =>
    client.post(`${API_PREFIX}/webhooks/driver-signup`, data),

  // GET /integrations/status — health check for all active workflows
  status: () =>
    client.get(`${API_PREFIX}/integrations/status`),
};
