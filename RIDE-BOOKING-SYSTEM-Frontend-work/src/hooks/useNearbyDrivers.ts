import { useState, useEffect } from 'react';
import { driverApi } from '../api/driverApi';

// Fetches nearby drivers and refreshes every 10s for map pins
export function useNearbyDrivers(lat: number | null, lng: number | null) {
  const [drivers, setDrivers] = useState<unknown[]>([]);

  useEffect(() => {
    if (!lat || !lng) return;
    const fetch = async () => {
      try {
        const { data } = await driverApi.nearby(lat, lng);
        setDrivers(data.drivers ?? []);
      } catch {}
    };
    fetch();
    const interval = setInterval(fetch, 10000);
    return () => clearInterval(interval);
  }, [lat, lng]);

  return drivers;
}
