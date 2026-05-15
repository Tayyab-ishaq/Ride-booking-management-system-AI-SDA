import { client } from './client';

const PAYMENTS_PREFIX = '/api/payments';

export const paymentApi = {
  // POST /payments/initiate — uses surge fare from Workflow B
  initiate: (data: { ride_id: string; payment_method: string; amount: number }) =>
    client.post(`${PAYMENTS_PREFIX}/initiate`, data),

  // POST /payments/confirm — triggers Workflow C receipt dispatch
  confirm: (payment_id: string) =>
    client.post(`${PAYMENTS_PREFIX}/confirm`, { payment_id }),

  // POST /payments/refund
  refund: (payment_id: string, amount?: number) =>
    client.post(`${PAYMENTS_PREFIX}/refund`, { payment_id, amount }),

  // GET /payments/history
  history: (params?: { page?: number; limit?: number }) =>
    client.get(`${PAYMENTS_PREFIX}/history`, { params }),

  // GET /payments/methods
  listMethods: () =>
    client.get(`${PAYMENTS_PREFIX}/methods`),

  // POST /payments/methods
  addMethod: (data: { token: string; type: 'card' | 'wallet' }) =>
    client.post(`${PAYMENTS_PREFIX}/methods`, data),

  // DELETE /payments/methods/{id}
  removeMethod: (id: string) =>
    client.delete(`${PAYMENTS_PREFIX}/methods/${id}`),
};
