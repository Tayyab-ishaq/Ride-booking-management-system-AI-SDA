import { useState, useEffect } from 'react';
import { driverApi } from '../api/driverApi';

export function useEarnings(driverId: string | null, from?: string, to?: string) {
  const [earnings, setEarnings] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!driverId) return;
    setLoading(true);
    driverApi.earnings(driverId, { from, to })
      .then(({ data }) => setEarnings(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [driverId, from, to]);

  return { earnings, loading };
}
