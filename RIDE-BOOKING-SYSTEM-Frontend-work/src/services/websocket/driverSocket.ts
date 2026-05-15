import { WsClient } from './wsClient';
import { WS_EVENTS } from '../../constants/wsEvents';

// /ws/driver/{driver_id} — receives: ride_offer (AI-ranked), status_updates
export const createDriverSocket = (driverId: string) => {
  const ws = new WsClient(`/ws/driver/${driverId}`);

  return {
    connect: () => ws.connect(),
    disconnect: () => ws.disconnect(),
    onRideOffer: (fn: (data: unknown) => void) => ws.on(WS_EVENTS.RIDE_OFFER, fn),
    onRideCancelled: (fn: (data: unknown) => void) => ws.on(WS_EVENTS.RIDE_CANCELLED, fn),
    onStatusUpdate: (fn: (data: unknown) => void) => ws.on(WS_EVENTS.STATUS_UPDATE, fn),
    onRideCompleted: (fn: (data: unknown) => void) => ws.on(WS_EVENTS.RIDE_COMPLETED, fn),
  };
};
