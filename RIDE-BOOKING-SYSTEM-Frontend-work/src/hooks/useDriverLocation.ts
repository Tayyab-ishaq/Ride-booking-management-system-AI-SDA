import { useEffect, useRef } from 'react';
import { driverApi } from '../api/driverApi';
import { useGeolocation } from './useGeolocation';

// Keeps the latest browser location in memory while the driver is online.
// The actual save to the backend happens once from the online toggle handler.
export function useDriverLocation(isOnline: boolean) {
  const { coords, error } = useGeolocation(true); // watch mode
  const coordsRef = useRef(coords);
  coordsRef.current = coords;

  useEffect(() => {
    if (!isOnline) return;

    // No backend writes here; just keep the latest coords available to the UI.
    const c = coordsRef.current;
    if (c) {
      coordsRef.current = c;
    }
  }, [isOnline]);

  return { coords, error };
}
