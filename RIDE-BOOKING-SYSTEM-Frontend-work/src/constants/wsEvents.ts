// All WebSocket event name strings — single source of truth (no magic strings)
export const WS_EVENTS = {
  DRIVER_MATCHED: 'driver_matched',
  LOCATION_UPDATE: 'location_update',
  RIDE_ACCEPTED: 'ride_accepted',
  RIDE_CANCELLED: 'ride_cancelled',
  DRIVER_ARRIVED: 'driver_arrived',
  RIDE_COMPLETED: 'ride_completed',
  PAYMENT_DONE: 'payment_done',
  FARE_UPDATED: 'fare_updated',
  RIDE_OFFER: 'ride_offer',
  STATUS_UPDATE: 'status_update',
} as const;

export type WsEvent = typeof WS_EVENTS[keyof typeof WS_EVENTS];
