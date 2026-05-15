import { useState, useEffect, useCallback } from 'react';
import { matchingApi } from '../api/matchingApi';

// Polls /matching/status/{ride_id} and exposes accept/reject
export function useMatching(rideId: string | null) {
  const [status, setStatus] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!rideId) return;
    const interval = setInterval(async () => {
      try {
        const { data } = await matchingApi.status(rideId);
        setStatus(data);
      } catch {}
    }, 3000);
    return () => clearInterval(interval);
  }, [rideId]);

  const accept = useCallback(async (driverId: string) => {
    if (!rideId) return;
    setLoading(true);
    try {
      await matchingApi.accept(rideId, driverId);
    } finally {
      setLoading(false);
    }
  }, [rideId]);

  const reject = useCallback(async (driverId: string) => {
    if (!rideId) return;
    // Re-runs Workflow A with updated driver pool
    await matchingApi.reject(rideId, driverId);
  }, [rideId]);

  return { status, loading, accept, reject };
}
