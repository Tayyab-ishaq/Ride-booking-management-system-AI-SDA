// Haversine distance between two lat/lng points — returns meters
export const haversineDistance = (lat1: number, lng1: number, lat2: number, lng2: number): number => {
  const R = 6371000;
  const toRad = (deg: number) => (deg * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1);
  const dLng = toRad(lng2 - lng1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
};

export const formatCoords = (lat: number, lng: number, decimals = 5) =>
  `${Number(lat).toFixed(decimals)}, ${Number(lng).toFixed(decimals)}`;

export const isValidCoords = (lat: number, lng: number) =>
  typeof lat === 'number' && typeof lng === 'number' &&
  lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180;
