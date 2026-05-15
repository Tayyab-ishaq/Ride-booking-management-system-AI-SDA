import { useState, useEffect } from 'react';

interface Coords { lat: number; lng: number }

// Browser GPS wrapper used by driver location ping and map pins
export function useGeolocation(watch = false) {
  const [coords, setCoords] = useState<Coords | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!navigator.geolocation) {
      setError('Geolocation not supported');
      return;
    }
    const opts: PositionOptions = {
      enableHighAccuracy: false,
      timeout: 30000,
      maximumAge: 60000,
    };
    const success = (pos: GeolocationPosition) =>
      setCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude });
    const fail = (err: GeolocationPositionError) => setError(err.message);

    if (watch) {
      const id = navigator.geolocation.watchPosition(success, fail, opts);
      return () => navigator.geolocation.clearWatch(id);
    } else {
      navigator.geolocation.getCurrentPosition(success, fail, opts);
    }
  }, [watch]);

  return { coords, error };
}
