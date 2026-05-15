import { WsClient } from './wsClient';
import { WS_EVENTS } from '../../constants/wsEvents';

// /ws/rider/{user_id} — receives: driver_matched, location_update, fare_updated, etc.
export const createRiderSocket = (userId: string) => {
  const ws = new WsClient(`/ws/rider/${userId}`);

  return {
    connect: () => ws.connect(),
    disconnect: () => ws.disconnect(),
    onDriverMatched: (fn: (data: unknown) => void) => ws.on(WS_EVENTS.DRIVER_MATCHED, fn),
    onLocationUpdate: (fn: (data: unknown) => void) => ws.on(WS_EVENTS.LOCATION_UPDATE, fn),
    onRideAccepted: (fn: (data: unknown) => void) => ws.on(WS_EVENTS.RIDE_ACCEPTED, fn),
    onRideCancelled: (fn: (data: unknown) => void) => ws.on(WS_EVENTS.RIDE_CANCELLED, fn),
    onDriverArrived: (fn: (data: unknown) => void) => ws.on(WS_EVENTS.DRIVER_ARRIVED, fn),
    onRideCompleted: (fn: (data: unknown) => void) => ws.on(WS_EVENTS.RIDE_COMPLETED, fn),
    onPaymentDone: (fn: (data: unknown) => void) => ws.on(WS_EVENTS.PAYMENT_DONE, fn),
    onFareUpdated: (fn: (data: unknown) => void) => ws.on(WS_EVENTS.FARE_UPDATED, fn),
  };
};
