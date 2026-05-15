import { useState, useCallback } from 'react';
import { rideApi } from '../api/rideApi';

export function useRide() {
  const [ride, setRide] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const requestRide = useCallback(async (payload: { origin: string; destination: string; ride_type?: string; pickup_latitude?: number; pickup_longitude?: number; estimated_fare?: number }) => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await rideApi.create(payload);
      setRide(data);
      return data;
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? 'Failed to request ride');
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  const cancelRide = useCallback(async (id: string) => {
    await rideApi.cancel(id);
    setRide(null);
  }, []);

  const updateStatus = useCallback(async (id: string, status: string) => {
    const method =
      status === 'accepted'
        ? rideApi.accept
        : status === 'in_progress'
          ? rideApi.start
          : status === 'completed'
            ? rideApi.complete
            : null;

    if (!method) {
      throw new Error(`Unsupported ride status: ${status}`);
    }

    const { data } = await method(id);
    setRide(data);
    return data;
  }, []);

  return { ride, loading, error, requestRide, cancelRide, updateStatus };
}
